import subprocess
import sys

def run_command(command, stdin=None, input=None, stdout=subprocess.PIPE):
    proc = subprocess.run(command, shell=True, encoding='utf-8',
                          stdin=stdin, input=input, stdout=stdout,
                          stderr=open("/dev/null", "w"))
    return proc.stdout
