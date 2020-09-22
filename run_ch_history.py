import pandas as pd
import os.path
import numpy as np

import sys
sys.path.append('../')
from elmonk.dst import DstReader ### to read the DST files into pandas
import matplotlib.pyplot as plt


import argparse
import modules.load as load


parser = argparse.ArgumentParser(description='Command line parser of plotting options')

parser.add_argument('--year', dest='year',type=int, help='which year', default=2017)
parser.add_argument('--run', dest='run',type=int, help='which run number', default=274199)
parser.add_argument('--ch', dest='ch', type=int, help='which channel', default=0)

parser.add_argument('--debug', dest='debug', help='debug', default=False, action ='store_true')

args = parser.parse_args()

def plot_t_fed_gb(df_xtalG, df_xtalB, year, run, ch):
    fig, axs = plt.subplots(2,1,figsize=(15,10))
    fig.subplots_adjust(wspace = 0.3, hspace= 0.4)
    df_xtalB.plot(y = 'tMax', x='time', marker='o', linestyle = "", ax = axs[0], title = str(year) + ", run  " + str(run) + ", ch" + str(ch) )
    df_xtalG.plot(y = 'tMax', x='time', marker='o', linestyle = "",  ax = axs[0], color = 'green',title = str(year) + ", run " + str(run) + ", ch" + str(ch)  )
    
    df_xtalB.plot(y = 'FED', x='time', marker='o',  linestyle = "", ax = axs[1], title = str(year) + ", run " + str(run) + ", ch " + str(ch) )
    df_xtalG.plot(y = 'FED', x='time', marker='o',  linestyle = "", ax = axs[1], color = 'green',title = str(year) + ", run " + str(run) + ", ch " + str(ch) )
    return fig


year = args.year
run = args.run
ch = args.ch

df_dstFiles = load.load_files(year)
df_xtalG = load.load_run_ch(df_dstFiles,run, ch , year, green = True)
df_xtalB = load.load_run_ch(df_dstFiles,run, ch , year)

fig = plot_t_fed_gb(df_xtalG, df_xtalB, year, run, ch)
fig.show()
input()
