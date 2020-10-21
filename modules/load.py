import pandas as pd
import os.path
import numpy as np
import uproot

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



def load_files(year):
    prod_disk     = "/eos/cms/store/group/dpg_ecal/alca_ecalcalib/laser/dst.hdf/"
    inputDir  = ('%s/%d/' % (prod_disk,year))
    list_dstFiles   = inputDir + ('dstFiles_db.%d.csv'% year) # panda df containing the DST files path
    df_dstFiles = pd.read_csv(list_dstFiles)
    if year == 2018: df_dstFiles["fname"] = df_dstFiles["fname"].str.replace("/cmsecallaser/srv-ecal-laser-10/disk0/persistent/Corrections/Beam18/oneShot/Fabrice/pn2018/overwrite_dst/", "/eos/cms/store/group/dpg_ecal/alca_ecalcalib/laser/dst.merged/2018/") 
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


def load_dst_firstline(dst_name, isGreen, ch = -1):
    info = pd.read_csv(dst_name, header=None,sep = ' ', nrows = 1, usecols = [0, 3, 10, 13, 14], names=['run','time','bfield','temperature','TCDS'])
    info['time'] = pd.to_datetime(info['time'], unit='s')
    return info


def load_ch_firstline(df_dstFiles, ch, year, green = False, run = -1, fed = -1): 
    filename = "/afs/cern.ch/work/c/camendol/LaserData/"+str(year)+"/firstline_"+str(year)+"_"+str(fed)+"_"+str(ch)+".hdf"
    #print(filename)
    if not os.path.isfile(filename): 
        s_name = 'fname'
        s_fed = 'FED'
        if year == 2016: 
            s_name = 'file'
            s_fed = 'fed'
        
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
        df_chunk_info = []

        with tqdm(total=len(these_dstFiles), unit='entries') as pbar:
            for i, block in enumerate(these_dstFiles):
                db = load_dst_firstline(block, green, ch)
                df_chunk_info.append(db)
                pbar.update(1)

        df_info = pd.concat(df_chunk_info, axis = 0)
        df_info.index = pd.RangeIndex(len(df_these_fed.index))
        df_info['FED'] = df_these_fed[s_fed]
        df_info.to_hdf(filename, key="firstline", mode = "w")        
    else: 
        df_info = pd.read_hdf(filename, key="firstline", mode = "r")

    return df_info
