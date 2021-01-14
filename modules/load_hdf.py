from elmonk.common import HdfLaser

import matplotlib.pyplot as plt
import matplotlib as mpl
import ecalic
import numpy as np
import pandas as pd
import os.path
import sys

def make_path(year, green, UL = True):
        if year == 2018: 
                fullpath = f'{year}/dst.w447.hdf5' if not green else f'{year}/dst.w527.hdf5'        
                if UL: fullpath = f'UL_{year}/dst.w447.hdf5' if not green else f'UL_{year}/dst.w527.hdf5'        
        return fullpath

def load_history(filename, year, write, basedir, FED, property = 'tAPD', green = False):
        if ((not os.path.isfile(filename)) or write):
                fullpath = make_path(year, green)
                print(fullpath)
                data = HdfLaser(basedir / fullpath)
                period = [f'{year}-04-01',f'{year}-12-31']
                
                #apply mask broken channels 2018
                status = ecalic.xml('../elmonk/etc/data/ecalChannelStatus_run324773.xml',type='status').icCMS()
                good_channels = status.iov.mask(status['ic']!=0).dropna(how='all')
                xtals = data.xtal_idx('FED == '+str(FED)).intersection(good_channels.index)

                
                histories = data.xtal_history(iov_idx=data.iov_idx(period),xtal_idx=xtals, xtal_property=property)
                
                run_seq = data.iov_idx_to_run_seq(data.iov_idx(period)['iov_idx'].values)
                histories[["run","seq"]] = np.array(run_seq)
                histories = histories.reset_index().set_index(["date", "run", "seq"])
                print("Writing to "+filename)
                histories.to_hdf(filename, key= "hist", mode = "w")
        else: 
                histories = pd.read_hdf(filename,key = "hist", mode = "r")
                
        return histories


def append_idxs(df, ch = -1, ietamin = -999, ietamax = -999, iphimin = -999, iphimax = -999, side = -1, TT = -1):
        """
        Appends ieta, iphi, side, TT, strip, Xtal, xtal_id.
        The dataframe must be given in the format:
        
        date            2018-07-13 04:27:43 ...
        seq             0                   ...
        run             319579              ...
        xtal_ecalic_id
        0               XX                  ...
        1               YY                  ...
        ...             ...                 ...
        """

        df['ieta']    = df.set_index('xtal_ecalic_id').index.map(ecalic.geom.ix) 
        df['iphi']    = df.set_index('xtal_ecalic_id').index.map(ecalic.geom.iy) 
        df['iphi']    = (df['iphi'] - 1).mod(20) + 1
        df['TT']      = df.set_index('xtal_ecalic_id').index.map(ecalic.geom.ccu)   

        #add sides mask
        side1 = (((df['ieta'] > 0) & (df['ieta'] > 5) & (df['iphi']  > 10)) |  #EB+
                 ((df['ieta'] < 0) & (df['ieta'] < - 5) & (df['iphi'] < 11))) #EB-
        df['side'] = np.where(side1, 1, 0)

        #get xtal_id as defined in dst files 
        df['xtal_id']    = df.set_index('xtal_ecalic_id').index.map(ecalic.geom.elecID) 

        
        if ch > -1:        df = df[(df["xtal_id"] == ch)]        
        if ietamin > -999: df = df[(df["ieta"] >= ietamin)]        
        if ietamax > -999: df = df[(df["ieta"] <= ietamax)]        
        if iphimin > -999: df = df[(df["iphi"] >= iphimin)]        
        if iphimax > -999: df = df[(df["iphi"] <= iphimax)]        
        if side > -1:      df = df[(df["side"] == side)]        
        if TT > -1:        df = df[(df["TT"] == TT)]        
        

        #df = df[df["iphi"] > 10]
        #df = df[((df["iphi"] <=5) | ((10 < df["iphi"]) & (df["iphi"] <=15)))]
        #df = df[(((5 < df["iphi"]) & (df["iphi"] <=10)) | ((15 < df["iphi"]) & (df["iphi"] <=20)))]
        df = df.reset_index().set_index(["ieta", "iphi", "xtal_id", "side","TT"])
        df = df.drop(columns=['xtal_ecalic_id','index'])
        return df


