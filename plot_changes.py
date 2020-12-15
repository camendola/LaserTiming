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

parser.add_argument('--dump',    dest='dump',      help='dump tables',                    default=False,  action ='store_true')
parser.add_argument('--show',    dest='show',      help='show plots',                     default=False,  action ='store_true')
parser.add_argument('--isgreen', dest='isgreen',   help='green laser',                    default=False,  action ='store_true')
parser.add_argument('--temp',    dest='temp',      help='make correction by temperature', default=False,  action ='store_true')

args = parser.parse_args()


year = 2018
basedir = Path(f'/eos/cms/store/group/dpg_ecal/alca_ecalcalib/laser/dst.hdf')


workdir = "/afs/cern.ch/work/c/camendol/LaserData/"+str(year)+"/tables/"
if args.isgreen: workdir = "/afs/cern.ch/work/c/camendol/LaserData/"+str(year)+"/tables_green/"


FED = args.fed


filename = workdir + "FED_"+str(FED)+".hdf"

#get timing
histories     = pd.read_hdf(filename,key = "hist", mode = "r")
histories     = load_hdf.skim_history(histories, "time", year, args, basedir, FED, not args.isgreen)
histories     = load_hdf.stack_history(histories)
    
###get temperature
fullpath = load_hdf.make_path(year, args.isgreen)
sequence = pd.read_hdf((basedir / fullpath), 'sequence')
histories["temperature"] = histories.reset_index().set_index(["run","seq"]).index.map(sequence.set_index(["run", "seq"]).temperature)
histories = histories.reset_index().set_index(["date", "run","seq","temperature"])


#get TCDS - not in hdf: map directly from dst files 
dst_filelist = load.load_files(year, args.isgreen)
runlist = histories.reset_index().run.drop_duplicates().sort_values().tolist()
df_firstline = load.load_firstline(dst_filelist, year, fed = args.fed, runlist = runlist)

if year == 2018:
    #clean bunch of runs with bugged temperature
    histories = histories.reset_index().set_index(["date","seq","temperature"])
    
    histories = histories[(histories["run"] < 314344) | (histories["run"] > 314350)]
    histories = histories.reset_index().set_index(["date","run", "seq","temperature"])
    

histories["TCDS"] = histories.reset_index().set_index(["run","seq"]).index.map(df_firstline.reset_index().set_index(["run", "seq"]).TCDS)/1000000. # LHC freq [MHz]

histories = histories.reset_index().set_index("date")

histories.columns = ['run','seq','temperature','xtal_id', 'time', 'TCDS'] 
histories = histories[(histories['time'] > -10) & (histories['time'] < 10)] 
print (histories)



left = 0.
right = 1.
top = 1.


