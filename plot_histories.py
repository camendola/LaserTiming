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

parser.add_argument('--fed',     dest='fed',type=int, help='fed', default=None)
parser.add_argument('--ch',      dest='ch',type=int, help='ch', default=-1)
parser.add_argument('--rmin',    dest='rmin',type=int, help='rmin', default=-1)
parser.add_argument('--rmax',    dest='rmax',type=int, help='rmax', default=-1)
parser.add_argument('--ietamin', dest='ietamin',type=int, help='ietamin', default=-999)
parser.add_argument('--ietamax', dest='ietamax',type=int, help='ietamax', default=-999)
parser.add_argument('--iphimin', dest='iphimin',type=int, help='iphimin', default=-999)
parser.add_argument('--iphimax', dest='iphimax',type=int, help='iphimax', default=-999)
parser.add_argument('--TT',      dest='TT',type=int, help='TT', default=-999)


parser.add_argument('--side', dest='side',type=int, help='side', default=-1)
parser.add_argument('--dump',    dest='dump',   help='dump tables', default=False,  action ='store_true')
parser.add_argument('--show',    dest='show',   help='show plots', default=False,  action ='store_true')
parser.add_argument('--isgreen',    dest='isgreen',   help='green laser', default=False,  action ='store_true')

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
if args.isgreen: workdir = "/afs/cern.ch/work/c/camendol/LaserData/"+str(year)+"/tables_green/"
all_histories = []



for FED in FEDs:
    filename = workdir + "FED_"+str(FED)+".hdf"

    tables = []
    stack = False
    if (args.ch < 0):  stack = True

    #get timing
    histories_time = pd.read_hdf(filename,key = "hist", mode = "r")
    histories_rawtime = load_hdf.skim_history(histories_time, "time", year, args,  basedir, FED, False)

    histories_time = load_hdf.skim_history(histories_time, "time", year, args, basedir, FED, not args.isgreen)
    
    if args.ch > - 1:
        ##get tmatacq timing
        histories_tmatacq = load_hdf.load_tmatacq(histories_time, year, basedir, FED, args.rmin, args.rmax, args.isgreen)
        histories_tmatacq = histories_tmatacq.sub(histories_tmatacq.iloc[0])
    #
    if stack:         histories_time    = load_hdf.stack_history(histories_time)
    if stack:         histories_rawtime = load_hdf.stack_history(histories_rawtime)
    print(histories_rawtime)
    print(histories_time)
    tables.append(histories_rawtime)
    tables.append(histories_time)    
    if args.ch > - 1:
        if stack:         histories_tmatacq = load_hdf.stack_history(histories_tmatacq)    
        tables.append(histories_tmatacq)
        
    #get apd/pn
    filenameAPD = filename.replace("tables", "tables_APD_PN")
    if args.isgreen: filenameAPD = filename.replace("tables_green", "tables_green_APD_PN")
    histories_APD = pd.read_hdf(filenameAPD,key = "hist", mode = "r")
    histories_APD = load_hdf.skim_history(histories_APD, "APD_PN", year, args, basedir, FED)
    if stack:         histories_APD = load_hdf.stack_history(histories_APD)
    tables.append(histories_APD)


    #merge timing and apd/pn
    histories = pd.concat(tables,axis=1,keys=['time','rawtime', 'tmatacq','APD_PN'] if args.ch > -1 else ['time','rawtime','APD_PN']).swaplevel(0,1,axis=1).sort_index(axis=1)

    #histories = histories[(histories["","","time"] > -5) & (histories["","","time"] < 5)] 
    print(histories[(histories> -100)])
    histories = histories[(histories> -5) & (histories < 5)] 
    del tables


    #get temperature
    fullpath = f'{year}/dst.{year}.w447.hdf5' if not args.isgreen else f'{year}/dst.{year}.w527.hdf5'
    sequence = pd.read_hdf((basedir / fullpath), 'sequence')
    histories["temperature"] = histories.reset_index().set_index(["run","seq"]).index.map(sequence.set_index(["run", "seq"]).temperature)
    histories = histories.reset_index().set_index(["date", "run","seq","temperature"])
    
    #get TCDS - not in hdf: map directly from dst files 
    #dst_filelist = load.load_files(year)
    root_dir = "/eos/cms/store/group/dpg_ecal/alca_ecalcalib/laser/dst.merged/2018/"
    dst_filelist = []
    for filename in glob.iglob(root_dir + '**/*.corlinpn', recursive=True):
        if not args.isgreen:
            if "447" in filename: dst_filelist.append(filename)
        else:
            if "527" in filename: dst_filelist.append(filename)
    runlist = histories.reset_index().run.drop_duplicates().sort_values().tolist()
    df_firstline = load.load_firstline(dst_filelist, year, fed = args.fed, runlist = runlist)
    

    if year == 2018:
        #clean bunch of runs with bugged temperature
        histories = histories.reset_index().set_index(["date","seq","temperature"])
        histories = histories[(histories["run"] < 314344) | (histories["run"] > 314350)]
        histories = histories.reset_index().set_index(["date","run", "seq","temperature"])

    histories["TCDS"] = histories.reset_index().set_index(["run","seq"]).index.map(df_firstline.reset_index().set_index(["run", "seq"]).TCDS)/1000000. # LHC freq [MHz]
    
    histories = histories.reset_index().set_index("date").drop(columns=['seq','run'])
    all_histories.append(histories)

