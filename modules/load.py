import pandas as pd
import os.path
import numpy as np
import uproot
import glob

from pathlib import Path

import sys
sys.path.append('../')
from elmonk.dst import DstReader ### to read the DST files into pandas

from tqdm import tqdm


def load_ch(df_dstFiles, ch, year, green = False, run = -1, fed = -1): 
    s_name = 'fname'
    s_fed = 'FED'
    if year == 2016: 
        s_name = 'file'
        s_fed = 'fed'
    print( df_dstFiles)
    if (run > -1): df_dstFiles = df_dstFiles[df_dstFiles['run'] == run]
    if (fed > -1): df_dstFiles = df_dstFiles[df_dstFiles[s_fed] == fed]

    if green: 
        these_dstFiles = df_dstFiles[s_name].str.replace('.447.','.527.')
        these_dstFiles = these_dstFiles[these_dstFiles.map(os.path.isfile)]

    else: 
        these_dstFiles = df_dstFiles[df_dstFiles[s_name].map(os.path.isfile)][s_name]

    these_dstFiles = these_dstFiles[(these_dstFiles.map(os.path.getsize) > 0.)]

    these_fed = df_dstFiles[s_fed] 
    df_these_fed = pd.DataFrame({'index':these_fed.index, s_fed:these_fed.values})
    df_chunk_xtal =[]
    with tqdm(total=len(these_dstFiles), unit='entries') as pbar:
        for i, block in enumerate(these_dstFiles):
            db = load_dst(block, green, ch)
            df_chunk_xtal.append(db)
            pbar.update(1)

    
    df_xtal = pd.concat(df_chunk_xtal, axis = 0)
    df_xtal.index = pd.RangeIndex(len(df_xtal.index))
    df_xtal['FED'] = df_these_fed[s_fed]


    return df_xtal



def load_files(year, green):
    basedir = Path(f'/eos/cms/store/group/dpg_ecal/alca_ecalcalib/laser/dst.hdf')
    if year == 2018: fullpath = f'{year}/dstFiles.{year}.w447.csv' if not green else f'{year}/dstFiles.{year}.w527.csv'
    print (basedir / fullpath)
    df_dstFiles = pd.read_csv(basedir / fullpath)

    return df_dstFiles


def load_dst(dst_name, isGreen, ch = -1):
    print(dst_name)
    dR = DstReader(dst_name)

    # columns definition in https://twiki.cern.ch/twiki/bin/viewauth/CMS/ECalLaserDSTfile
    db = dR.readXtals(columns=[1, 4, 9,  27], names=['xtalID','tMax', 'APD_PN', 'tStart'], dtype = {'APD_PN':'float32', 'tMax':'float32', 'tStart':'float32'})
    if ch > -1: db = db[(db['xtalID'] == ch)]
    info = pd.read_csv(dst_name, header=None,sep = ' ', nrows = 1, usecols = [3, 13, 14], names=['time', 'temperature','TCDS'])
    db.index = pd.RangeIndex(len(db.index))      
    db[['temperature','TCDS']] = info[['temperature','TCDS']].copy()
    db['time'] = pd.to_datetime(info['time'], unit='s').copy() 
    matacq = dR.readMatacq()
    # Timing of the pulse APD wrt laser 
    # blue:
    # (col_4)*25 - laser_tstart = <t_apd> - <t_laser>
    # green:
    # (col_n)*25            = <t_apd-t_laser>
    # (in ns) 

    if not isGreen: 
        if len(matacq['tstart']) > 1: # why do I need these protections?
            db["time_wrtLaser"] = (db["tMax"]*25  - matacq['tstart'][0] + 1385)
        elif len(matacq['tstart']) == 1: 
            db["time_wrtLaser"] = (db["tMax"]*25  - matacq['tstart'] + 1385)
        else: 
            db["time_wrtLaser"] = np.nan
    if isGreen: db["time_wrtLaser"] = (db["tStart"]*25)
    
    return db


def load_dst_firstline(dst_name, isGreen):
    info = pd.read_csv(dst_name, header=None,sep = ' ', nrows = 1, usecols = [0, 3, 10, 13, 14], names=['run','time','bfield','temperature','TCDS'],  engine='python')
    info['time'] = pd.to_datetime(info['time'], unit='s')
    info['seq']  = int(os.path.basename(dst_name).split('.')[1])
    return info


def load_firstline(df_dstFiles, year, green = False, run = -1, fed = -1, runlist = []): 
    if not green: 
        filename = "/afs/cern.ch/work/c/camendol/LaserData/"+str(year)+"/firstline_"+str(year)+"_"+str(fed)+".hdf"
    else: 
        filename = "/afs/cern.ch/work/c/camendol/LaserData/"+str(year)+"/firstline_"+str(year)+"_"+str(fed)+"_green.hdf"
    if not os.path.isfile(filename): 
        if (fed > -1): df_dstFiles = [f for f in df_dstFiles if "/"+str(fed)+"/" in f]
                
        df_dstFiles = [f for f in df_dstFiles if os.path.getsize(f) > 0.]
        
        #s_name = 'fname'
        #s_fed = 'FED'
        #if year == 2016: 
        #    s_name = 'file'
        #    s_fed = 'fed'
        #
        #if (run > -1): df_dstFiles = df_dstFiles[df_dstFiles['run'] == run]
        #if (fed > -1): df_dstFiles = df_dstFiles[df_dstFiles[s_fed] == fed]
        #
        #
        #df_dstFiles = df_dstFiles[(df_dstFiles[s_name].map(os.path.isfile))]
        #df_dstFiles = df_dstFiles[(df_dstFiles[s_name].map(os.path.getsize) > 0.)]
                                
        print(df_dstFiles.shape)
        df_chunk_info = []
        print("Writing to " + filename)
        #with tqdm(total=len(df_dstFiles[s_name]), unit='entries') as pbar:
        with tqdm(total=len(df_dstFiles), unit='entries') as pbar:
            #for i, block in enumerate(df_dstFiles[s_name]):
            for i, block in enumerate(df_dstFiles):
                db = load_dst_firstline(block, green)
                df_chunk_info.append(db)
                pbar.update(1)
                
        df_info = pd.concat(df_chunk_info, axis = 0)
        df_info.index = pd.RangeIndex(len(df_info.index))
        print (df_info.shape)
        df_info['FED'] = df_dstFiles[s_fed]
        df_info.to_hdf(filename, key="firstline", mode = "w")        
    else: 
        df_info = pd.read_hdf(filename, key="firstline", mode = "r")
    print(df_info)

    if len(runlist) > 0: 
        if len(runlist) == 2:
            df_info = df_info[(df_info["run"] <= runlist[-1]) & (df_info["run"] >= runlist[0]) ]
        else:
            df_info = df_info[df_info["run"].isin(runlist)]
        return df_info
            

def load_dst_matacq(dst_name):
    dR = DstReader(dst_name)
    # columns definition in https://twiki.cern.ch/twiki/bin/viewauth/CMS/ECalLaserDSTfile
    matacq = dR.readMatacq(columns = [x for x in range (0,13) if not x == 5], names = ['Amplitude', 'riseTime', 'width50', 'width10', 'width5', 'integral', 'integral100', 'integral250', 'integral500', 'integral750', 'tmax', 'tstart'])

    return matacq


def load_matacq(df_dstFiles, year, green = False, run = -1, fed = -1, runlist = []): 
    filename = "/afs/cern.ch/work/c/camendol/LaserData/"+str(year)+"/matacq_"+str(year)+"_"+str(fed)+".hdf"
    if green: filename = "/afs/cern.ch/work/c/camendol/LaserData/"+str(year)+"/matacq_"+str(year)+"_"+str(fed)+"_green.hdf"
    if not os.path.isfile(filename): 
        
        if (fed > -1): df_dstFiles = [f for f in df_dstFiles if "/"+str(fed)+"/" in f]

        df_dstFiles = [f for f in df_dstFiles if os.path.getsize(f) > 0.]
                                
        df_chunk = []
        print("Writing to " + filename)
        with tqdm(total=len(df_dstFiles), unit='entries') as pbar:
            for i, block in enumerate(df_dstFiles):
                db = load_dst_matacq(block)
                df_chunk.append(db)
                pbar.update(1)
                
        df = pd.concat(df_chunk, axis = 0)
        df.index = pd.RangeIndex(len(df.index))
    
        df['FED'] = fed
        df.to_hdf(filename, key="matacq", mode = "w")        
    else: 
        df = pd.read_hdf(filename, key="matacq", mode = "r")


    if len(runlist) > 0: 
        if len(runlist) == 2:
            df = df[(df["run"] <= runlist[-1]) & (df["run"] >= runlist[0])]        
        else:
            df = df[df["run"].isin(runlist)]
    return df
