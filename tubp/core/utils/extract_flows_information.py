import binascii
import glob
import logging
import os
import subprocess

import dpkt
import socket

import numpy
import torch
from PIL import Image
from django.conf import settings
from torchvision import transforms

from tubp.core.models.mongo_models import FlowsInformations
from tubp.core.utils.prediction_model import PredictionModel

PNG_SIZE = 28

logger = logging.getLogger(__name__)


class ExtractFlowsInformation(object):

    def __init__(self, input_dir, pattern):
        self.input_dir = input_dir
        self.model = PredictionModel()
        self.pattern = pattern
        self.model.load_state_dict(torch.load(settings.PREDICTION_MODEL_PATH, map_location=torch.device('cpu')))

    @staticmethod
    def _get_matrix_from_pcap(filename, width):
        with open(filename, 'rb') as f:
            content = f.read()

        hexst = binascii.hexlify(content)

        fh = numpy.array([int(hexst[i:i + 2], 16) for i in range(0, len(hexst), 2)])
        if len(fh) < width * width:
            logger.info("bad size")
            raise ValueError('bad size')
        samp = fh[0:width * width]
        fh = samp.reshape(width, width)

        fh = numpy.uint8(fh)

        return fh

    def extract_features(self):
        while glob.glob(self.input_dir + '/*.*', recursive=True):
            for item in glob.glob(self.input_dir + '/*.*', recursive=True):
                try:
                    data = self._extract_time_and_ip(item)
                    if data["destination_ip"] not in settings.POTENTIAL_IPS:
                        os.remove(item)
                        continue
                except Exception as e:
                    os.remove(item)
                    continue

                try:
                    traffic_type = self._extract_dpi_type(item, self.pattern)
                    bw_info = self._extract_bandwidth(item, data)
                except Exception as e:
                    os.remove(item)
                    continue

                os.remove(item)
                data["traffic_type"] = traffic_type
                data.update(**bw_info)
                logger.info("save in mongo")
                FlowsInformations(**data).save()

    @staticmethod
    def _extract_dpi_type(item, pattern):
        proc = subprocess.Popen("../DPI/example/ndpiReader -i %s -q -w output_%s.txt" % (item, pattern), shell=True)
        while proc.poll() is None:
            pass
        with open("output_%s.txt" % pattern) as f:
            traffic_type = f.read().split("\n")[0]

        return traffic_type

    def _get_image_addr(self, item):
        logger.info("convert pcap to array")
        im = Image.fromarray(self._get_matrix_from_pcap(item, PNG_SIZE))
        return im

    @staticmethod
    def _extract_time_and_ip(file_dir):
        details = subprocess.check_output(
            'tshark -r %s -t ad' % file_dir, shell=True).decode("utf-8").split(' ')
        return {"date": details[5], "hour": details[6], "source_ip": details[7], "destination_ip": details[8]}

    def _predict_traffic_type_class(self, png_addr):
        pred = self.model.forward(self.__get_image(png_addr))
        return list(pred.view(18, -1).argmax().numpy().reshape(-1, ))[0]

    @staticmethod
    def __get_image(image):
        return transforms.ToTensor()(image)

    @staticmethod
    def _extract_bandwidth(filename, data):

        f = open(filename, 'rb')
        pcap = dpkt.pcap.Reader(f)
        times = []
        total_bytes = 0
        src = None
        dst = None
        try:
            for timestamp, buf in pcap:
                packet = dpkt.ethernet.Ethernet(buf).data
                if not src and not dst:
                    src = socket.inet_ntop(socket.AF_INET, packet.src)
                    dst = socket.inet_ntop(socket.AF_INET, packet.dst)
                    logger.info(src)
                    logger.info("I hate my projecttttttttttttttt")
                total_bytes += packet.len
                times.append(timestamp)

            e_timestamp = max(times)
            f_timestamp = min(times)

            bw = total_bytes/(e_timestamp-f_timestamp)/1000

        except Exception as e:
            f_timestamp = None
            e_timestamp = None
            bw = None
            src = None
            dst = None

        return {
                "first_timestamp": f_timestamp,
                "last_timestamp": e_timestamp,
                "bandwidth": bw,
                "source_ip": src if src else data['source_ip'],
                "destination_ip_2": dst
        }
