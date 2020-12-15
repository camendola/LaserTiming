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

parser.add_argument('--year',  dest='year',  type=int,     help='which year',   default=2018)
parser.add_argument('--fed',   dest='fed',   type=int,     help='which fed',    default=610)
parser.add_argument('--green', dest='green', help='green', action='store_true', default = False)

args = parser.parse_args()

year = args.year

dst_filelist = load.load_files(year, args.green)

runlist = [313800, 314750]

#runlist = histories.reset_index().run.drop_duplicates().sort_values().tolist()
matacq= load.load_matacq(dst_filelist, year, fed = args.fed, runlist = runlist)
matacq = matacq.reset_index().set_index(["run", "seq"])
side = 1
matacq = matacq[matacq["side"] == side]

firstline = load.load_firstline(dst_filelist, year, fed = args.fed, runlist = runlist)
firstline = firstline.reset_index().set_index(["run", "seq"])



matacq["time"] = matacq.index.map(firstline.time)
matacq["temperature"] = matacq.index.map(firstline.temperature)
matacq["TCDS"] = matacq.index.map(firstline.TCDS)/1000000.

print(matacq)
ranges = [40.0784, 40.0785, 40.0789, 40.07897, 40.0790, 40.07915, 40.0793] #TCDS ranges

var = ['Amplitude', 'riseTime', 'width50', 'width10', 'width5', 'integral', 'integral100', 'integral250', 'integral500', 'i\
ntegral750', 'tmax', 'tstart']

matacq = matacq.reset_index().set_index("time")

for v in var:
     fig, ax = plt.subplots(figsize= (10, 5))
     for grname, gr in matacq.groupby(pd.cut(matacq.TCDS, ranges)):
          print (gr)
          if not gr.empty:
               print (gr)
               print (gr["TCDS"].mean())
               print ("T < 21.5")
               gr_low  = gr[gr["temperature"] < 21.5][v]
               z_scores_low = stats.zscore(gr_low)
               abs_z_scores_low = np.abs(z_scores_low)
               filtered_entries_low = (abs_z_scores_low < 3)

               gr_low = gr_low[filtered_entries_low]

               print ("T > 22")
               gr_high = gr[gr["temperature"] > 22][v]
               z_scores_high = stats.zscore(gr_high)
               abs_z_scores_high = np.abs(z_scores_high)
               filtered_entries_high = (abs_z_scores_high < 3)
               gr_high = gr_high[filtered_entries_high]

               ax.plot(gr_low.index, gr_low  , marker=".", markersize = 1, linestyle = "--", label = "T < 21.5 $^\cdot$C, TCDS = %f MHz" % gr["TCDS"].mean())
               ax.plot(gr_high.index, gr_high, marker=".", markersize = 1, linestyle = "-", label = "T > 22 $^\cdot$C, TCDS = %f MHz" % gr["TCDS"].mean())

     ax.set(xlabel = 'date', ylabel = v)
     directory = "matacq"
     subfolder = ""
     FED = args.fed
     if not os.path.exists("/eos/home-c/camendol/www/LaserTiming/"+directory+"/"+subfolder+str(FED)):
          os.makedirs("/eos/home-c/camendol/www/LaserTiming/"+directory+"/"+subfolder+str(FED))
          shutil.copy("/eos/home-c/camendol/www/index.php","/eos/home-c/camendol/www/LaserTiming/"+directory+"/"+subfolder)
          shutil.copy("/eos/home-c/camendol/www/index.php","/eos/home-c/camendol/www/LaserTiming/"+directory+"/"+subfolder+str(FED))
               
     plt.legend()
     fig.savefig("/eos/home-c/camendol/www/LaserTiming/"+directory+"/"+subfolder+str(FED)+"/"+str(v)+".pdf",bbox_inches='tight')
     fig.savefig("/eos/home-c/camendol/www/LaserTiming/"+directory+"/"+subfolder+str(FED)+"/"+str(v)+".png",bbox_inches='tight')