histories = pd.concat(all_histories)
del all_histories


histories.columns = ['temperature','xtal_id', 'APD_PN','rawtime','time', 'TCDS'] if stack else ['temperature','APD_PN','rawtime','time','tmatacq','TCDS']
print (histories)

# plots
rmin = str(runlist[0])
rmax = str(runlist[-1])
runlabel = rmin+"-"+rmax
if (runlist[0] == runlist[-1]): runlabel = str(runlist[0])

print("Mean temperature: ", histories["temperature"].mean(), " C")

histories = histories.dropna()
histories["tdiff"] = histories["rawtime"]- histories["tmatacq"]
print(histories[["rawtime", "tmatacq", "time", "tdiff"]])


chunks = histories.reset_index()
chunks = chunks[["run", "seq", "temperature", "TCDS"]]
print(chunks)

ranges = [40.0784, 40.0785, 40.0789, 40.07897, 40.0790, 40.07915, 40.0793] #TCDS ranges

if args.dump:
    dump = histories["time"].to_frame()
    dump["temperature"] = histories.temperature
    #dump["xtal_id"] = histories.xtal_id
    dump["TCDS"] = histories.TCDS
    dump["run"] = histories.run
    dump["seq"] = histories.seq
    dump["APD_PN"] = histories.APD_PN
    dump = dump.reset_index()
    dump["date"] = dump.date.values.astype(np.int64) // 10 ** 9 #c onvert to timestamp 
    #dumpfile = "/afs/cern.ch/user/c/camendol/public/xFederico/FED616_green_ch1550.dat"
    
    dumpfile = "/afs/cern.ch/work/c/camendol/LaserData/"+str(year)+"/history_FED%d.dat" %(FED)
    if args.isgreen:  dumpfile = "/afs/cern.ch/work/c/camendol/LaserData/"+str(year)+"/green/history_FED%d.dat" %(FED)

    dump.to_csv(dumpfile, index = False)
    

left = 0.
right = 1.
top = 1.

##### TCDS history + histogram pad
if False: 
    leftp, width = 0.1, 0.65
    bottom, height = 0.1, 0.65
    spacing = 0.005
    
    rect_scatter = [leftp, bottom, width, height]
    rect_histy = [leftp + width + spacing, bottom, 0.2, height]
    
    plt.figure(figsize=(10,5))
    
    ax_scatter = plt.axes(rect_scatter)
    ax_scatter.tick_params(direction='in', top=True, right=True)
    ax_histy = plt.axes(rect_histy)
    ax_histy.tick_params(direction='in', labelleft=False)
    
    ax_scatter.scatter(histories.reset_index().date,histories.TCDS,  marker=".",s = 50, linestyle = "--")
    ax_scatter.set_ylim(40.0784, 40.0793)
    
    ax_histy.hist(histories.TCDS, bins=100, orientation='horizontal')
    ax_histy.set_ylim(ax_scatter.get_ylim())
    ax_scatter.set_ylabel("TCDS freq. [MHz]")
    ax_scatter.axvline(pd.Timestamp('2018-04-20'), lw=2, color='red', alpha=0.4)
    ax_scatter.set_xlabel("date")
    ax_histy.text(right, top, runlabel,
                  horizontalalignment='right',
                  verticalalignment='bottom',
                  transform=ax_histy.transAxes)
    ax_scatter.text(pd.Timestamp('2018-04-20'),40.079,'beginning of collisions',
                    horizontalalignment='right',
                    verticalalignment='center',
                    rotation='vertical',
                    color='r')
    
    ax_scatter.tick_params(axis="x", labelrotation = 45)
    
    if args.show:
        plt.show()
        #plt.savefig("/eos/home-c/camendol/www/LaserTiming/blue_t_vs_T/TCDS_2018_history.pdf", bbox_inches='tight')
        #plt.savefig("/eos/home-c/camendol/www/LaserTiming/blue_t_vs_T/TCDS_2018_history.png", bbox_inches='tight')
        input()

