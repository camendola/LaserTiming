import pandas as pd
import os.path
import numpy as np
import statistics

def save_fit(FED, ch, ietamin, ietamax, slope,unc_slope, intercept, unc_intercept, chi2, TCDS, suffix = "simfit"):
    #if FED == -1:
                
    #elif FED == 1:

    if FED:
        chorieta = "ch" if ietamax == -999 else "ietabins"
        if ietamax > -999 and ietamin > -999: ch = statistics.mean([ietamax,ietamin])
        print('fits_results/temperature/FEDs_'+chorieta+'.csv')
        if os.path.isfile('fits_results/temperature/FEDs_'+chorieta+'_'+suffix+'.csv'):
            df = pd.read_csv('fits_results/temperature/FEDs_'+chorieta+'_'+suffix+'.csv', index_col=[0,1],  header=[0, 1], skipinitialspace=True)
            df.columns = pd.MultiIndex.from_tuples(df.columns)
            df.loc[(FED, ch), "slope"]  = slope
            df.loc[(FED, ch), "unc_slope"]  = unc_slope
            df.loc[(FED, ch), "intercept"] = intercept
            df.loc[(FED, ch), "unc_intercept"] = unc_intercept
            df.loc[(FED, ch), "chi2"] = chi2
            df.loc[(FED, ch), "TCDS"]   = TCDS
            print(df)
            df.to_csv('fits_results/temperature/FEDs_'+chorieta+'_'+suffix+'.csv', mode='w')
        else:
            columns = ["TCDS1", "TCDS2","TCDS3","TCDS4","TCDS5", "TCDS6"]
            idx = pd.MultiIndex.from_arrays([[FED], [ch]], names=['FED','ch'])
            dfs = pd.DataFrame([slope],  index=idx, columns = columns)
            dfs_u = pd.DataFrame([unc_slope],  index=idx, columns = columns)
            dfo = pd.DataFrame([intercept], index=idx, columns = columns)
            dfo_u = pd.DataFrame([unc_intercept], index=idx, columns = columns)
            dfchi2 = pd.DataFrame([chi2],   index=idx, columns = columns)
            dft = pd.DataFrame([TCDS],   index=idx, columns = columns)
            df = pd.concat([dfs,dfs_u,dfo,dfo_u,dfchi2, dft],axis=1,keys=['slope','unc_slope','intercept', 'unc_intercept','chi2', 'TCDS']).sort_index(axis=1)
            print (df)
            df.to_csv('fits_results/temperature/FEDs_'+chorieta+'_'+suffix+'.csv')
    #else:

