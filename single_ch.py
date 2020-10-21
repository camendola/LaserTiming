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

from elmonk.common.helper import scalar_to_list, make_index
import seaborn as sns

import argparse
from tqdm import tqdm

import modules.load_hdf as load_hdf # methods for histories from hdf files
import modules.load as load         # methods for dst files 

parser = argparse.ArgumentParser(description='Command line parser of plotting options')

parser.add_argument('--fed',    dest='fed',type=int, help='fed', default=612)
parser.add_argument('--ch',    dest='ch',type=int, help='ch', default=0)
parser.add_argument('--rmin',    dest='rmin',type=int, help='rmin', default=None)
parser.add_argument('--rmax',    dest='rmax',type=int, help='rmax', default=None)
parser.add_argument('--temp',    dest='temp',type=int, help='plot temperature', default=0)
parser.add_argument('--single', dest='single', help='write single sequence and run', action='store_true')
parser.add_argument('--long',   dest='long',   help='use only longest run', default=False,  action ='store_true')

args = parser.parse_args()

FED = args.fed

year = 2018
basedir = Path(f'/eos/cms/store/group/dpg_ecal/alca_ecalcalib/laser/dst.hdf')

workdir = "/afs/cern.ch/work/c/camendol/LaserData/"+str(year)+"/tables/"
filename = workdir + "FED_"+str(FED)+".hdf"

#get timing
histories = pd.read_hdf(filename,key = "hist", mode = "r")
histories = histories.reset_index().set_index(["date","seq","run"])
histories = histories.T.reset_index()
histories = load_hdf.append_idxs(histories, args.ch).T

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
histories_APD = load_hdf.append_idxs(histories_APD, args.ch).T
first = histories_APD.copy().reset_index().set_index("date")
first = first[((first["run"] == first_run) & (first["seq"] == 0))]
first = first.reset_index().set_index(["date", "run","seq"])
histories_APD = histories_APD.reset_index().set_index(["date", "run","seq"])
histories_APD = histories_APD.T.divide(first.T[first.T.columns[0]], axis = 0).T

#merge apd/pn in histories
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
rmin = str(runlist[0])
rmax = str(runlist[-1])

#get TDCS - not in hdf: map directly from dst files for selected runs
dst_filelist = load.load_files(year)
dst_filelist = dst_filelist[dst_filelist["run"].isin(runlist)]
dst = load.load_ch_firstline(dst_filelist, args.ch , year, fed = args.fed)

histories = histories[(histories > -5) & (histories < 5)]
run_chunks = []
for run,gr in histories.reset_index().groupby("run"):
    sTCDS = dst[(dst["run"] == int(run))].TCDS
    if sTCDS.size > 0:
        gr["TCDS"] = sTCDS.values[0]/1000   #LHC freq in MHz
    else:
        gr["TCDS"] = 0   #LHC freq in MHz
    run_chunks.append(gr)
histories = pd.concat(run_chunks)
del run_chunks

histories = histories.reset_index().set_index("date").drop(columns=['seq','run', 'index'])
histories.columns = ["temperature", "APD_PN", "time","TCDS"]

# plots
left = 0.
right = 1.
top = 1.

fig, axs = plt.subplots(2, sharex=True, gridspec_kw={'hspace': 0})

axs[0].plot(histories["time"], marker=".", linestyle = "--")
axs[0].set_ylabel("$(t_{xtal} - t_{MATACQ})(t)-(t_{xtal} - t_{MATACQ})(0)$ [ns]")
axs[1].plot(histories["temperature"], marker=".", linestyle = "--")
axs[1].set_ylabel("$T [^\circ C]$")
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
ax.scatter(histories["temperature"], histories["time"], marker = ".", s = 50, c =  histories["TCDS"])
ax.set_xlabel("$T [^\circ C]$")
ax.set_ylabel("$(t_{xtal} - t_{MATACQ})(t)-(t_{xtal} - t_{MATACQ})(0)$ [ns]")
ax.text(right, top, rmin+"-"+rmax,
        horizontalalignment='right',
        verticalalignment='bottom',
        transform=ax.transAxes)
ax.text(left, top, "FED: "+str(args.fed)+", ch: "+str(args.ch),
        horizontalalignment='left',
        verticalalignment='bottom',
        transform=ax.transAxes)
fig.show()


fig, axs = plt.subplots(2, sharex=True, gridspec_kw={'hspace': 0})

axs[0].plot(histories["time"], marker=".", linestyle = "--")
axs[0].set_ylabel("$(t_{xtal} - t_{MATACQ})(t)-(t_{xtal} - t_{MATACQ})(0)$ [ns]")
axs[1].plot(histories["APD_PN"], marker=".", linestyle = "--")
axs[1].set_ylabel("$(APD/PN)(t)/(APD/PN)(0)$")
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
ax.scatter(histories["APD_PN"], histories["time"], marker=".", s=50, c =  histories["TCDS"])
ax.set_xlabel("$(APD/PN)(t)/(APD/PN)(0)$")
ax.set_ylabel("$(t_{xtal} - t_{MATACQ})(t)-(t_{xtal} - t_{MATACQ})(0)$ [ns]")
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


