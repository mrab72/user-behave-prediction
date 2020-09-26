import logging
import os
import subprocess
import time
import random
import string
import glob
from celery.schedules import crontab
from celery.task import PeriodicTask, Task
from django.conf import settings
from datetime import datetime
from tubp.core.utils.extract_flows_information import ExtractFlowsInformation
from tubp.core.utils.utils import kill_process

logger = logging.getLogger(__name__)


class CaptureTrafficTask(PeriodicTask):
    run_every = crontab(minute="*/5")
    soft_time_limit = 24 * 60 * 60
    routing_key = settings.TUBP_DATA_CAPTURE_ROUTING_KEY

    def run(self, period="5"):
        """

        :param period: the duration of capturing network line
        :return: write pcap data in a file in temp_directory and then run PPOEEE decoder
        """

        temp_file_name = ''.join(random.choice(string.ascii_lowercase) for i in range(10))
        file = os.path.join(settings.TEMP_MEMORY_DIR, 'temporary_pcap_file_%s.pcap' % temp_file_name)
        start = datetime.utcnow()
        logger.info("start capturing traffic")
        if start.minute % int(period) == 0:
            proc = subprocess.Popen(
                "sudo tcpdump -i ens1f0 -w %s" % file, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE
            )

            logger.info("finish capturing traffic")
            while (datetime.utcnow() - start).total_seconds() < int(period) * 60:
                pass

            kill_process(proc.pid)

            PPOEDecoderTask().run(input_file=file, process_num=temp_file_name)


class PPOEDecoderTask(Task):
    soft_time_limit = 24 * 60 * 60
    routing_key = settings.TUBP_DECODER_ROUTING_KEY

    def run(self, input_file=None, process_num="1"):
        """

        :param input_file: a pcap file
        :param process_num: a random pattern to have a specific pattern for the pcap file until its data store in mongod
        :return: write a pcap file without ppoeee header and run remover arp dns task
        """
        output_file = os.path.join(settings.TEMP_MEMORY_DIR, 'temporary_decode_pcap_%s.pcap' % process_num)
        proc = subprocess.Popen(
            "sudo ./stripe/stripe -r %s  -w %s" % (input_file, output_file),
            shell=True
        )

        logger.info("start decoding ppoeee")
        while proc.poll() is None:
            pass
        os.remove(input_file)
        RemoveARPDNSPacketsTask().run(output_file, process_num)


class RemoveARPDNSPacketsTask(Task):
    soft_time_limit = 24 * 60 * 60
    routing_key = settings.TUBP_REMOVER_ROUTING_KEY

    def run(self, input_file=None, process_num="1"):
        """

        :param input_file: a pcap file without ppoeee headers
        :param process_num: a random pattern to have a specific pattern for the pcap file until its data store in mongod
        :return: write the traffic without arp and dns in pcap file and run extract flows task
        """
        output_file = os.path.join(settings.TEMP_MEMORY_DIR, 'temporary_remove_pcap_%s.pcap' % process_num)
        proc = subprocess.Popen(
            "sudo tcpdump -r %s not port 53 and not arp -w %s" % (input_file, output_file),
            shell=True
        )
        logger.info("start removing arp and dns packets")
        while proc.poll() is None:
            pass
        os.remove(input_file)
        ExtractFlowsTask().run(output_file, process_num)


class ExtractFlowsTask(Task):
    soft_time_limit = 24 * 60 * 60
    routing_key = settings.TUBP_FLOWS_PROCESS_ROUTING_KEY

    def run(self, input_file=None, process_num="1"):
        """

        :param input_file: a pcap file
        :param process_num:
        :return: extract flows from pcap file and run task of extracting features of flows
         the process of extracting features start after extracting 1000 flows(for better pipeline)
        """
        output_dir = settings.FLOWS_TEMP_DIR + "_%s" % process_num
        os.mkdir(output_dir)
        proc = subprocess.Popen(
            "sudo PcapSplitter -f %s -o %s -m connection" % (input_file, output_dir),
            shell=True
        )
        logger.info("start extracting flows")
        while len(glob.glob(os.path.join(output_dir, "*.pcap"))) < 1000:
            pass

        ExtractFlowsFeaturesTask().run(output_dir, process_num, input_file)


class ExtractFlowsFeaturesTask(Task):
    soft_time_limit = 24 * 60 * 60
    routing_key = settings.TUBP_FLOWS_PROCESS_ROUTING_KEY

    def run(self, file_dir=None, process_num="1", removed_pcap_file=None):
        """

        :param file_dir: a directory that include all flows
        :param process_num:
        :param removed_pcap_file: pass removed_pcap file from previous step to delete it at the end of extracting
        process
        :return: extract ip, time, traffic_type by running dpi and save record in mongodb
        """
        logger.info("start extracting features of flows")
        start = time.time()
        while time.time() - start < 30:
            pass
        try:
            ExtractFlowsInformation(input_dir=file_dir, pattern=process_num).extract_features()
        except Exception as e:
            logger.info(e)

        os.rmdir(file_dir)
        os.remove(removed_pcap_file)
