import pandas as pd

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

#from elmonk.common.helper import scalar_to_list, make_index
import modules.load as load                   # methods for dst files 

import argparse

parser = argparse.ArgumentParser(description='Command line parser of plotting options')

parser.add_argument('--fed',     dest='fed',type=int, help='fed', default=None)
parser.add_argument('--ch',      dest='ch',type=int, help='ch', default=-1)
parser.add_argument('--side',      dest='side',type=int, help='side', default=-1)
parser.add_argument('--rmin',    dest='rmin',type=int, help='rmin', default=-1)
parser.add_argument('--rmax',    dest='rmax',type=int, help='rmax', default=-1)
parser.add_argument('--dump',    dest='dump',   help='dump tables', default=False,  action ='store_true')
parser.add_argument('--show',    dest='show',   help='show plots', default=False,  action ='store_true')

args = parser.parse_args()

def load_df(name, FED, side):
    df = pd.read_hdf((basedir / f'{year}/dstUL_db.{year}.hdf5'), name)
    if side > -1: df = df[(df["side"] == side)].drop(columns = ["side"])
    if FED: 
        df = df[(df["FED"] == FED)].drop(columns = ["FED"])
        df = df.reset_index().set_index(["run","seq"])
    else: 
        df = df.reset_index().set_index(["run","seq", "FED"])
    if "index" in list(df.columns): df = df.drop(columns = ["index"])
    return df

year = 2018
basedir = Path(f'/eos/cms/store/group/dpg_ecal/alca_ecalcalib/laser/dst.hdf')
FED = args.fed

tables = []
tables_names = ['Matacq', 'Spybox']


for name in tables_names:
    df = load_df(name, FED, args.side)
    tables.append(df)

df = pd.concat(tables, axis = 1, keys = dict(zip(tables_names, tables))).reset_index().set_index(["run","seq"])
tables = []
# get temperature 
sequence = pd.read_hdf((basedir / f'{year}/dstUL_db.{year}.hdf5'), 'sequence')[["fill", "temperature", "bfield", "run", "seq"]]
sequence = sequence.reset_index().set_index(["run","seq"]).drop(columns=["index"])

for name in sequence.columns: 
    df["sequence", name] = df.index.map(sequence[name])

#get TCDS - not in hdf: map directly from dst files 
dst_filelist = load.load_files(year)
runlist = df.reset_index().run.drop_duplicates().sort_values().tolist()
df_firstline = load.load_firstline(dst_filelist, year, fed = args.fed, runlist = runlist)

if year == 2018:
    #clean bunch of runs with bugged temperature
    df = df.reset_index()
    df = df[(df["run"] < 314344) | (df["run"] > 314350)]
    df = df.reset_index().set_index(["run", "seq"]).drop(columns=["index"])

df["","TCDS"] = df.index.map(df_firstline.reset_index().set_index(["run", "seq"]).TCDS)/1000000. # LHC freq [MHz]

df["date"] = pd.to_datetime(df.index.map(df_firstline.reset_index().set_index(["run", "seq"]).time))

df = df.reset_index().set_index(["date"])
df = df.reset_index().set_index(["date", "run", "seq"])
print (df)
