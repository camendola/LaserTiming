import pandas as pd
from root_pandas import read_root
import warnings
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)

import os.path
import numpy as np
from pathlib import Path

import sys
sys.path.append('../')
import shutil

from elmonk.dst import DstReader ### to read the DST files into pandas
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.patches as patches

import ecalic 

import glob

from pylab import *
from scipy.optimize import curve_fit
import statistics

mpl.rcParams['axes.linewidth'] = 2
mpl.rcParams['axes.formatter.useoffset'] = False

mpl.rcParams['xtick.direction'] = 'in'
mpl.rcParams['ytick.direction'] = 'in'
mpl.rcParams["ytick.right"] = True
mpl.rcParams["xtick.top"] = True

#from elmonk.common.helper import scalar_to_list, make_index

import argparse

import modules.load_hdf as load_hdf           # methods for histories from hdf files
import modules.load as load                   # methods for dst files 
import modules.write_csv as write_csv        



def linear_fit(x,b, m):
    y = b + m * x
    
    return y

parser = argparse.ArgumentParser(description='Command line parser of plotting options')

parser.add_argument('--fed',     dest='fed',       type=int, help='fed',      default=None)
parser.add_argument('--ch',      dest='ch',        type=int, help='ch',       default=-1)
parser.add_argument('--rmin',    dest='rmin',      type=int, help='rmin',     default=-1)
parser.add_argument('--rmax',    dest='rmax',      type=int, help='rmax',     default=-1)
parser.add_argument('--ietamin', dest='ietamin',   type=int, help='ietamin',  default=-999)
parser.add_argument('--ietamax', dest='ietamax',   type=int, help='ietamax',  default=-999)
parser.add_argument('--iphimin', dest='iphimin',   type=int, help='iphimin',  default=-999)
parser.add_argument('--iphimax', dest='iphimax',   type=int, help='iphimax',  default=-999)
parser.add_argument('--TT',      dest='TT',        type=int, help='TT',       default=-999)
parser.add_argument('--side',    dest='side',      type=int, help='side',     default=-1)
parser.add_argument('--era',    dest='era',        help='era',     default="A")

parser.add_argument('--dump',    dest='dump',      help='dump tables',                    default=False,  action ='store_true')
parser.add_argument('--show',    dest='show',      help='show plots',                     default=False,  action ='store_true')
parser.add_argument('--isgreen', dest='isgreen',   help='green laser',                    default=False,  action ='store_true')


args = parser.parse_args()


year = 2018
basedir = Path(f'/eos/cms/store/group/dpg_ecal/alca_ecalcalib/laser/dst.hdf')



workdir = "/afs/cern.ch/work/c/camendol/LaserData/"+str(year)+"/tables/"
if args.isgreen: workdir = "/afs/cern.ch/work/c/camendol/LaserData/"+str(year)+"/tables_green/"

FEDs = [fed for fed in range(610, 646)]
if args.fed == 610: FEDs = [fed for fed in range(610, 628)]
if args.fed == 628: FEDs = [fed for fed in range(628, 646)]
#if args.fed: FEDs = [args.fed]

