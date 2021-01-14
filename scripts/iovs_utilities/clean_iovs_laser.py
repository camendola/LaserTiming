import pandas as pd
import os



directory= "/afs/cern.ch/work/c/camendol/LaserIOVs/2018/B/"
i = 0
for filename in os.listdir(directory):

    if len(filename.split("_"))<3 :
        print (filename)
        os.remove(directory+filename)
    else:
        continue
