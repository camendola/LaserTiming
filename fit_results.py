from elmonk.dst import DstReader
import matplotlib.pyplot as plt
import matplotlib as mpl
import pandas as pd
import numpy as np

mpl.rcParams['axes.linewidth'] = 2
mpl.rcParams['axes.formatter.useoffset'] = False

mpl.rcParams['xtick.direction'] = 'in'
mpl.rcParams['ytick.direction'] = 'in'
mpl.rcParams["ytick.right"] = True
mpl.rcParams["xtick.top"] = True

df = pd.read_csv('fits_results/temperature/FEDs_ietabins_simfit.csv', index_col=[0,1],  header=[0, 1], skipinitialspace=True)
df.columns = pd.MultiIndex.from_tuples(df.columns)

df = df.sort_values(["FED", "ch"])
df = df.reset_index().set_index("ch")
df_small = df[(df["FED"] == 610) | (df["FED"] == 628)]


TCDSs = ["TCDS2", "TCDS3"]
vars = ["slope", "intercept"]
dims = ["[ns/$^\circ$C]]", "[ns]"]
print (df_small)
fig, ax = plt.subplots(1, 2, figsize = (12,6))
for i, var in enumerate(vars):
    for TCDS in TCDSs:

        ax[i].errorbar(x = df_small.reset_index()['ch'], y = df_small[(var, TCDS)], yerr = df_small[('unc_'+var, TCDS)], label = "TCDS = %.4f MHz" % (df_small[('TCDS', TCDS)].to_list()[0]), marker = "o")
        
    ax[i].set_xlabel('i$\eta$')
    ax[i].set_ylabel(var+" "+dims[i])

plt.legend()
fig.show()
input()

df["pair"] = (df["FED"] - 609) % 18

print(df)

for TCDS in TCDSs:
    fig, ax = plt.subplots(1, 2, figsize = (12,6))
    for i, var in enumerate(vars):
        for pair, gpair in df.groupby(["pair"]):
            FEDs = gpair["FED"].drop_duplicates().to_list()
            ax[i].errorbar(x = gpair.reset_index()['ch'], y = gpair[(var, TCDS)], yerr = gpair[('unc_'+var, TCDS)], label = "FED = %d-%d" % (FEDs[0], FEDs[-1]), marker = "o")
        
    ax[1].set_xlabel('i$\eta$')
    ax[1].set_ylabel(var+" "+dims[i])
    ax[1].text(1., 1., "TCDS = %.4f MHz" % (gpair[('TCDS', TCDS)].to_list()[0]),
               horizontalalignment='right',
               verticalalignment='bottom',
               transform=ax[i].transAxes)
    plt.legend()
    fig.show()
    input()
