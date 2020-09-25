
import os
import signal
import subprocess

import psutil


def kill_process(process_id):
    parent = psutil.Process(process_id)
    children = parent.children(recursive=True)
    for child_process in children:
        subprocess.check_output("sudo kill {}".format(child_process.pid), shell=True)