## summary history plot: time, temperature, APD_PN, TCDS in colorbar
if False:
    fig, axs = plt.subplots(figsize= (10, 5), ncols=2, nrows=3, sharex=True, gridspec_kw={'hspace': 0, "width_ratios":[95,5], 'wspace': 0.001,})
    axs[0][0].plot(histories.reset_index().date,histories.time,  marker=".", markersize = 1, linestyle = "--", zorder = 0)
    sc = axs[0][0].scatter(histories.reset_index().date,histories.time,  marker=".",s = 50, c =  histories["TCDS"], linestyle = "--", zorder = 5)
    
    axs[0][0].set_ylabel("$\Delta (t_{xtal} - t_{MATACQ})$ [ns]")
    axs[1][0].plot(histories["temperature"], marker=".", linestyle = "--")
    axs[1][0].set_ylabel("T [$^\circ$C]")
    #axs[1][0].plot(histories["rawtime"], marker=".", linestyle = "--")
    #axs[1][0].set_ylabel("$\Delta (t_{xtal})$ [ns]")
    #axs[1][0].plot(histories["APD_PN"], marker=".", linestyle = "--")
    #axs[1][0].set_ylabel("Relative APD/PN")

    axs[2][0].plot(histories["APD_PN"], marker=".", linestyle = "--")
    #axs[2][0].plot(histories["tmatacq"], marker=".", linestyle = "--")
    axs[2][0].set_ylabel("Relative APD/PN")
    #axs[2][0].set_ylabel("$\Delta (t_{MATACQ})$ [ns]")
    axs[1][0].set_xlabel("date")
    axs[0][0].text(right, top, runlabel,
                   horizontalalignment='right',
                   verticalalignment='bottom',
                   transform=axs[0][0].transAxes)
    axs[0][0].text(left, top, "FED: "+str(args.fed)+", ch: "+str(args.ch),
                   horizontalalignment='left',
                   verticalalignment='bottom',
                   transform=axs[0][0].transAxes)
    
    for i in range(0,2):
        axs[i][0].tick_params(axis="x", labelbottom=0)
    for i in range(0,3):
        axs[i][1].axis("off")


    fig.tight_layout()
    plt.colorbar(axs[0][0].collections[0], ax=axs[0][1], label='TCDS [MHz]')

    axs[2][0].tick_params(axis="x", labelrotation = 45)
    axs[2][0].autoscale(enable=True, axis='x', tight=True)

    if args.show:
        fig.show()
        #fig.savefig("/eos/home-c/camendol/www/LaserTiming/blue_t_vs_T/summary_614.pdf", bbox_inches='tight')
        #fig.savefig("/eos/home-c/camendol/www/LaserTiming/blue_t_vs_T/summary_614.png", bbox_inches='tight')
        input()


### summary history plot: time, temperature, APD_PN
if False: 
    fig, axs = plt.subplots(3, sharex=True, gridspec_kw={'hspace': 0})
    axs[0].plot(histories["time"], marker=".", linestyle = "--")
    axs[0].set_ylabel("$\Delta (t_{xtal} - t_{MATACQ})$ [ns]")
    axs[1].plot(histories["temperature"], marker=".", linestyle = "--")
    axs[1].set_ylabel("T [$^\circ$ C]")
    
    axs[2].plot(histories["APD_PN"], marker=".", linestyle = "--")
    axs[2].set_ylabel("Relative APD/PN")
    axs[2].set_xlabel("date")
    axs[0].text(right, top, runlabel,
                horizontalalignment='right',
                verticalalignment='bottom',
                transform=axs[0].transAxes)
    axs[0].text(left, top, "FED: "+str(args.fed)+", ch: "+str(args.ch),
                horizontalalignment='left',
                verticalalignment='bottom',
                transform=axs[0].transAxes)
    
    for ax in axs:
        ax.label_outer()
    plt.xticks(rotation=45)
    fig.tight_layout()
    
    if args.show:
        fig.show()
        #fig.savefig("/eos/home-c/camendol/www/LaserTiming/blue_t_vs_T/summary_longrun_corr.pdf", bbox_inches='tight')
        #fig.savefig("/eos/home-c/camendol/www/LaserTiming/blue_t_vs_T/summary_longrun_corr.png", bbox_inches='tight')
        input()
        
