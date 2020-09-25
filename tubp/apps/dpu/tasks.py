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

    def run(self, period="5"):
        temp_file_name = ''.join(random.choice(string.ascii_lowercase) for i in range(10))
        file = '/mnt/temporary_pcap_file_%s.pcap' % temp_file_name
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

    def run(self, input_file=None, process_num="1"):
        output_file = '/mnt/temporary_decode_pcap_%s.pcap' % process_num
        proc = subprocess.Popen(
            "sudo ./stripe/stripe -r %s  -w %s" % (input_file, output_file),
            shell=True
        )
        logger.info("start decoding ppoee")
        while proc.poll() is None:
            pass
        os.remove(input_file)
        RemoveARPDNSPacketsTask().run(output_file, process_num)


class RemoveARPDNSPacketsTask(Task):
    soft_time_limit = 24 * 60 * 60

    def run(self, input_file=None, process_num="1"):
        output_file = '/mnt/temporary_remove_pcap_%s.pcap' % process_num
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

    def run(self, input_file=None, process_num="1"):
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

    def run(self, file_dir=None, process_num="1", removed_pcap_file=None):
        logger.info("start extracting features of flows")
        start = time.time()
        while time.time() - start < 30:
            pass
        ExtractFlowsInformation(input_dir=file_dir, pattern=process_num).extract_features()
        os.rmdir(file_dir)
        os.remove(removed_pcap_file)


class DeleteFlowsFiles(Task):

    soft_time_limit = 24 * 60 * 60

    def run(self, proc, file):
        while proc.poll() is None:
            pass

        os.remove(file)
