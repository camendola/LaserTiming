import pandas as pd
import os

#directory = '/afs/cern.ch/user/f/ferriff/public/ForChiaraA/EcalTimeCalibConstants_UL_Run1_Run2_v1/'

directory= "/afs/cern.ch/work/c/camendol/LaserIOVs/"
i = 0
for filename in os.listdir(directory):

    if len(filename.split("_"))<3 :
        print (filename)
        os.remove(directory+filename)
    else:
        continue
