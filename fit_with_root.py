from ROOT import *
from array import array
import modules.write_csv as write_csv
import sys
import os.path

gROOT.SetBatch(0)

fed = int(sys.argv[1])
if fed > 627:
    ietas = [5+(x*10)+0.5 for x in range(0, 6)]
else:
    ietas = [5+(x*10)-0.5 for x in range(-6, 0)]

for ieta in ietas:
    slope = []
    intercept = []
    unc_slope = []
    unc_intercept = []
    TCDS = []
    for tcds in range(1,6):
        b = 0
        m = 0
        unc_b = 0
        unc_m = 0

        if tcds == 2 or tcds == 3: 
            X = array( 'd' )
            Y = array( 'd' )
            if  os.path.isfile("fits_results/temperature/FED_%d_ieta_%.1f_TCSD%d.csv" % (fed, ieta, tcds)): 
                with open("fits_results/temperature/FED_%d_ieta_%.1f_TCSD%d.csv" % (fed, ieta, tcds)) as f:
                    next(f)
                    for l in f:
                        #print l.strip().split(" ")
                        date, hour, temperature, time =  l.strip().split(" ")
                        temperature = float(temperature)
                        time = float(time)
                        X.append(temperature)
                        Y.append(time)
                        
                    gr = TGraph(len(X), X, Y )
                    #gr.Draw("ap")
                    gr.Fit("pol1")
                    f = gr.GetFunction("pol1")
                    b = f.GetParameter(0)
                    m = f.GetParameter(1)
                    unc_b = f.GetParError(0)
                    unc_m = f.GetParError(1)
                    
        slope.append(m)
        intercept.append(b)
        unc_slope.append(unc_m)
        unc_intercept.append(unc_b)
        TCDS.append(tcds)
    print slope, TCDS
    write_csv.save_fit(fed, -999, ieta-4.5, ieta+4.5, slope , unc_slope, intercept, unc_intercept, TCDS, suffix = "rootfit")