# delays map - make full FED
if True:
    ecal = ecalic.icCMS().iov
    ecal = ecal[(ecal['FED']  == args.fed)]
    for hwchanges in [318111,323110,327775]:
        print (hwchanges in runlist)

        if not histories[histories["run"] > hwchanges].empty:
            histories = histories.reset_index().set_index(["xtal_id"])
            run_after = histories[histories["run"] >= hwchanges]
            #print(run_after)
            #print(run_after.groupby('run'))
            #print(run_after.groupby('run').first().iloc[0].name)
            run_after = run_after.groupby('run').get_group(run_after.groupby('run').first().iloc[0].name)

            ranges = [40.0784, 40.0785, 40.0789, 40.07897, 40.0790, 40.07915, 40.0793] #TCDS ranges
            TCDSnames = ["TCDS"+str(i) for i in range (1,7)]
            fitfile = "fits_results/temperature/FEDX_ch_split_rootfit"
            if args.isgreen: filename = "fits_results/temperature/FEDX_ch_split_rootfit_green"
            fitfile  = fitfile + ".csv"
            if args.fed:
                df = pd.read_csv(fitfile.replace("X", str(args.fed)), index_col=[0,1],  header=[0, 1], skipinitialspace=True)
            df.columns = pd.MultiIndex.from_tuples(df.columns)
            
            df = df.reset_index().set_index(["ch", "FED", ("TCDS","TCDS1"),("TCDS","TCDS2"),("TCDS","TCDS3"),("TCDS","TCDS4"),("TCDS","TCDS5"), ("TCDS","TCDS6")])
            df = df[(df.T != 0).any()]
            df = df.reset_index().set_index("ch")
            df = df[(df["FED"] > 609)]
            #df = df.reset_index().set_index(["ch", "FED"])
            print (df)
            first_idx = histories["time"].first_valid_index()
            first = histories.loc[first_idx] 

            i = 0
            grs = []
            first = first.reset_index().set_index(["xtal_id"])
            for grname, gr in first.groupby(pd.cut(first.TCDS, ranges)):    
                print(grname)
                TCDSname = TCDSnames[i]
        
                gr["slope"]     = gr.index.map(df[("slope", TCDSname)])
                gr["intercept"] = gr.index.map(df[("intercept", TCDSname)])
                gr["corrtime"]  = gr["time"] - (gr["temperature"]*gr["slope"] + gr["intercept"])
                print (gr[["slope", "intercept", "run"]])
                gr = gr.drop(columns = ["slope", "intercept"])
                grs.append(gr)
                i += 1
        
            first = pd.concat(grs)
            del grs

            i = 0
            grs = []
            run_after = run_after.reset_index().set_index(["xtal_id"])
            for grname, gr in run_after.groupby(pd.cut(run_after.TCDS, ranges)):    
                print(grname)
                TCDSname = TCDSnames[i]
        
                gr["slope"]     = gr.index.map(df[("slope", TCDSname)])
                gr["intercept"] = gr.index.map(df[("intercept", TCDSname)])
                gr["corrtime"]  = gr["time"] - (gr["temperature"]*gr["slope"] + gr["intercept"])
                print (gr[["slope", "intercept", "run"]])
                gr = gr.drop(columns = ["slope", "intercept"])
                grs.append(gr)
                i += 1
        
            run_after = pd.concat(grs)
            del grs
        
 
            #run_after["corrtime"] = run_after["corrtime"] - first["corrtime"]


            run_before = histories[histories["run"] < hwchanges]
            run_before = run_before.groupby('run').get_group(run_before.groupby('run').last().iloc[-1].name)
            i = 0
            grs = []
            run_before = run_before.reset_index().set_index(["xtal_id"])
            for grname, gr in run_before.groupby(pd.cut(run_before.TCDS, ranges)):    
                print(grname)
                TCDSname = TCDSnames[i]
        
                gr["slope"]     = gr.index.map(df[("slope", TCDSname)])
                gr["intercept"] = gr.index.map(df[("intercept", TCDSname)])
                gr["corrtime"]  = gr["time"] - (gr["temperature"]*gr["slope"] + gr["intercept"])
                print (gr[["slope", "intercept", "run"]])
                gr = gr.drop(columns = ["slope", "intercept"])
                grs.append(gr)
                i += 1
        
            run_before = pd.concat(grs)
            del grs
        
            #run_before["corrtime"] = run_before["corrtime"] - first["corrtime"]


            fig, ax = plt.subplots(figsize= (7, 18))

            print(run_after)
            print(run_before)

            diff = run_after[["corrtime"]].sub(run_before[["corrtime"]], axis = 0)
            print (diff)
            diff = diff.reset_index().set_index(["xtal_id"])
            ecal = ecal.reset_index().set_index(["elecID"])
            diff['ieta']    = diff.index.map(ecal["ix"])
            diff['iphi']    = diff.index.map(ecal.iy)
            diff['TT']      = diff.index.map(ecal["ccu"])
            print(diff.groupby("TT").mean())
            print (diff)
            sns.heatmap(diff.pivot_table(columns = "iphi", index = "ieta", values = "corrtime").sort_index(ascending = False), cbar_kws={'label': "Difference $\Delta (t_{xtal} - t_{MATACQ})$ [ns]"}, ax = ax)
            sns.color_palette("coolwarm")
            ax.text(left, top, "FED: "+str(args.fed),
                    horizontalalignment='left',
                    verticalalignment='bottom',
                    transform=ax.transAxes)
            ax.text(right, top, str(run_after["run"].values[0]) +"-"+ str(run_before["run"].values[0]),
                    horizontalalignment='right',
                    verticalalignment='bottom',
                    transform=ax.transAxes)
            ax.set(xlabel='i$\phi$', ylabel='i$\eta$')
            fig.show()
            input()
