from ROOT import *
from array import array
import modules.write_csv as write_csv
import sys
import os.path
import pandas as pd
import numpy as np

import argparse
parser = argparse.ArgumentParser(description='Command line parser of plotting options')

parser.add_argument('--fed',     dest='fed',     type=int, help='fed', default=None)
parser.add_argument('--isgreen', dest='isgreen', help='green laser',   default=False,  action ='store_true')

args = parser.parse_args()

def shift_to_zero(X, Y):
    df = pd.DataFrame(list(zip(X.tolist(),Y.tolist())), columns=["X", "Y"])    
    df["X"] = df["X"]-22.025

    df["Y"] = df["Y"] - df[df["X"].abs() < 0.5]["Y"].mean()
    return array('d', df["X"].values.tolist()), array('d', df["Y"].values.tolist())

    return array('d', df["X"].values.tolist()), array('d', df["Y"].values.tolist()),array('d', df["Xerr"].values.tolist()), array('d', df["Yerr"].values.tolist())

gROOT.SetBatch(0)

fed = args.fed
year = 2018
if os.path.isfile("/afs/cern.ch/work/c/camendol/LaserData/"+str(year)+"/history_FED%d.dat" % (fed)):
    df = pd.read_csv("/afs/cern.ch/work/c/camendol/LaserData/"+str(year)+"/history_FED%d.dat" % (fed))
if args.isgreen:
    if os.path.isfile("/afs/cern.ch/work/c/camendol/LaserData/"+str(year)+"/green/history_FED%d.dat" % (fed)):
        df = pd.read_csv("/afs/cern.ch/work/c/camendol/LaserData/"+str(year)+"/green/history_FED%d.dat" % (fed))

ranges = [40.0784, 40.0785, 40.0789, 40.07897, 40.0790, 40.07915, 40.0793] #TCDS ranges

thesech = [470, 471, 472, 473, 474, 495, 496, 497, 498, 499, 469, 468, 467, 466, 465, 494, 493, 492, 491, 490, 460, 461, 462, 463, 464, 485, 486, 487, 488, 489, 459, 458, 457, 456, 455, 484, 483, 482, 481, 480, 450, 451, 452, 453, 454, 475, 476, 477, 478, 479, 370, 371, 372, 373, 374, 395, 396, 397, 398, 399, 369, 368, 367, 366, 365, 394, 393, 392, 391, 390, 360, 361, 362, 363, 364, 385, 386, 387, 388, 389, 359, 358, 357, 356, 355, 384, 383, 382, 381, 380, 350, 351, 352, 353, 354, 375, 376, 377, 378, 379, 254, 253, 252, 251, 250, 279, 278, 277, 276, 275, 255, 256, 257, 258, 259, 280, 281, 282, 283, 284, 264, 263, 262, 261, 260, 289, 288, 287, 286, 285, 265, 266, 267, 268, 269, 290, 291, 292, 293, 294, 274, 273, 272, 271, 270, 299, 298, 297, 296, 295, 154, 153, 152, 151, 150, 179, 178, 177, 176, 175, 155, 156, 157, 158, 159, 180, 181, 182, 183, 184, 164, 163, 162, 161, 160, 189, 188, 187, 186, 185, 165, 166, 167, 168, 169, 190, 191, 192, 193, 194, 174, 173, 172, 171, 170, 199, 198, 197, 196, 195, 54, 53, 52, 51, 50, 79, 78, 77, 76, 75, 55, 56, 57, 58, 59, 80, 81, 82, 83, 84, 64, 63, 62, 61, 60, 89, 88, 87, 86, 85, 65, 66, 67, 68, 69, 90, 91, 92, 93, 94, 74, 73, 72, 71, 70, 99, 98, 97, 96, 95]

c = TCanvas()
for chname, ch in df.groupby("xtal_id"):
    if (fed == 614 and chname in thesech): 
        ch = ch[pd.to_datetime(ch["date"], unit="s") < "2018-04-15 12:00:00"]
    print "@@@ xtal %d" % chname
    slope = []
    u_slope = []
    intercept = []
    u_intercept = []
    TCDS = []
    chi2 = []
    for tcdsname, gr in ch.groupby(pd.cut(ch.TCDS, ranges)):
        X = array( 'd' )
        Y = array( 'd' )
        m = 0
        b = 0
        u_m = 0
        u_b = 0
        tcds = 0
        f = np.nan
        k = 0 
        if not gr.empty:
            gr = gr.dropna()
            tcds= gr["TCDS"].mean()
            X = array('d', gr["temperature"].values.tolist())
            Y = array('d', gr["time"].values.tolist())
            gr = TGraph(len(X), X, Y)
            gr.Draw("ap")
            gr.SetMarkerStyle(8)
            f = None
            f = TF1("f","[0]+[1]*x",20,30)
            gr.Fit(f, "Q")
            if chname == 958:
                c.Update()
                c.Modified()
                raw_input()

            b = f.GetParameter(0)
            m = f.GetParameter(1)
            u_b = f.GetParError(0)
            u_m = f.GetParError(1)
            k = f.GetChisquare()/f.GetNDF()
            print "**** Chi2 = ", f.GetChisquare(), " NDF = ", f.GetNDF(), " Chi2/NDF = ",f.GetChisquare()/f.GetNDF()
            
        slope.append(m)
        intercept.append(b)
        u_slope.append(u_m)
        u_intercept.append(u_b)
        TCDS.append(tcds)
        chi2.append(k)
    suffix = "split_rootfit"
    if args.isgreen: suffix = suffix + "_green"
    #write_csv.save_fit(fed, chname, -999, -999, -999, slope , u_slope, intercept, u_intercept, chi2, TCDS, suffix = suffix)

