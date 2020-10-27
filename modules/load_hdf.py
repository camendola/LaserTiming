from elmonk.common import HdfLaser
import ecalic
import numpy as np
import pandas as pd
import os.path

def load_history(filename, year, write, basedir, FED, property = 'tAPD'):
        if ((not os.path.isfile(filename)) or write):
                data = HdfLaser(basedir / f'{year}/dstUL_db.{year}.hdf5')
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


def append_idxs(df, ch = -1, ietamin = -999, ietamax = -999):
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
        
        #add sides mask
        side1 = (((df['ieta'] > 0) & (df['ieta'] > 5) & ((df['iphi'] - 1).mod(20) + 1 > 10)) |  #EB+
                 ((df['ieta'] < 0) & (df['ieta'] < - 5) & ((df['iphi'] - 1).mod(20) + 1 < 11))) #EB-
        df['side'] = np.where(side1, 1, 0)
        
        #make xtal_id as defined in dst files 
        df['TT']      = df.set_index('xtal_ecalic_id').index.map(ecalic.geom.ccu)   
        df['strip']   = df.set_index('xtal_ecalic_id').index.map(ecalic.geom.strip) 
        df['Xtal']    = df.set_index('xtal_ecalic_id').index.map(ecalic.geom.Xtal)  
        df["xtal_id"] = (df['TT'] - 1) * 25 + (df['strip'] - 1) * 5 + df['Xtal'] - 1

        if ch > -1: df = df[(df["xtal_id"] == ch)]        
        if ietamin > -999: df = df[(df["ieta"] >= ietamin)]        
        if ietamax > -999: df = df[(df["ieta"] <= ietamax)]        

        df = df.reset_index().set_index(["ieta", "iphi", "xtal_id", "side"])
        df = df.drop(columns=['TT', 'strip','Xtal', 'xtal_ecalic_id','index'])
        return df

def subtract_tmatacq(df, year, basedir, FED):
        """
        Subtracts the tstart of MATACQ - needed for blue laser.
        The dataframe must be given in the format:

        side                                     0    1   ...
        date                 run        seq 
        2018-07-13 04:27:43  319579     0        XX   YY  ...
        ...                  ...        ...      ...  ... ...
        """

        matacq = pd.read_hdf((basedir / f'{year}/dstUL_db.{year}.hdf5'), 'Matacq')
        matacq = matacq[(matacq["FED"] == FED)]
        df["tstart0"]  = df.reset_index().set_index(["run","seq"]).index.map(matacq[(matacq["side"] == 0)].set_index(["run", "seq"]).tstart)
        df["tstart1"]  = df.reset_index().set_index(["run","seq"]).index.map(matacq[(matacq["side"] == 1)].set_index(["run", "seq"]).tstart)
        
        #convert to ns and subtract matacq for side 1 and 0 
        df.iloc[:, :-2] = df.iloc[:, :-2] * 25 #conv times to ns (except for matacq columns)
        idx = pd.IndexSlice
        df.loc[:, idx[:,:,:,(df.columns.get_level_values('side') == 1)]] = df.sub(df.tstart1, axis = 0) + 1390 #1390 is some random offset
        df.loc[:, idx[:,:,:,(df.columns.get_level_values('side') == 0)]] = df.sub(df.tstart0, axis = 0) + 1390 #1390 is some random offset
        df = df.drop(columns = ["tstart1", "tstart0"])
        return df