all_histories = []
for FED in FEDs:
    filename = workdir + "FED_"+str(FED)+".hdf"
    
    tables = []
    stack = False
    if (args.ch < 0):  stack = True
    
    #get timing
    histories_time = pd.read_hdf(filename,key = "hist", mode = "r")
    histories_time = load_hdf.skim_history(histories_time, "time", year, args, basedir, FED, not args.isgreen)
    if stack:         histories_time    = load_hdf.stack_history(histories_time)
    histories_time = histories_time.reset_index().set_index(["date","seq"])
    if args.era == "A":        histories_time = histories_time[(histories_time["run"]>=315252) & (histories_time["run"]<=316995)]
    if args.era == "B":        histories_time = histories_time[(histories_time["run"]>=316998) & (histories_time["run"]<=319312)]
    if args.era == "C":        histories_time = histories_time[(histories_time["run"]>=319313) & (histories_time["run"]<=320393)]
    if args.era == "D":        histories_time = histories_time[(histories_time["run"]>=320394) & (histories_time["run"]<=325273)]
    histories_time = histories_time.reset_index().set_index(["date","run", "seq"])
    tables.append(histories_time)    
        
    
    #merge timing and apd/pn
    histories = pd.concat(tables,axis=1,keys=['time'] if args.ch > -1 else ['time']).swaplevel(0,1,axis=1).sort_index(axis=1)
    
    del tables
    
    ###get temperature
    fullpath = load_hdf.make_path(year, args.isgreen)
    sequence = pd.read_hdf((basedir / fullpath), 'sequence')
    histories["temperature"] = histories.reset_index().set_index(["run","seq"]).index.map(sequence.set_index(["run", "seq"]).temperature)
    histories = histories.reset_index().set_index(["date", "run","seq","temperature"])
    
    #get TCDS - not in hdf: map directly from dst files 
    dst_filelist = load.load_files(year, args.isgreen)
    runlist = histories.reset_index().run.drop_duplicates().sort_values().tolist()
    df_firstline = load.load_firstline(dst_filelist, year, fed = FED, runlist = runlist)
    
    if year == 2018:
        #clean bunch of runs with bugged temperature
        histories = histories.reset_index().set_index(["date","seq","temperature"])
        
        histories = histories[(histories["run"] < 314344) | (histories["run"] > 314350)]
        if args.era == "A":        histories = histories[(histories["run"]>=315252) & (histories["run"]<=316995)]
        if args.era == "B":        histories = histories[(histories["run"]>=316998) & (histories["run"]<=319312)]
        if args.era == "C":        histories = histories[(histories["run"]>=319313) & (histories["run"]<=320393)]
        if args.era == "D":        histories = histories[(histories["run"]>=320394) & (histories["run"]<=325273)]

        histories = histories.reset_index().set_index(["date","run", "seq","temperature"])
        
    
    histories["TCDS"] = histories.reset_index().set_index(["run","seq"]).index.map(df_firstline.reset_index().set_index(["run", "seq"]).TCDS)/1000000. # LHC freq [MHz]
    
    #histories = histories.reset_index().set_index("date").drop(columns=['seq','run'])
    histories = histories.reset_index().set_index("date")
    
    
    
    histories.columns = ['run','seq','temperature','xtal_id', 'time', 'TCDS'] if stack else ['run','seq', 'temperature','time','TCDS']
    
    histories = histories[(histories['time'] > -1.2) & (histories['time'] < 1.2)] 
    
    ranges = [40.0784, 40.0785, 40.0789, 40.07897, 40.0790, 40.07915, 40.0793] #TCDS ranges
    TCDSnames = ["TCDS"+str(i) for i in range (1,7)]
    fitfile = "fits_results/temperature/FEDX_ch_split_rootfit"
    if args.isgreen: filename = "fits_results/temperature/FEDX_ch_split_rootfit_green"
    fitfile  = fitfile + ".csv"
    if FED:
        df = pd.read_csv(fitfile.replace("X", str(FED)), index_col=[0,1],  header=[0, 1], skipinitialspace=True)
    df.columns = pd.MultiIndex.from_tuples(df.columns)
    
    df = df.reset_index().set_index(["ch", "FED", ("TCDS","TCDS1"),("TCDS","TCDS2"),("TCDS","TCDS3"),("TCDS","TCDS4"),("TCDS","TCDS5"), ("TCDS","TCDS6")])
    df = df[(df.T != 0).any()]
    df = df.reset_index().set_index("ch")
    df = df[(df["FED"] > 609)]
    #df = df.reset_index().set_index(["ch", "FED"])
    
    histories.dropna()

    i = 0
    grs = []
    if stack:
        histories = histories.reset_index().set_index("xtal_id")
        for grname, gr in histories.groupby(pd.cut(histories.TCDS, ranges)):    
            TCDSname = TCDSnames[i]
            gr["slope"]     = gr.index.map(df[("slope", TCDSname)])
            gr["intercept"] = gr.index.map(df[("intercept", TCDSname)])
            gr["time"] =  gr["time"] - (gr["temperature"]*gr["slope"] + gr["intercept"])
    
            gr = gr.drop(columns = ["slope", "intercept", "temperature", "TCDS"])
            grs.append(gr)
            i += 1
    
    else:
        for grname, gr in histories.groupby(pd.cut(histories.TCDS, ranges)):    
    
            TCDSname = TCDSnames[i]
            gr["slope"]     = df[("slope", TCDSname)].loc[args.ch]
            gr["intercept"] = df[("intercept", TCDSname)].loc[args.ch]
            gr["time"] =  gr["time"] - (gr["temperature"]*gr["slope"] + gr["intercept"])
    
            gr = gr.drop(columns = ["slope", "intercept", "temperature", "TCDS"])
        
            grs.append(gr)
            i += 1

    histories = pd.concat(grs).sort_index()
    del grs
    if stack: 
        histories = histories.reset_index().set_index("date")

    first_idx = histories["time"].first_valid_index()
    
    first = histories["time"].loc[first_idx]

    if not stack: histories["time"] = histories["time"] - first

    histories = histories.reset_index().set_index("xtal_id")
    ecal = ecalic.icCMS().iov
    ecal = ecal[(ecal['FED']  == FED)]
    ecal = ecal.reset_index().set_index(["elecID"])
    histories['ieta']  = histories.index.map(ecal["ix"])
    histories['iphi']  = histories.index.map(ecal.iy)
    histories = histories.reset_index()  
    
    histories = histories.drop(columns = ["xtal_id"])
    print (histories)

    all_histories.append(histories)

histories = pd.concat(all_histories)
del all_histories


print (histories.groupby(["run", "seq"]).size())


i = 0
iov = 0
for grname, gr in histories.groupby(["run", "seq"]):
    print(gr)
    gr = gr[~gr.index.duplicated(keep='first')]
    gr["part"] = 0
    
    print ("===>",gr["date"])
    gr["date"] = gr.date.values.astype(np.int64) // 10 ** 9
    idx = gr["date"].first_valid_index()
    print(idx)

    iov = gr["date"].loc[idx].item()
    print(iov)
    gr["ieta"] = gr["ieta"].astype("int") 
    gr["iphi"] = gr["iphi"].astype("int") 
    gr["part"] = gr["part"].astype("int") 
    gr["zero"] =  gr["part"].astype("float")
    gr[["ieta", "iphi", "part", "time", "zero"]].to_csv("/afs/cern.ch/work/c/camendol/LaserIOVs/"+str(year)+"/"+args.era+"/IOV"+str(i)+"_"+str(iov)+"_"+str(args.fed)+".txt", index = False, sep = " ", header = False)
    i += 1
