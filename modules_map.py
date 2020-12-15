import pandas as pd
import warnings
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)

import os.path
import numpy as np
from pathlib import Path

import sys
sys.path.append('../')
import shutil

from elmonk.dst import DstReader ### to read the DST files into pandas
import matplotlib.pyplot as plt
import matplotlib as mpl
mpl.rcParams['axes.linewidth'] = 2
mpl.rcParams['axes.formatter.useoffset'] = False

from elmonk.common.helper import scalar_to_list, make_index
import seaborn as sns

import argparse
from tqdm import tqdm

import modules.load_hdf as load_hdf

parser = argparse.ArgumentParser(description='Command line parser of plotting options')

parser.add_argument('--fed',    dest='fed',type=int, help='fed', default=612)
parser.add_argument('--single', dest='single', help='write single sequence and run', action='store_true')
parser.add_argument('--write',  dest='write',  help='write hdf', default=False,  action ='store_true')
parser.add_argument('--rmin',   dest='rmin',type=int,  help='run min', default=0)
parser.add_argument('--rmax',   dest='rmax',type=int,  help='run max', default=0)
parser.add_argument('--apd',    dest='apd',    help='apd_pn maps', default=False,  action ='store_true')
parser.add_argument('--green',    dest='green',    help='green laser', default=False,  action ='store_true')
parser.add_argument('--long',    dest='long',    help='only take longest run', default=False,  action ='store_true')

args = parser.parse_args()

FED = args.fed

year = 2018
basedir = Path(f'/eos/cms/store/group/dpg_ecal/alca_ecalcalib/laser/dst.hdf')

workdir = "/afs/cern.ch/work/c/camendol/LaserData/"+str(year)+"/tables/"
if args.apd and not args.green:
    workdir = "/afs/cern.ch/work/c/camendol/LaserData/"+str(year)+"/tables_APD_PN/"
elif args.green and not args.apd:
    workdir = "/afs/cern.ch/work/c/camendol/LaserData/"+str(year)+"/tables_green/"
elif args.green and args.apd:
    workdir = "/afs/cern.ch/work/c/camendol/LaserData/"+str(year)+"/tables_green_APD_PN/"

filename = workdir + "FED_"+str(FED)+".hdf"

if not os.path.exists(workdir):
    os.makedirs(workdir)

print(filename)                                                          

prop = "tAPD"
if args.green: prop = "tStart"
if args.apd: prop = "APD_PN"
print (prop)
histories = load_hdf.load_history(filename, year, args.write, basedir, FED, prop, args.green)
histories = histories.reset_index().set_index(["date","seq","run"]).T.reset_index()
histories = load_hdf.append_idxs(histories).T

#correct blue laser timing by matacq tstart
if not args.green and not args.apd: histories = load_hdf.subtract_tmatacq(histories, year, basedir, FED)

if args.rmin > 0 :
    histories = histories.reset_index()
    histories = histories[(histories["run"] > args.rmin)]
    histories = histories.reset_index().set_index(["date", "run","seq"]).drop(columns=["index"])

if args.rmax > 0 :
    histories = histories.reset_index()
    histories = histories[(histories["run"] < args.rmax)]
    histories = histories.reset_index().set_index(["date", "run","seq"]).drop(columns=["index"])

if args.long: 
    bylenght = histories.copy().reset_index()
    bylenght["size"]=bylenght.groupby("run").run.transform(np.size)
    #bylenght = bylenght.drop([bylenght.iloc[bylenght['size'].idxmax()]])
    longest_run = bylenght.iloc[bylenght['size'].idxmax()]["run"].values[0]
    histories = histories.reset_index()
    histories = histories[(histories["run"] == longest_run)]
    histories = histories.reset_index().set_index(["date", "run","seq"]).drop(columns=["index"])
else:
    histories = histories.reset_index().set_index(["date", "run","seq"])

first_run = histories.reset_index().run.tolist()[0]
last_run = histories.reset_index().run.tolist()[-1]
first = histories.copy().reset_index().set_index("date")
first = first[((first["run"] == first_run) & (first["seq"] == 0))]
first = first.reset_index().set_index(["date", "run","seq"])

#write indivitual .txt files for each run and sequence
subfolder = ""
if args.long: subfolder = str(longest_run)+"/"
if args.rmin > 0 or args.rmax > 0: subfolder = str(first_run)+"_"+str(last_run)+"/"