def load_tmatacq(df, year, basedir, FED, rmin, rmax, green = False):
        """
        Concatenates identical df conctaining the tstart of MATACQ - needed for blue laser-
        for each crystal in the original df. 
        
        The dataframe must be given in the format:

        side                                     0    1   ...
        date                 run        seq 
        2018-07-13 04:27:43  319579     0        XX   YY  ...
        ...                  ...        ...      ...  ... ...
        """
        fullpath = make_path(year, green)
        print (fullpath)
        matacq = pd.read_hdf((basedir / fullpath), 'Matacq')

        matacq = matacq[(matacq["FED"] == FED)]

        if rmin > -1 or rmax > -1:
                matacq = matacq.reset_index()
                if rmin > -1: matacq = matacq[(matacq["run"] >= rmin)]
                if rmax > -1: matacq = matacq[(matacq["run"] <= rmax)]

        df_tmatacq = df.copy()

        df_tmatacq["tstart0"]  = df_tmatacq.reset_index().set_index(["run","seq"]).index.map(matacq[(matacq["side"] == 0)].set_index(["run", "seq"]).tstart)
        df_tmatacq["tstart1"]  = df_tmatacq.reset_index().set_index(["run","seq"]).index.map(matacq[(matacq["side"] == 1)].set_index(["run", "seq"]).tstart)


        idx = pd.IndexSlice

        if any(df_tmatacq.columns.get_level_values('side') == 0):        df_tmatacq.loc[:, idx[:,:,:,(df_tmatacq.columns.get_level_values('side') == 0)]] = df_tmatacq.tstart0
        if any(df_tmatacq.columns.get_level_values('side') == 1):        df_tmatacq.loc[:, idx[:,:,:,(df_tmatacq.columns.get_level_values('side') == 1)]] = df_tmatacq.tstart1

        df_tmatacq = df_tmatacq.drop(columns = ["tstart1", "tstart0"])
        first_idx = df_tmatacq.sort_index().first_valid_index()
        df_tmatacq = df_tmatacq.sub(df_tmatacq.loc[first_idx])

        return df_tmatacq
        
def subtract_tmatacq(df, year, basedir, FED, green = False):
        """
        Subtracts the tstart of MATACQ - needed for blue laser.
        The dataframe must be given in the format:

        side                                     0    1   ...
        date                 run        seq 
        2018-07-13 04:27:43  319579     0        XX   YY  ...
        ...                  ...        ...      ...  ... ...
        """
        fullpath = make_path(year, green)
        matacq = pd.read_hdf((basedir / fullpath), 'Matacq')
        matacq = matacq[(matacq["FED"] == FED)]
        df["tstart0"]  = df.reset_index().set_index(["run","seq"]).index.map(matacq[(matacq["side"] == 0)].set_index(["run", "seq"]).tstart)
        df["tstart1"]  = df.reset_index().set_index(["run","seq"]).index.map(matacq[(matacq["side"] == 1)].set_index(["run", "seq"]).tstart)
        
        #convert to ns and subtract matacq for side 1 and 0 
        df.iloc[:, :-2] = df.iloc[:, :-2] * 25 #conv times to ns (except for matacq columns)
        idx = pd.IndexSlice

        df.loc[:, idx[:,:,:,(df.columns.get_level_values('side') == 1)]] = df.sub(df.tstart1, axis = 0) + 1390 #1390 is some random offset
        df.loc[:, idx[:,:,:,(df.columns.get_level_values('side') == 0)]] = df.sub(df.tstart0, axis = 0) + 1390 #1390 is some random offset
        df = df.drop(columns = ["tstart1", "tstart0"])
        matacq = pd.DataFrame()
        return df


def skim_history(df, table_content, year, args, basedir = "", FED = -1, sub_tmatacq = False):
        
        """
        Skims history based on channels and runs 
        * timing history: subtract matacq for blue laser, subtract first run
        * APD history:    divide by first run
        
        Returns df in the format         
                                                             <this_table>    
        date                 run        seq      (id_xtal)   
        2018-07-13 04:27:43  319579     0        0           XX
        ...                  ...        ...      ...         ...
        """

        df = df.reset_index().set_index(["date","seq","run"])
        df = df.T.reset_index()
        df = append_idxs(df, args.ch, args.ietamin, args.ietamax, args.iphimin, args.iphimax, args.side, args.TT).T

        if table_content == "time": 
                if sub_tmatacq: 
                        df = subtract_tmatacq(df, year, basedir, FED)
                else: 
                        df = df * 25 #only convert to ns

        if args.rmin > -1 or args.rmax > -1:
                df = df.reset_index().set_index(["date", "seq"])
                if args.rmin > -1: df = df[(df["run"] >= args.rmin)]
                if args.rmax > -1: df = df[(df["run"] <= args.rmax)]
                df = df.reset_index().set_index(["date", "run","seq"])

        first_idx = df.sort_index().first_valid_index()
        first = df.loc[[first_idx]]

        df = df.reset_index().set_index(["date", "run","seq"])

        if table_content == "time":   df = df.T.sub(first.T[first.T.columns[0]], axis = 0).T
        if table_content == "APD_PN": df = df.T.divide(first.T[first.T.columns[0]], axis = 0).T

        return df
        
def stack_history(df):
        df = df.reset_index().set_index(["date","run", "seq"]).T.reset_index().set_index("xtal_id").drop(columns= ["iphi", "ieta","side", "TT"]).T
        df = df.reset_index().set_index(["date","run", "seq"]).stack().reset_index().set_index(["date","run", "seq", "xtal_id"]) #stack crystals
        return df



def select_era(df, year, era):
        """
        Selects era by run number
        """

        run_range = []
        if year == 2018:
                if era == "A": run_range = [315252,316995]
                if era == "B": run_range = [316998,319312]
                if era == "C": run_range = [319313,320393]
                if era == "D": run_range = [320394,325273]
                
        if len(run_range) == 0: sys.exit("!!! Era " + era + " not in " + year)
        df = df[(df["run"] >= run_range[0]) & (df["run"] <= run_range[1])]
        return df




