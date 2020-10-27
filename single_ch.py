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
import matplotlib.patches as patches

mpl.rcParams['axes.linewidth'] = 2
mpl.rcParams['axes.formatter.useoffset'] = False

mpl.rcParams['xtick.direction'] = 'in'
mpl.rcParams['ytick.direction'] = 'in'
mpl.rcParams["ytick.right"] = True
mpl.rcParams["xtick.top"] = True

from elmonk.common.helper import scalar_to_list, make_index
import seaborn as sns

import argparse
from tqdm import tqdm

import modules.load_hdf as load_hdf           # methods for histories from hdf files
import modules.load as load                   # methods for dst files 
import modules.write_csv as write_csv        

parser = argparse.ArgumentParser(description='Command line parser of plotting options')

parser.add_argument('--fed',     dest='fed',type=int, help='fed', default=None)
parser.add_argument('--ch',      dest='ch',type=int, help='ch', default=-1)
parser.add_argument('--rmin',    dest='rmin',type=int, help='rmin', default=None)
parser.add_argument('--rmax',    dest='rmax',type=int, help='rmax', default=None)
parser.add_argument('--ietamin', dest='ietamin',type=int, help='ietamin', default=-999)
parser.add_argument('--ietamax', dest='ietamax',type=int, help='ietamax', default=-999)
parser.add_argument('--long',    dest='long',   help='use only longest run', default=False,  action ='store_true')
parser.add_argument('--show',    dest='show',   help='show plots', default=False,  action ='store_true')

args = parser.parse_args()

if args.fed == -1:
    FEDs = [int(x) for x in range(610,627)] 
elif args.fed == 1:
    FEDs = [int(x) for x in range(628,645)] 
elif args.fed: 
    FEDs = [args.fed]
else:
    FEDs = [int(x) for x in range(610,645)] 

year = 2018
basedir = Path(f'/eos/cms/store/group/dpg_ecal/alca_ecalcalib/laser/dst.hdf')

workdir = "/afs/cern.ch/work/c/camendol/LaserData/"+str(year)+"/tables/"
all_histories = []

for FED in FEDs:
    filename = workdir + "FED_"+str(FED)+".hdf"

    #get timing
    histories = pd.read_hdf(filename,key = "hist", mode = "r")
    histories = histories.reset_index().set_index(["date","seq","run"])
    histories = histories.T.reset_index()
    histories = load_hdf.append_idxs(histories, args.ch, args.ietamin, args.ietamax).T
    
    #get matacq tstart
    histories = load_hdf.subtract_tmatacq(histories, year, basedir, FED)
    
    first_run = histories.reset_index().run.drop_duplicates().sort_values().tolist()[0]
    first = histories.copy().reset_index().set_index("date")
    first = first[((first["run"] == first_run) & (first["seq"] == 0))]
    first = first.reset_index().set_index(["date", "run","seq"])
    
    histories = histories.reset_index().set_index(["date", "run","seq"])
    histories = histories.T.sub(first.T[first.T.columns[0]], axis = 0).T
    
    #get apd/pn
    
    histories_APD = pd.read_hdf(filename.replace("tables", "tables_APD_PN"),key = "hist", mode = "r")
    histories_APD = histories_APD.reset_index().set_index(["date","seq","run"]).T.reset_index()
    histories_APD = load_hdf.append_idxs(histories_APD, args.ch, args.ietamax, args.ietamin).T
    first = histories_APD.copy().reset_index().set_index("date")
    first = first[((first["run"] == first_run) & (first["seq"] == 0))]
    first = first.reset_index().set_index(["date", "run","seq"])
    histories_APD = histories_APD.reset_index().set_index(["date", "run","seq"])
    histories_APD = histories_APD.T.divide(first.T[first.T.columns[0]], axis = 0).T
    
    #merge apd/pn in histories
    print (histories)
    histories = pd.concat([histories,histories_APD],axis=1,keys=['time','APD_PN']).swaplevel(0,1,axis=1).sort_index(axis=1)
    
    #get temperature
    sequence = pd.read_hdf((basedir / f'{year}/dstUL_db.{year}.hdf5'), 'sequence')
    histories["temperature"] = histories.reset_index().set_index(["run","seq"]).index.map(sequence.set_index(["run", "seq"]).temperature)
    histories = histories.reset_index().set_index(["date", "run","seq","temperature"])
    
    if args.rmin or args.rmax:
        histories = histories.reset_index().set_index(["date", "seq","temperature"])
        if args.rmin: histories = histories[(histories["run"] >= args.rmin)]
        if args.rmax: histories = histories[(histories["run"] <= args.rmax)]
        histories = histories.reset_index().set_index(["date", "run","seq","temperature"])
        
    runlist = histories.reset_index().run.drop_duplicates().sort_values().tolist()

    #get TCDS - not in hdf: map directly from dst files for selected runs
    dst_filelist = load.load_files(year)
    df_firstline = load.load_firstline(dst_filelist, year, fed = args.fed, runlist = runlist)

    histories = histories[(histories > -5) & (histories < 5)]
    
    histories["TCDS"] = histories.reset_index().set_index(["run","seq"]).index.map(df_firstline.reset_index().set_index(["run", "seq"]).TCDS)/1000000. # LHC freq [MHz]
    
    histories = histories.reset_index().set_index("date").drop(columns=['seq','run'])
    histories.columns = ["temperature", "APD_PN", "time","TCDS"]
    all_histories.append(histories)

