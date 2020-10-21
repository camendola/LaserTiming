#!/usr/bin/env python

import os,sys
import optparse
import fileinput
import commands
import time
import glob
import subprocess
from os.path import basename
import ROOT



if __name__ == "__main__":

    usage = 'usage: %prog [options]'
    parser = optparse.OptionParser(usage)
    parser.add_option ('-f', '--fed', dest='fed', type = int, help='skim location folder', default=None)
    parser.add_option ('-T', '--tag'    , dest='tag'    , help='folder tag name'     , default='jobs')
    parser.add_option ('-s', '--sleep'  , dest='sleep'  , help='sleep in submission' , default=False)
    parser.add_option('--single', dest='single', help='write single sequence and run', action='store_true')
    parser.add_option('--write', dest='write', help='write hdf', default=False,  action ='store_true')

    (opt, args) = parser.parse_args()

    currFolder = os.getcwd ()

   
    # Submit the jobs
    # ---- ---- ---- ---- ---- ---- ---- ---- ---- ----


    tagname = "/" + opt.tag if opt.tag else ''
    jobsDir = currFolder + tagname 
    if os.path.exists (jobsDir) : os.system ('rm -f ' + jobsDir + '/*')
    else                        : os.system ('mkdir -p ' + jobsDir)
    executable = "modules_maps.py"
    scriptFile = open ('%s/submit_map_%d.sh'% (jobsDir,opt.fed), 'w')
    scriptFile.write ('#!/bin/bash\n')
    scriptFile.write ('echo $HOSTNAME\n')
    scriptFile.write ('source setup.sh\n')
    command  = executable + ' --single --fed ' + str(opt.fed) 
    if opt.single: command += " --single"
    if opt.single: command += " --write"
    command += (" " + ">& " + jobsDir + "/submit_map_"+str(opt.fed)+".log\n")
    scriptFile.write(command)
    scriptFile.write ('touch ' + jobsDir + '/done_%d\n' %opt.fed)
    scriptFile.write ('echo "All done for job %d" \n'%opt.fed)
    scriptFile.close ()
    os.system ('chmod u+rwx '+jobsDir+'/submit_map_'+str(opt.fed)+'.sh')
    
    condorFile = open ('%s/condor_wrapper_%d.sub'% (jobsDir,opt.fed), 'w')
    condorFile.write ('Universe = vanilla\n')
    condorFile.write ('Executable  = '+jobsDir + '/submit_map_' + str (opt.fed) + '.sh\n')
    condorFile.write ('Log         = %s/condor_job_$(ProcId).log\n'%jobsDir)
    condorFile.write ('Output      = %s/condor_job_$(ProcId).out\n'%jobsDir)
    condorFile.write ('Error       = %s/condor_job_$(ProcId).error\n'%jobsDir)
    condorFile.write ('queue 1\n')
    condorFile.close ()
    
    command = 'condor_submit '+ jobsDir + '/condor_wrapper_'+str(opt.fed)+'.sub'
    if opt.sleep : time.sleep (0.1)
    os.system (command)
    print(command)
