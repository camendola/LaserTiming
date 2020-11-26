import pandas as pd
import os.path
import numpy as np

import sys
sys.path.append('../')
from elmonk.dst import DstReader ### to read the DST files into pandas
import matplotlib.pyplot as plt


import argparse
import modules.load as load
import glob

parser = argparse.ArgumentParser(description='Command line parser of plotting options')

parser.add_argument('--year', dest='year',type=int, help='which year', default=2018)
parser.add_argument('--fed',  dest='fed', type=int, help='which fed', default=610)
parser.add_argument('--green',  dest='green', help='green',action='store_true', default = False)


args = parser.parse_args()


year = args.year

#dst_filelist = load.load_files(year, args.green)
root_dir = "/eos/cms/store/group/dpg_ecal/alca_ecalcalib/laser/dst.merged/2018/"

dst_filelist = []
for filename in glob.iglob(root_dir + '**/*.corlinpn', recursive=True):
     if not args.green:
          if "447" in filename: dst_filelist.append(filename)
     else:
          if "527" in filename: dst_filelist.append(filename)

runlist = []

#runlist = histories.reset_index().run.drop_duplicates().sort_values().tolist()
matacq= load.load_matacq(dst_filelist, year, fed = args.fed, runlist = runlist)



print(matacq)
