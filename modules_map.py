import pandas as pd
import os.path
import numpy as np
from pathlib import Path

import sys
sys.path.append('../')
from elmonk.dst import DstReader ### to read the DST files into pandas
import matplotlib.pyplot as plt

from elmonk.common import HdfLaser
from elmonk.common.helper import scalar_to_list, make_index
import seaborn as sns

import ecalic

import argparse
import modules.load as load


parser = argparse.ArgumentParser(description='Command line parser of plotting options')

parser.add_argument('--fed', dest='fed',type=int, help='fed', default=612)

args = parser.parse_args()

FED = args.fed

year = 2018
basedir = Path(f'/eos/cms/store/group/dpg_ecal/alca_ecalcalib/laser/dst.hdf')

workdir = "/afs/cern.ch/work/c/camendol/LaserData/"+str(year)+"/tables/"
filename = workdir + "FED_"+str(FED)+".hdf"

print(filename)                                                                                                                        
#if True:
if (not os.path.isfile(filename)): 
    data = HdfLaser(basedir / f'{year}/dstUL_db.{year}.hdf5')
    period = [f'{year}-06-01',f'{year}-09-01']
    #period = [f'{year}-06-01',f'{year}-06-02']    
    #mask 
    #status = ecalic.xml('../elmonk/etc/data/ecalChannelStatus_run324773.xml',type='status').icCMS()
    #good_channels = status.iov.mask(status['ic']!=0).dropna(how='all')

    xtals = data.xtal_idx('FED == '+str(FED))
        
    histories = data.xtal_history(iov_idx=data.iov_idx(period),xtal_idx=xtals, xtal_property='tAPD')

    run_seq = data.iov_idx_to_run_seq(data.iov_idx(period)['iov_idx'].values)
    histories[["run","seq"]] = np.array(run_seq)
    histories = histories.reset_index().set_index(["date", "run", "seq"])
    histories.to_hdf(filename, key= "hist", mode = "w")

else: 
    histories = pd.read_hdf(filename,key = "hist", mode = "r")

matacq = pd.read_hdf((basedir / f'{year}/dstUL_db.{year}.hdf5'), 'Matacq')
matacq = matacq[(matacq["FED"] == FED)]
matacq = matacq[(matacq["side"] == 0)]

histories["tstart"]  = histories.reset_index().set_index(["run","seq"]).index.map(matacq.set_index(["run", "seq"]).tstart)


histories = histories.reset_index().set_index(["date", "tstart"])
histories = histories.drop(columns = ["run","seq"])

histories = histories * 25 #conv to ns
histories = histories.reset_index().set_index("date").drop(columns=["tstart"]).sub(histories.reset_index().set_index("date").tstart, axis = 0) + 1390
print(histories)
histories = histories.T.reset_index()

histories['ieta']    = histories.set_index('xtal_ecalic_id').index.map(ecalic.geom.ix) 
histories['iphi']    = histories.set_index('xtal_ecalic_id').index.map(ecalic.geom.iy) 
#histories['side']    = np.where(np.where(histories['ieta'].values > 0,
#                                np.where(((histories['ieta'].values > 4) & (histories['iphi'].mod(10).values > 9)), 1, 0),
#                                np.where(((histories['ieta'].values < - 4) & (histories['iphi'].mod(10).values < 10)), 0, 1)))
histories['TT']      = histories.set_index('xtal_ecalic_id').index.map(ecalic.geom.ccu) 
histories['strip']   = histories.set_index('xtal_ecalic_id').index.map(ecalic.geom.strip) 
histories['Xtal']    = histories.set_index('xtal_ecalic_id').index.map(ecalic.geom.Xtal) 
histories["xtal_id"] = (histories['TT'] - 1) * 25 + (histories['strip'] - 1) * 5 + histories['Xtal'] - 1

print(histories)
histories = histories.reset_index().set_index(["ieta", "iphi", "xtal_id"])
histories = histories.drop(columns=['TT', 'strip','Xtal', 'xtal_ecalic_id'])
histories = histories.where(histories.std(axis=1) > 1)
histories = histories.where(histories.std(axis=1) < 50)
histories["mean"] = histories.mean(axis=1)
histories["RMS"]  = histories.std(axis=1)
histories["min"]  = histories.min(axis=1)
histories["max"]  = histories.max(axis=1)

histories = histories.reset_index()
trimmed = histories[["xtal_id", "mean", "RMS", "min", "max", "ieta", "iphi"]]

for var in ["min","max", "RMS", "mean"]:
    plt.figure(figsize=(7,20))
    ax = sns.heatmap(trimmed.pivot_table(columns = "iphi", index = "ieta", values = var).sort_index(ascending = False))
    #plt.xticks(np.arange(trimmed.ieta.min(), trimmed.ieta.max()+1, 5))
    plt.savefig("/eos/home-c/camendol/www/LaserTiming/blue_FEDs/"+str(FED)+"_"+str(var)+".pdf")
    plt.savefig("/eos/home-c/camendol/www/LaserTiming/blue_FEDs/"+str(FED)+"_"+str(var)+".png")
    trimmed.pivot_table(columns = "iphi", index = "ieta", values = var).to_csv("/eos/home-c/camendol/www/LaserTiming/blue_FEDs/"+str(FED)+"_"+str(var)+".txt")