### 2D plot - time
if False: 
    fig, ax = plt.subplots()
    sc = ax.scatter(histories["temperature"], histories["time"], marker = ".", s = 50, c =  histories["TCDS"], label = "$\Delta (t_{xtal} - t_{MATACQ})$")
    #sc = ax.scatter(histories["temperature"], histories["rawtime"], marker = ".", s = 50, c =  histories["TCDS"], label = "$\Delta (t_{xtal})$")
    #sc = ax.scatter(histories["temperature"], histories["tmatacq"], marker = ".", s = 50, c =  histories["TCDS"], label = "$\Delta (t_{MATACQ})$")
    ax.set_xlabel("T [$^\circ$ C]")
    ax.set_ylabel("$\Delta t$ [ns]")
    cb = plt.colorbar(sc)
    cb.set_label('TCDS [MHz]')

    ax.text(right, top, runlabel,
            horizontalalignment='right',
            verticalalignment='bottom',
            transform=ax.transAxes)
    ax.text(left, top, "FED: "+str(args.fed)+", ch: "+str(args.ch),
            horizontalalignment='left',
            verticalalignment='bottom',
            transform=ax.transAxes)
    plt.legend()
    if args.show:
        #fig.savefig("/eos/home-c/camendol/www/LaserTiming/blue_t_vs_T/fit_FED%d_ieta%d_314050-327764.pdf"%(args.fed, statistics.mean([args.ietamin, args.ietamax])), bbox_inches='tight')
        #fig.savefig("/eos/home-c/camendol/www/LaserTiming/blue_t_vs_T/fit_FED%d_ieta%d_314050-327764.png"%(args.fed, statistics.mean([args.ietamin, args.ietamax])), bbox_inches='tight')
        
        #fig.savefig("/eos/home-c/camendol/www/LaserTiming/blue_t_vs_T/fit_FED%d_ch%d_314050-327764.pdf"%(args.fed, args.ch), bbox_inches='tight')
        #fig.savefig("/eos/home-c/camendol/www/LaserTiming/blue_t_vs_T/fit_FED%d_ch%d_314050-327764.png"%(args.fed, args.ch), bbox_inches='tight')
        fig.show()
        input()


### 2D plot - time
if False:
    fig, ax = plt.subplots()
    #sc = ax.scatter(histories["temperature"], histories["time"], marker = ".", s = 50, c =  histories["TCDS"], label = "$\Delta (t_{xtal} - t_{MATACQ})$")
    #sc = ax.scatter(histories["temperature"], histories["rawtime"], marker = ".", s = 50, c =  histories["TCDS"], label = "$\Delta (t_{xtal})$")
    sc = ax.scatter(histories["temperature"], histories["tmatacq"], marker = ".", s = 50, c =  histories["TCDS"], label = "$\Delta (t_{MATACQ})$")
    ax.set_xlabel("T [$^\circ$ C]")
    ax.set_ylabel("$\Delta t$ [ns]")
    cb = plt.colorbar(sc)
    cb.set_label('TCDS [MHz]')
    
    ax.text(right, top, runlabel,
            horizontalalignment='right',
            verticalalignment='bottom',
            transform=ax.transAxes)
    ax.text(left, top, "FED: "+str(args.fed)+", ch: "+str(args.ch),
            horizontalalignment='left',
            verticalalignment='bottom',
            transform=ax.transAxes)
    plt.legend()
    if args.show:
        #fig.savefig("/eos/home-c/camendol/www/LaserTiming/blue_t_vs_T/fit_FED%d_ieta%d_314050-327764.pdf"%(args.fed, statistics.mean([args.ietamin, args.ietamax])), bbox_inches='tight')
        #fig.savefig("/eos/home-c/camendol/www/LaserTiming/blue_t_vs_T/fit_FED%d_ieta%d_314050-327764.png"%(args.fed, statistics.mean([args.ietamin, args.ietamax])), bbox_inches='tight')
        
        #fig.savefig("/eos/home-c/camendol/www/LaserTiming/blue_t_vs_T/fit_FED%d_ch%d_314050-327764.pdf"%(args.fed, args.ch), bbox_inches='tight')
        #fig.savefig("/eos/home-c/camendol/www/LaserTiming/blue_t_vs_T/fit_FED%d_ch%d_314050-327764.png"%(args.fed, args.ch), bbox_inches='tight')
        fig.show()
    

