import pandas as pd
import os

#directory = '/afs/cern.ch/user/f/ferriff/public/ForChiaraA/EcalTimeCalibConstants_UL_Run1_Run2_v1/'
directory = "../conddb/CMSSW_10_3_0/src/usercode/"
i = 0
for filename in os.listdir(directory):
    if filename.endswith(".dat"):
        print (filename)
        df  = pd.read_csv(directory+filename, header = None, sep = " ")
        print(df)
        iov = filename.split("_")[4]
        print (iov)
        df["prof"] = 0
        df["prof"] = df["prof"].astype("int")
        df["zero"] = 0.0

        df[[0, 1, "prof", 3, "zero"]].to_csv("/afs/cern.ch/work/c/camendol/CalibIOVs/IOV"+str(i)+"_"+str(iov)+".txt", header = False, index = False, sep = " ")

        i += 1
    else:
        continue
