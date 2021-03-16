import os, sys
import argparse
import time
import datetime

parser = argparse.ArgumentParser()

parser.add_argument("-f", "--file", default=2017, help="file with commands to run")
parser.add_argument("-p", "--pattern", help="pattern of commands to launch")
parser.add_argument(
    "--tag",
    dest="tag",
    help="name of working space (defaults to timestamp)",
    default=None,
)
parser.add_argument(
    "-q", "--queue", dest="queue", help="condor queue", default="microcentury"
)

args = parser.parse_args()

file = args.file

variables = [
    line.rstrip("\n")
    for line in open(file)
    if line.split("=")[0].isupper() and not line.startswith("#")
]
linestolaunch = [
    line.rstrip("\n") for line in open(file) if line.startswith(args.pattern)
]

for var in variables:
    print(var)
for line in linestolaunch:
    print(line)


os.system("rm condor_0.log")

tag = datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S")
if args.tag:
    tag = args.tag

tag = "condor_" + tag

if os.path.exists(tag):
    os.system("rm -f " + tag + "/*")
else:
    os.system("mkdir -p " + tag)

n = 0

for line in linestolaunch:
    job_file = open(tag + "/job_" + str(n) + ".sh", "w")
    job_file.write("#!/bin/bash\n")
    job_file.write("source /afs/cern.ch/user/c/camendol/LaserTiming/setup.sh\n")
    job_file.write("cd /afs/cern.ch/user/c/camendol/LaserTiming\n")
    for var in variables:
        job_file.write(var + "\n")
    command = line
    command += " >& " + tag + "/job_" + str(n) + ".log;\n"
    job_file.write(command)
    job_file.write("touch " + tag + "/done_" + str(n) + ";\n")
    job_file.close()
    os.system("chmod u+rwx " + tag + "/job_" + str(n) + ".sh")

    submit_file = open(tag + "/submit_" + str(n) + ".sh", "w")
    submit_file.write("Universe = vanilla\n")
    submit_file.write("Executable  = " + tag + "/job_" + str(n) + ".sh\n")
    submit_file.write("Log         = " + tag + "/submit_$(ProcId).log\n")
    submit_file.write("Output      = " + tag + "/submit_$(ProcId).out\n")
    submit_file.write("Error       = " + tag + "/submit_$(ProcId).error\n")
    submit_file.write("queue 1\n")
    submit_file.write('+JobFlavour = "' + args.queue + '"\n')
    submit_file.close()
    launchcommand = "condor_submit " + tag + "/submit_" + str(n) + ".sh"
    print(launchcommand)
    os.system(launchcommand)
    n = n + 1
