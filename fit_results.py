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

#df = pd.read_csv('fits_results/temperature/FEDs_ietabins_shifted_split_mean_rootfit.csv', index_col=[0,1],  header=[0, 1], skipinitialspace=True)
df = pd.read_csv('fits_results/temperature/FEDs_ietabins_shifted_split_rootfit.csv', index_col=[0,1],  header=[0, 1], skipinitialspace=True)
df.columns = pd.MultiIndex.from_tuples(df.columns)

df = df.sort_values(["FED", "ch"])
print(df.columns)
df = df.reset_index().set_index(["ch", "FED", ("TCDS","TCDS1"),("TCDS","TCDS2"),("TCDS","TCDS3"),("TCDS","TCDS4"),("TCDS","TCDS5"), ("TCDS","TCDS6")])
df = df[(df.T != 0).any()]
df = df.reset_index().set_index("ch")
FED1 = 610
FED2 = FED1+18

df_small = df[(df["FED"] == FED1) | (df["FED"] == FED2)]


TCDSs = ["TCDS2", "TCDS3", "TCDS4"]
TCDSmean = [40.078887, 40.078963, 40.078974]
#vars = ["slope", "intercept"]
#dims = ["[ns/$^\circ$C]", "[ns]"]
#vars = ["slope"]
#dims = ["[ns/$^\circ$C]"]
vars = ["chi2"]
dims = ["/ ndf"]
print (df_small)
#fig, ax = plt.subplots(1, 2, figsize = (12,6))
fig, ax = plt.subplots()
for i, var in enumerate(vars):
    for j,TCDS in enumerate(TCDSs):
            #ax.errorbar(x = df_small.reset_index()['ch'], y = df_small[(var, TCDS)], yerr = df_small[('unc_'+var, TCDS)], label = "TCDS = %.5f MHz" % TCDSmean[j], marker = "o")
            ax.errorbar(x = df_small.reset_index()['ch'], y = df_small[(var, TCDS)], label = "TCDS peak %d" % (df_small[('TCDS', TCDS)].to_list()[0]), marker = "o")
            
    ax.set_xlabel('i$\eta$')
    ax.set_ylabel(var+" "+dims[i])
plt.title(str(FED1)+"-"+str(FED2))
plt.legend()
fig.show()
#fig.savefig("/eos/home-c/camendol/www/LaserTiming/blue_t_vs_T/fitres_FED610-628_314050-327764.pdf", bbox_inches='tight')
#fig.savefig("/eos/home-c/camendol/www/LaserTiming/blue_t_vs_T/fitres_FED610-628_314050-327764.png", bbox_inches='tight')

input()
df["pair"] = (df["FED"] - 609) % 18

print(df)

for j, TCDS in enumerate(TCDSs):
    #fig, ax = plt.subplots(1, 2, figsize = (12,6))
    fig, ax = plt.subplots(figsize = (8,4))
    for i, var in enumerate(vars):
        for pair, gpair in df.groupby(["pair"]):
            if pair == 5: continue
            if pair == 11: continue
            if pair == 9: continue
            FEDs = gpair["FED"].drop_duplicates().to_list()
            if int(pair) < 10:
                ax.errorbar(x = gpair.reset_index()['ch'], y = gpair[(var, TCDS)], yerr = gpair[('unc_'+var, TCDS)], label = "FED = %d-%d" % (FEDs[0], FEDs[-1]), marker = "o")
                #ax.errorbar(x = gpair.reset_index()['ch'], y = gpair[(var, TCDS)],  label = "FED = %d-%d" % (FEDs[0], FEDs[-1]), marker = "o")
            else: 
                ax.errorbar(x = gpair.reset_index()['ch'], y = gpair[(var, TCDS)], yerr = gpair[('unc_'+var, TCDS)], label = "FED = %d-%d" % (FEDs[0], FEDs[-1]), marker = "s")
                #ax.errorbar(x = gpair.reset_index()['ch'], y = gpair[(var, TCDS)], label = "FED = %d-%d" % (FEDs[0], FEDs[-1]), marker = "s")
    ax.set_xlabel('i$\eta$')
    ax.set_ylabel(var+" "+dims[i])
    ax.text(1., 1., "TCDS = %.5f MHz" % TCDSmean[j],
               horizontalalignment='right',
               verticalalignment='bottom',
               transform=ax.transAxes)
    plt.gca().legend(loc='upper left', bbox_to_anchor=(1, 1))
    fig.show()
    fig.savefig("/eos/home-c/camendol/www/LaserTiming/blue_t_vs_T/fitres_vs_ieta_TCDS%d_314050-327764.pdf"%(gpair[('TCDS', TCDS)].to_list()[0]), bbox_inches='tight')
    fig.savefig("/eos/home-c/camendol/www/LaserTiming/blue_t_vs_T/fitres_vs_ieta_TCDS%d_314050-327764.png"%(gpair[('TCDS', TCDS)].to_list()[0]), bbox_inches='tight')
    input()
