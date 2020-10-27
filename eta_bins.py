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

from pylab import *
from scipy.optimize import curve_fit

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

import statistics

def linear_fit(x, b, m):
    y = b + m * x
    return y



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
    first_run = runlist[0]
    first = histories.copy().reset_index().set_index("date")
    first = first[((first["run"] == first_run) & (first["seq"] == 0))]
    first = first.reset_index().set_index(["date", "run","seq","temperature"])
    
    histories = histories.reset_index().set_index(["date", "run","seq","temperature"])
    histories = histories.T.sub(first.T[first.T.columns[0]], axis = 0).T
    
    #histories = histories.reset_index().set_index(["run","seq"])
    #print(histories[(histories["date"] < "2018-04-16 00:00:00") & (histories["date"] >= "2018-04-15 00:00:00")])
    #histories = histories.reset_index().set_index(["date", "run","seq","temperature"])
    
    #clean bunch of runs with bugged temperature
    histories = histories.reset_index().set_index(["date","seq","temperature"])
    histories = histories[(histories["run"] < 314344) | (histories["run"] > 314350)] 
    histories = histories.reset_index().set_index(["date","run", "seq","temperature"])


    #get TCDS - not in hdf: map directly from dst files for selected runs
    dst_filelist = load.load_files(year)
    df_firstline = load.load_firstline(dst_filelist, year, fed = args.fed, runlist = runlist)

    histories = histories[(histories > -5) & (histories < 5)]

    histories["TCDS"] = histories.reset_index().set_index(["run","seq"]).index.map(df_firstline.reset_index().set_index(["run", "seq"]).TCDS)/1000000. # LHC freq [MHz]
    
    histories = histories.reset_index().set_index("date").drop(columns=['seq','run'])

    all_histories.append(histories)

histories = pd.concat(all_histories)
del all_histories
histories = histories.reset_index().set_index(["date","temperature","TCDS"]).T.reset_index().set_index("xtal_id").drop(columns = ["side", "iphi", "ieta"]).T




histories = histories.reset_index().set_index(["date","temperature","TCDS"]).stack().reset_index().set_index(["date"])
histories.columns =  ["temperature", "TCDS", "xtal_id","time"]

# plots
rmin = str(runlist[0])
rmax = str(runlist[-1])

runlabel = rmin+"-"+rmax
if (runlist[0] == runlist[-1]): runlabel = str(runlist[0])

left = 0.
right = 1.
top = 1.

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
u_slope = []
intercept = []
u_intercept = []
TCDS = []
#for grname, gr in histories.groupby(pd.cut(histories.TCDS, ranges)):
#    m = 0
#    b = 0
#    u_m = 0
#    u_b = 0
#    f = np.nan
#    if not gr.empty:
#        gr = gr.dropna()
#        f = gr["TCDS"].mean()    
#        fit,cov=curve_fit(linear_fit,gr["temperature"],gr["time"])
#        b = fit[0]
#        m = fit[1]
#        u_b = sqrt(cov[0][0])
#        u_m = sqrt(cov[1][1])
#        #m, b= np.polyfit(gr["temperature"], gr["time"], 1)
#
#        if b > 0: 
#            flabel ="%.2f $\cdot$T +%.2f" % (m, b)
#        else:
#            flabel ="%.2f $\cdot$T %.2f" % (m, b)
#        plt.plot(gr["temperature"], m*gr["temperature"] + b, color = sc.to_rgba(f), label = flabel)
#    slope.append(m)
#    intercept.append(b)
#    u_slope.append(u_m)
#    u_intercept.append(u_b)
#    TCDS.append(f)


# for simultaneous fit
grs = []
grs_index = []

for grname, gr in histories.groupby(pd.cut(histories.TCDS, ranges)):
    i = 1
    if gr.empty:
        m = 0
        b = 0
        u_m = 0
        u_b = 0
        f = np.nan
        slope.append(m)
        intercept.append(b)
        u_slope.append(u_m)
        u_intercept.append(u_b)
        TCDS.append(f)
    else: 
        grs.append(gr)
        grs_index.append(i)
    i = i+1

print(grs_index)



x1 = grs[0]["temperature"]
x2 = grs[1]["temperature"]

y1 = grs[0]["time"]
y2 = grs[1]["time"]

z1 = grs[0]["TCDS"]
z2 = grs[1]["TCDS"]

grs[0][["temperature","time"]].to_csv("fits_results/temperature/FED_%d_ieta_%.1f_TCSD2.csv" % (args.fed, statistics.mean([args.ietamin, args.ietamax])), sep=" ", header=True)
grs[1][["temperature","time"]].to_csv("fits_results/temperature/FED_%d_ieta_%.1f_TCSD3.csv" % (args.fed, statistics.mean([args.ietamin, args.ietamax])), sep=" ", header=True)

x = np.append(x1, x2)
y = np.append(y1, y2)

def sim_linear_fit(X, b1, b2, m):
    y1 = b1 + m * X[:len(x1)]
    y2 = b2 + m * X[len(x1):]
    return np.append(y1 , y2)

fit, cov = curve_fit(sim_linear_fit, x, y)

b1 = fit[0]
b2 = fit[1]
m  = fit[2]
u_b1 = sqrt(cov[0][0])
u_b2 = sqrt(cov[1][1])
u_m  = sqrt(cov[2][2])

flabel ="%.2f $\cdot$T %.2f" % (m, b1)
plt.plot(x1, m*x1 + b1, color = sc.to_rgba(z1.mean()), label = flabel)
flabel ="%.2f $\cdot$T %.2f" % (m, b2)
plt.plot(x2, m*x2 + b2, color = sc.to_rgba(z2.mean()), label = flabel)

slope.insert(grs_index[0], m)
slope.insert(grs_index[1], m)
intercept.insert(grs_index[0],b1)
intercept.insert(grs_index[1],b2)
u_slope.insert(grs_index[0], u_m)
u_slope.insert(grs_index[1], u_m)
u_intercept.insert(grs_index[0], u_b1)
u_intercept.insert(grs_index[1], u_b2)
TCDS.insert(grs_index[0], z1.mean())
TCDS.insert(grs_index[1], z2.mean())



write_csv.save_fit(args.fed, args.ch, args.ietamin, args.ietamax, slope,u_slope, intercept, u_intercept, TCDS)

if args.show:
    plt.legend()
    fig.show()
    
    input()