### 2D plot and fits: time vs. temperature
if False: 
    histories["temperature"] = histories["temperature"]-22.025
    histories["time"] = histories["time"] - histories[histories["temperature"].abs() < 0.5]["time"].mean()
    
    fig, ax = plt.subplots()
    sc = ax.scatter(histories["temperature"], histories["time"], marker = ".", s = 50, c =  histories["TCDS"])
    ax.set_xlabel("T [$^\circ$ C]")
    ax.set_ylabel("$\Delta (t_{xtal} - t_{MATACQ})$ [ns]")
    cb = plt.colorbar(sc)
    cb.set_label('TCDS [MHz]')
    
    ax.text(right, top, runlabel,
            horizontalalignment='right',
            verticalalignment='bottom',
            transform=ax.transAxes)
    ax.text(left, top, "FED: "+str(args.fed)+", ch: "+str(args.ch),
            horizontalalignment='left',
            verticalalignment='bottom',
            transform=ax.transAxes)
    

    ranges = [40.0784, 40.0785, 40.0789, 40.07897, 40.0790, 40.07915, 40.0793] #TCDS ranges
    slope = []
    u_slope = []
    intercept = []
    u_intercept = []
    TCDS = []
    i = 1
    for grname, gr in histories.groupby(pd.cut(histories.TCDS, ranges)):
        m = 0
        b = 0
        u_m = 0
        u_b = 0
        f = np.nan
        if not gr.empty:
            gr = gr.dropna()
            f = gr["TCDS"].mean()    
            fit,cov=curve_fit(linear_fit,gr["temperature"],gr["time"])
            b = fit[0]
            m = fit[1]
            u_b = sqrt(cov[0][0])
            u_m = sqrt(cov[1][1])
            
            if b > 0: 
                flabel ="%.2f $\cdot$T +%.2f" % (m, b)
            else:
                flabel ="%.2f $\cdot$T %.2f" % (m, b)
            plt.plot(gr["temperature"], m*gr["temperature"] + b, color = sc.to_rgba(f), label = flabel)

        slope.append(m)
        intercept.append(b)
        u_slope.append(u_m)
        u_intercept.append(u_b)
        TCDS.append(f)
        i += 1
    #write_csv.save_fit(args.fed, args.ch, args.ietamin, args.ietamax, args.side,  slope,u_slope, intercept, u_intercept, [0.,0.,0.,0.,0.,0.], TCDS, suffix= "split")

    plt.legend()

    if args.show:
        #fig.savefig("/eos/home-c/camendol/www/LaserTiming/blue_t_vs_T/fit_FED%d_ieta%d_314050-327764.pdf"%(args.fed, statistics.mean([args.ietamin, args.ietamax])), bbox_inches='tight')
        #fig.savefig("/eos/home-c/camendol/www/LaserTiming/blue_t_vs_T/fit_FED%d_ieta%d_314050-327764.png"%(args.fed, statistics.mean([args.ietamin, args.ietamax])), bbox_inches='tight')
        
        #fig.savefig("/eos/home-c/camendol/www/LaserTiming/blue_t_vs_T/fit_FED%d_ch%d_314050-327764.pdf"%(args.fed, args.ch), bbox_inches='tight')
        #fig.savefig("/eos/home-c/camendol/www/LaserTiming/blue_t_vs_T/fit_FED%d_ch%d_314050-327764.png"%(args.fed, args.ch), bbox_inches='tight')
        fig.show()
        
    