histories = pd.concat(all_histories)
del all_histories

# plots
rmin = str(runlist[0])
rmax = str(runlist[-1])
runlabel = rmin+"-"+rmax
if (runlist[0] == runlist[-1]): runlabel = str(runlist[0])

left = 0.
right = 1.
top = 1.

fig, axs = plt.subplots(2, sharex=True, gridspec_kw={'hspace': 0})

axs[0].plot(histories["time"], marker=".", linestyle = "--")
axs[0].set_ylabel("$\Delta (t_{xtal} - t_{MATACQ})$ [ns]")
axs[1].plot(histories["temperature"], marker=".", linestyle = "--")
axs[1].set_ylabel("T [$^\circ$C]")
axs[1].set_xlabel("date")
axs[0].text(right, top, rmin+"-"+rmax,
            horizontalalignment='right',
            verticalalignment='bottom',
            transform=axs[0].transAxes)
axs[0].text(left, top, "FED: "+str(args.fed)+", ch: "+str(args.ch),
            horizontalalignment='left',
            verticalalignment='bottom',
            transform=axs[0].transAxes)

# hide x labels and tick labels for all but bottom plot
for ax in axs:
    ax.label_outer()
plt.xticks(rotation=45)
fig.tight_layout()
fig.show()

fig, ax = plt.subplots()
sc = ax.scatter(histories["temperature"], histories["time"], marker = ".", s = 50, c =  histories["TCDS"])
ax.set_xlabel("T [$^\circ$ C]")
ax.set_ylabel("$\Delta (t_{xtal} - t_{MATACQ})$ [ns]")
cb = plt.colorbar(sc)
cb.set_label('TCDS [MHz]')

ax.text(right, top, rmin+"-"+rmax,
        horizontalalignment='right',
        verticalalignment='bottom',
        transform=ax.transAxes)
ax.text(left, top, "FED: "+str(args.fed)+", ch: "+str(args.ch),
        horizontalalignment='left',
        verticalalignment='bottom',
        transform=ax.transAxes)


ranges = [40.0784, 40.0785, 40.0789, 40.0790, 40.07915, 40.0793] #TCDS ranges
slope = []
offset = []
TCDS = []
for grname, gr in histories.groupby(pd.cut(histories.TCDS, ranges)):
    m = 0
    b = 0
    f = np.nan
    if not gr.empty:
        gr = gr.dropna()
        f = gr["TCDS"].mean()
        m, b= np.polyfit(gr["temperature"], gr["time"], 1)
        print(m, b)
        print(m*gr["temperature"] + b)
        if b > 0: 
            flabel ="%.2f $\cdot$T +%.2f" % (m, b)
        else:
            flabel ="%.2f $\cdot$T %.2f" % (m, b)
        plt.plot(gr["temperature"], m*gr["temperature"] + b, color = sc.to_rgba(f), label = flabel)
    slope.append(m)
    offset.append(b)
    TCDS.append(f)

write_csv.save_fit(args.fed, args.ch, args.ietamin, args.ietamax, slope, offset, TCDS)
if args.show:
    plt.legend()
    fig.show()
    
    input()
fig, axs = plt.subplots(2, sharex=True, gridspec_kw={'hspace': 0})

axs[0].plot(histories["time"], marker=".", linestyle = "--")
axs[0].set_ylabel("$\Delta (t_{xtal} - t_{MATACQ})$ [ns]")
axs[1].plot(histories["APD_PN"], marker=".", linestyle = "--")
axs[1].set_ylabel("Relative APD/PN")
axs[1].set_xlabel("date")
axs[0].text(right, top, rmin+"-"+rmax,
            horizontalalignment='right',
            verticalalignment='bottom',
            transform=axs[0].transAxes)
axs[0].text(left, top, "FED: "+str(args.fed)+", ch: "+str(args.ch),
            horizontalalignment='left',
            verticalalignment='bottom',
            transform=axs[0].transAxes)

# Hide x labels and tick labels for all but bottom plot.
for ax in axs:
    ax.label_outer()
plt.xticks(rotation=45)
fig.tight_layout()
fig.show()

fig, ax = plt.subplots()
sc = ax.scatter(histories["APD_PN"], histories["time"], marker=".", s=50, c =  histories["TCDS"])
plt.colorbar(sc)
ax.set_xlabel("Relative APD/PN")
ax.set_ylabel("$\Delta (t_{xtal} - t_{MATACQ})$ [ns]")
ax.text(right, top, rmin+"-"+rmax,
        horizontalalignment='right',
        verticalalignment='bottom',
        transform=ax.transAxes)
ax.text(left, top, "FED: "+str(args.fed)+", ch: "+str(args.ch),
        horizontalalignment='left',
        verticalalignment='bottom',
        transform=ax.transAxes)
fig.show()
input()


