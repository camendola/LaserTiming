import pandas as pd
import os.path
import numpy as np

import sys
sys.path.append('../')
from elmonk.dst import DstReader ### to read the DST files into pandas
import uproot
import matplotlib.pyplot as plt
from tqdm import tqdm

def load_run_ch(df_dstFiles, run, ch, year, green = False): 
    s_name = 'fname'
    s_fed = 'FED'
    if year == 2016: 
        s_name = 'file'
        s_fed = 'fed'
    df_dstFiles = df_dstFiles[df_dstFiles['run'] == run]
    if green: 
        df_dstFiles_g = df_dstFiles.copy()
        df_dstFiles_g[s_name]=df_dstFiles[s_name].str.replace('.447.','.527.')
        these_dstFile = df_dstFiles_g[df_dstFiles_g[s_name].map(os.path.isfile)][s_name] 
    else: 
        these_dstFile = df_dstFiles[s_name]

    these_fed = df_dstFiles[s_fed] 
    df_these_fed = pd.DataFrame({'index':these_fed.index, s_fed:these_fed.values})
    df_chunk_xtal =[]
    with tqdm(total=len(these_dstFile), unit='entries') as pbar:
        for i, block in enumerate(these_dstFile):
            dR = DstReader(block)
            # columns definition in https://twiki.cern.ch/twiki/bin/viewauth/CMS/ECalLaserDSTfile
            xtal = dR.readXtals(columns=[1, 4], names=['xtalID','tMax'], dropna=[])
            db = xtal[xtal['xtalID'] == ch]
            info = pd.read_csv(block, header=None,sep = ' ', nrows = 1, usecols = [3], names=['time'])
            db.index = pd.RangeIndex(len(db.index))      
            db.loc[db.index,'time'] = pd.to_datetime(info['time'], unit='s', errors='ignore') 
            
            
            
            df_chunk_xtal.append(db)
            pbar.update(1)

    
    df_xtal = pd.concat(df_chunk_xtal, axis = 0)
    df_xtal.index = pd.RangeIndex(len(df_xtal.index))
    df_xtal['FED'] = df_these_fed[s_fed]
    df_xtal['elapsed_time'] = (df_xtal.time -  df_xtal.time[0])
    print(df_xtal.head())
    return df_xtal



def load_files(year):
    prod_disk     = "/eos/cms/store/group/dpg_ecal/alca_ecalcalib/laser/dst.hdf/"
    inputDir  = ('%s/%d/' % (prod_disk,year))
    list_dstFiles   = inputDir + ('dstFiles_db.%d.csv'% year) # panda df containing the DST files path
    df_dstFiles = pd.read_csv(list_dstFiles) 
    return df_dstFiles


def plot_t_fed_gb(df_xtalG, df_xtalB, year, run, ch):
    fig, axs = plt.subplots(2,1,figsize=(15,10))
    fig.subplots_adjust(wspace = 0.3, hspace= 0.4)
    df_xtalB.plot(y = 'tMax', x='time', marker='o', linestyle = "", ax = axs[0], title = str(year) + ", " + str(run) + ", " + str(ch) )
    df_xtalG.plot(y = 'tMax', x='time', marker='o', linestyle = "",  ax = axs[0], color = 'green',title = str(year) + ", " + str(run) + ", " + str(ch)  )
    
    df_xtalB.plot(y = 'FED', x='time', marker='o',  linestyle = "", ax = axs[1], title = str(year) + ", " + str(run) + ", " + str(ch) )
    df_xtalG.plot(y = 'FED', x='time', marker='o',  linestyle = "", ax = axs[1], color = 'green',title = str(year) + ", " + str(run) + ", " + str(ch) )

    return fig



year = 2017
run = 274199
ch = 1

df_dstFiles_2017 = load_files(year)
df_xtalG_2017 = load_run_ch(df_dstFiles_2017,run, ch , year, green = True)
df_xtalB_2017 = load_run_ch(df_dstFiles_2017,run, ch , year)

fig = plot_t_fed_gb(df_xtalG_2017, df_xtalB_2017, year, run, ch)
fig.show()

input()