### history plot: time, APD_PN
if False: 
    fig, axs = plt.subplots(2, sharex=True, gridspec_kw={'hspace': 0})
    axs[0].plot(histories["time"], marker=".", linestyle = "--")
    axs[0].set_ylabel("$\Delta (t_{xtal} - t_{MATACQ})$ [ns]")
    axs[1].plot(histories["APD_PN"], marker=".", linestyle = "--")
    axs[1].set_ylabel("Relative APD/PN")
    axs[1].set_xlabel("date")
    axs[0].text(right, top, runlabel,
                horizontalalignment='right',
                verticalalignment='bottom',
                transform=axs[0].transAxes)
    axs[0].text(left, top, "FED: "+str(args.fed)+", ch: "+str(args.ch),
                horizontalalignment='left',
                verticalalignment='bottom',
                transform=axs[0].transAxes)
    
    for ax in axs:
        ax.label_outer()
        
    plt.xticks(rotation=45)
    fig.tight_layout()
    if args.show:
        fig.show()
        input()
#
#### 2D plot: time vs. APD_PN
if False: 
    fig, ax = plt.subplots()
    sc = ax.scatter(histories["APD_PN"], histories["time"], marker=".", s=50, c =  histories["TCDS"])
    plt.colorbar(sc)
    ax.set_xlabel("Relative APD/PN")
    ax.set_ylabel("$\Delta (t_{xtal} - t_{MATACQ})$ [ns]")
    ax.text(right, top, runlabel,
            horizontalalignment='right',
            verticalalignment='bottom',
            transform=ax.transAxes)
    ax.text(left, top, "FED: "+str(args.fed)+", ch: "+str(args.ch),
            horizontalalignment='left',
            verticalalignment='bottom',
            transform=ax.transAxes)
    
    if args.show:
        fig.show()
        input()
#
#
#
#
##### 2D plot: time raw vs. tmatacq
if False: 
    fig, ax = plt.subplots()
    sc = ax.scatter(histories["rawtime"], histories["tmatacq"], marker=".", s=50, c =  histories["TCDS"])
    cb = plt.colorbar(sc)
    cb.set_label('TCDS [MHz]')
    ax.set_xlabel("$\Delta (t_{xtal})$ [ns]")
    ax.set_ylabel("$\Delta (t_{MATACQ})$ [ns]")
    ax.text(right, top, runlabel,
            horizontalalignment='right',
            verticalalignment='bottom',
            transform=ax.transAxes)
    ax.text(left, top, "FED: "+str(args.fed)+", ch: "+str(args.ch),
            horizontalalignment='left',
            verticalalignment='bottom',
            transform=ax.transAxes)
    
    if args.show:
        #fig.savefig("/eos/home-c/camendol/www/LaserTiming/blue_t_vs_T/zTCDS_FED%d_ch%d_314050-327764.pdf"%(args.fed, args.ch), bbox_inches='tight')
        #fig.savefig("/eos/home-c/camendol/www/LaserTiming/blue_t_vs_T/zTCDS_FED%d_ch%d_314050-327764.png"%(args.fed, args.ch), bbox_inches='tight')
        fig.show()
        #input()

#### 2D plot: time raw vs. tmatacq
if False: 
    fig, ax = plt.subplots()
    sc = ax.scatter(histories["rawtime"], histories["tmatacq"], marker=".", s=50, c =  histories["temperature"])
    cb = plt.colorbar(sc)
    cb.set_label("T [$^\circ$C]")
    ax.set_xlabel("$\Delta (t_{xtal})$ [ns]")
    ax.set_ylabel("$\Delta (t_{MATACQ})$ [ns]")
    ax.text(right, top, runlabel,
            horizontalalignment='right',
            verticalalignment='bottom',
            transform=ax.transAxes)
    ax.text(left, top, "FED: "+str(args.fed)+", ch: "+str(args.ch),
            horizontalalignment='left',
            verticalalignment='bottom',
            transform=ax.transAxes)
    if args.show:
        fig.show()
        #fig.savefig("/eos/home-c/camendol/www/LaserTiming/blue_t_vs_T/ztemp_FED%d_ch%d_314050-327764.pdf"%(args.fed, args.ch), bbox_inches='tight')
        #fig.savefig("/eos/home-c/camendol/www/LaserTiming/blue_t_vs_T/ztemp_FED%d_ch%d_314050-327764.png"%(args.fed, args.ch), bbox_inches='tight')
        input()