if args.single and not args.apd:
    list_groups = []
    with tqdm(total=histories.groupby("run").ngroups, unit='entries') as pbar:
        for run, rgroup in histories.groupby("run"):
            rgroup = rgroup.reset_index().set_index("date","run")
            #rgroup = rgroup.T.sub(first.T[first.T.columns[0]], axis = 0).T #for subtracting first tMax of the year
            #rgroup["run"] = run
            list_groups.append(rgroup)
            if not os.path.exists("/eos/home-c/camendol/www/LaserTiming/blue_FEDs_sub/"+subfolder+str(FED)):
                os.makedirs("/eos/home-c/camendol/www/LaserTiming/blue_FEDs_sub/"+subfolder+str(FED))
            if not os.path.exists("/afs/cern.ch/user/c/camendol/public/xFederico/blue_FEDs_sub/"+subfolder+str(FED)):
                os.makedirs("/afs/cern.ch/user/c/camendol/public/xFederico/blue_FEDs_sub/"+subfolder+str(FED))

            shutil.copy("/eos/home-c/camendol/www/index.php","/eos/home-c/camendol/www/LaserTiming/blue_FEDs_sub/"+subfolder)
            shutil.copy("/eos/home-c/camendol/www/index.php","/eos/home-c/camendol/www/LaserTiming/blue_FEDs_sub/"+subfolder+str(FED))
            for seq, sgroup in rgroup.groupby("seq"):
                sgroup = sgroup.reset_index().set_index("date").drop(columns=['seq','run']).T.reset_index()
                sgroup = sgroup.astype({"iphi": "int", "ieta":"int", sgroup.columns[-1] : "float"})
                sgroup.pivot_table(columns = "iphi", index = "ieta", values = sgroup.columns[-1]).to_csv("/eos/home-c/camendol/www/LaserTiming/blue_FEDs_sub/"+subfolder+str(FED)+"/"+str(FED)+"_"+str(run)+"_"+str(seq)+".txt")
                sgroup.pivot_table(columns = "iphi", index = "ieta", values = sgroup.columns[-1]).to_csv("/afs/cern.ch/user/c/camendol/public/xFederico/blue_FEDs_sub/"+subfolder+str(FED)+"/"+str(FED)+"_"+str(run)+"_"+str(seq)+".txt")
                list_groups.append(sgroup)

            pbar.update(1)

    del list_groups

if args.apd:
    histories = histories.T.div(first.T[first.T.columns[0]], axis = 0).T
else:
    histories = histories.T.sub(first.T[first.T.columns[0]], axis = 0).T

#fig, ax = plt.subplots()
#histories[(histories[histories.columns[1000]] > -200) & (histories[histories.columns[1000]] < 200)].hist(column = histories.to_numpy().flatten(), bins = 100, ax = ax)
#plt.hist(histories.to_numpy().flatten(), bins = 100, range = (-5, 5))
#ax.set_yscale('log')
#plt.show()
#input()

print(histories)

histories = histories.reset_index().set_index("date").drop(columns=['seq','run']).T
histories = histories[(histories > -5) & (histories < 5)]

histories["mean"] = histories.astype('float').mean(axis=1)
histories["RMS"]  = histories.astype('float').std(axis=1)
histories["min"]  = histories.astype('float').min(axis=1)
histories["max"]  = histories.astype('float').max(axis=1)

histories = histories.reset_index()

trimmed = histories[["xtal_id", "mean", "RMS", "min", "max", "ieta", "iphi"]]
    
print(trimmed)


directory="blue_FEDs"

if args.green:  directory="green_FEDs"
label= "[(t$_{xtal}$ - t$_{MATACQ}$)(t) - (t$_{xtal}$ - t$_{MATACQ}$)(0)] [ns]"
if args.apd:

    directory="blue_FEDs_APD_PN"
    if args.green:  directory="green_FEDs_APD_PN"
    label= "[(APD/PN)(t)/(APD/PN)(0)]"

for var in ["min","max", "RMS", "mean"]:
    plt.figure(figsize=(7,18))
    ax = sns.heatmap(trimmed.pivot_table(columns = "iphi", index = "ieta", values = var).sort_index(ascending = False), cbar_kws={'label': var+" "+label})
    
    ax.set(xlabel='i$\phi$', ylabel='i$\eta$')
    if not os.path.exists("/eos/home-c/camendol/www/LaserTiming/"+directory+"/"+subfolder+str(FED)):
        os.makedirs("/eos/home-c/camendol/www/LaserTiming/"+directory+"/"+subfolder+str(FED))
    shutil.copy("/eos/home-c/camendol/www/index.php","/eos/home-c/camendol/www/LaserTiming/"+directory+"/"+subfolder)
    shutil.copy("/eos/home-c/camendol/www/index.php","/eos/home-c/camendol/www/LaserTiming/"+directory+"/"+subfolder+str(FED))

    plt.savefig("/eos/home-c/camendol/www/LaserTiming/"+directory+"/"+subfolder+str(FED)+"_"+str(var)+".pdf",bbox_inches='tight')
    plt.savefig("/eos/home-c/camendol/www/LaserTiming/"+directory+"/"+subfolder+str(FED)+"_"+str(var)+".png",bbox_inches='tight')
    trimmed.pivot_table(columns = "iphi", index = "ieta", values = var).to_csv("/eos/home-c/camendol/www/LaserTiming/"+directory+"/"+subfolder+str(FED)+"_"+str(var)+".txt")









