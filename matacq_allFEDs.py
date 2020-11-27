import pandas as pd
import os.path
import numpy as np

import sys
sys.path.append('../')
from elmonk.dst import DstReader ### to read the DST files into pandas
import matplotlib.pyplot as plt

import shutil
import argparse
import modules.load as load
import glob

import scipy.stats as stats

parser = argparse.ArgumentParser(description='Command line parser of plotting options')

parser.add_argument('--year', dest='year',type=int, help='which year', default=2018)
parser.add_argument('--var', dest='var', action='append', help='var', default=[])
parser.add_argument('--green',  dest='green', help='green',action='store_true', default = False)


args = parser.parse_args()


year = args.year

#dst_filelist = load.load_files(year, args.green)

root_dir = "/eos/cms/store/group/dpg_ecal/alca_ecalcalib/laser/dst.merged/2018/"


filelist = ("input/dst_filelist_%d_blue.txt" if not args.green else "input/dst_filelist_%d_green.txt") % year
if os.path.isfile(filelist):
     with open(filelist) as f:
          dst_filelist = f.read().splitlines()
else: 
     dst_filelist = []
     for filename in glob.iglob(root_dir + '**/*.corlinpn', recursive=True):
          if not args.green:
               if "447" in filename: dst_filelist.append(filename)
          else:
               if "527" in filename: dst_filelist.append(filename)
     with open(filelist, 'w') as f:
          for item in dst_filelist:
               f.write("%s\n" % item)


matacq_list = []
firstline_list = []
FEDs = [x for x in range(610, 644) if not x == 625]
runlist = [313800, 314750]


for fed in FEDs:
     #runlist = histories.reset_index().run.drop_duplicates().sort_values().tolist()
     matacq= load.load_matacq(dst_filelist, year, fed = fed, runlist = runlist)
     side = 1
     vars = ["FED", "run", "seq"]
     print(type(args.var))
     vars.extend(args.var)
     print(vars)
     matacq = matacq[matacq["side"] == side][vars]
     matacq = matacq.reset_index().set_index(["run", "seq", "FED"])

     firstline = load.load_firstline(dst_filelist, year, fed = fed, runlist = runlist)
     firstline = firstline.reset_index().set_index(["run", "seq", "FED"])
     
     
     
     matacq["time"] = matacq.index.map(firstline.time)
     matacq["temperature"] = matacq.index.map(firstline.temperature)
     matacq["TCDS"] = matacq.index.map(firstline.TCDS)/1000000.
     
     matacq = matacq.reset_index().set_index("time")
     matacq_list.append(matacq)
     firstline_list.append(firstline)

matacq = pd.concat(matacq_list).sort_index()
del matacq_list, firstline_list

#print(matacq)
ranges = [40.0784, 40.0785, 40.0789, 40.07897, 40.0790, 40.07915, 40.0793] #TCDS ranges
     

d = len(args.var) 

directory = "matacq"
subfolder = ""
if not os.path.exists("/eos/home-c/camendol/www/LaserTiming/"+directory+"/"+subfolder):
     os.makedirs("/eos/home-c/camendol/www/LaserTiming/"+directory+"/"+subfolder)
     shutil.copy("/eos/home-c/camendol/www/index.php","/eos/home-c/camendol/www/LaserTiming/"+directory+"/"+subfolder)
     shutil.copy("/eos/home-c/camendol/www/index.php","/eos/home-c/camendol/www/LaserTiming/"+directory+"/"+subfolder)
          
v = args.var
     
if d == 1: fig, ax = plt.subplots(figsize= (10, 5)) 
for grname, gr in matacq.groupby(pd.cut(matacq.TCDS, ranges)):
     print (gr)
     if d == 2: fig, ax = plt.subplots(figsize= (5, 5))
     if not gr.empty:
          print (gr)
          print (gr["TCDS"].mean())
          print ("T < 21.5")
          gr_low  = gr[gr["temperature"] < 21.5][v]
          z_scores_low = stats.zscore(gr_low)
          abs_z_scores_low = np.abs(z_scores_low)
          filtered_entries_low = (abs_z_scores_low < 3)
          if d == 2: filtered_entries_low = (abs_z_scores_low < 3).all(axis = 1)
          gr_low = gr_low[filtered_entries_low]

          print ("T > 22")
          gr_high = gr[gr["temperature"] > 22][v]
          z_scores_high = stats.zscore(gr_high)
          abs_z_scores_high = np.abs(z_scores_high)
          filtered_entries_high = (abs_z_scores_high < 3)
          if d == 2: filtered_entries_high = (abs_z_scores_high < 3).all(axis = 1)
          gr_high = gr_high[filtered_entries_high]
          
          if d == 1:
               ax.plot(gr_low.index, gr_low  , marker=".", markersize = 1, linestyle = "--", label = "T < 21.5 $^\circ$C, TCDS = %f MHz" % gr["TCDS"].mean())
               ax.plot(gr_high.index, gr_high, marker=".", markersize = 1, linestyle = "-", label = "T > 22 $^\circ$C, TCDS = %f MHz" % gr["TCDS"].mean())

          elif d == 2: 
               ax.scatter(gr_low[args.var[0]], gr_low[args.var[1]]  , marker=".", label = "T < 21.5 $^\circ$C, TCDS = %f MHz" % gr["TCDS"].mean())
               ax.scatter(gr_high[args.var[0]], gr_high[args.var[1]]  , marker="s", label = "T < 21.5 $^\circ$C, TCDS = %f MHz" % gr["TCDS"].mean())
               ax.set(xlabel = args.var[0], ylabel = args.var[1])
               
               plt.legend()
               fig.savefig("/eos/home-c/camendol/www/LaserTiming/"+directory+"/"+subfolder+"/"+str(args.var[0])+"_"+str(args.var[1])+"_"+str(gr["TCDS"].mean())+".pdf",bbox_inches='tight')
               fig.savefig("/eos/home-c/camendol/www/LaserTiming/"+directory+"/"+subfolder+"/"+str(args.var[0])+"_"+str(args.var[1])+"_"+str(gr["TCDS"].mean())+".png",bbox_inches='tight')
               

if d == 1:
     ax.set(xlabel = 'date', ylabel = v)
     
     plt.legend()
     fig.savefig("/eos/home-c/camendol/www/LaserTiming/"+directory+"/"+subfolder+"/"+str(args.var[0])+".pdf",bbox_inches='tight')
     fig.savefig("/eos/home-c/camendol/www/LaserTiming/"+directory+"/"+subfolder+"/"+str(args.var[0])+".png",bbox_inches='tight')





