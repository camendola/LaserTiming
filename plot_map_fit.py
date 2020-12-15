import ROOT
import ecalic 
import pandas as pd
import numpy as np
import sys
from array import array
import os.path
import argparse


def table_to_TH2(table, name, fed = None):
    x = np.asarray(list(table.columns.values), dtype = np.float64)
    y = np.asarray(list(table.index.values), dtype = np.float64)

    x = np.append(x, x[-1] + (x[-1]-x[-2]))
    if (not fed) or fed > 627:   
        y = np.append(y, y[0] + (y[0]-y[1]))
        y.sort()
    if (not fed) or fed < 628:         
        y = np.append(y, y[-1] + (y[-1]-y[-2]))
        y.sort()
    x.sort()

    x = np.unique(x)
    y = np.unique(y)

    hist = ROOT.TH2F(name, name, len(x)-1, x, len(y)-1, y) 

    isPandas = False
    if(len(table.columns.values) + 1 < 256): isPandas = True
    i = 0

    for row in table.itertuples():
        for j , val in enumerate(list(table.columns.values)):
            if isPandas: 
                hist.SetBinContent(j+1,i+1,getattr(row, "_"+str(j+1)))
            else: 
                hist.SetBinContent(j+1,i+1,row[j+1]) 
        if (not fed) and (i+1 == 85):   
            i += 1
            hist.SetBinContent(j+1,i+1,np.nan) 
        i += 1
    return hist

def Frame(gPad,width=2):
    gPad.Update()
    gPad.RedrawAxis()
    l = ROOT.TLine()
    l.SetLineWidth(width)
    lm = gPad.GetLeftMargin();
    rm = 1.-gPad.GetRightMargin();
    tm = 1.-gPad.GetTopMargin();
    bm = gPad.GetBottomMargin();
    #top
    l.DrawLineNDC(lm,tm,rm,tm);
    #right
    l.DrawLineNDC(rm,bm,rm,tm);
    #bottom
    l.DrawLineNDC(lm,bm,rm,bm);
    #top
    l.DrawLineNDC(lm,bm,lm,tm);


def gridline(gPad,line, width=2, style = 2, axis = 0):
    # axis = 0 for horizontal line, axis = 1 for vertical line
    l = ROOT.TLine()
    l.SetLineWidth(width)
    l.SetLineStyle(style)
    lm = gPad.GetUxmax();
    rm = gPad.GetUxmin();
    tm = gPad.GetUymax();
    bm = gPad.GetUymin();
    if axis == 0: 
        l.DrawLine(rm, line, lm, line);
    else:
        l.DrawLine(line, tm, line, bm);
    return l
        
def TextAuto(gPad, text, size = 0.035, font=42, align = 13):
    x = 0
    y = 0
    
    t = gPad.GetTopMargin()
    b = gPad.GetBottomMargin()
    l = gPad.GetLeftMargin()
    r = gPad.GetRightMargin()
    if align==13:
        x = l + 0.02
        y = 1 - t - 0.02
    if align==31:
        x = 1 - r 
        y = 1 - t + 0.01
    if align==11:
        x = l 
        y = 1 - t + 0.01
    latex = ROOT.TLatex()
    latex.SetNDC();
    latex.SetTextSize(size)
    latex.SetTextAlign(align)
    latex.SetTextFont(font)
    latex.DrawLatex(x,y,text)
    return latex

def Text(gPad, text,x,y, size = 0.035, font=42, align = 13):
    latex = ROOT.TLatex()
    latex.SetNDC();
    latex.SetTextSize(size)
    latex.SetTextAlign(align)
    latex.SetTextFont(font)
    latex.DrawLatex(x,y,text)
    return latex



parser = argparse.ArgumentParser(description='Command line parser of plotting options')

parser.add_argument('--fed',     dest='fed',     type=int, help='fed',  default=None)
parser.add_argument('--isgreen', dest='isgreen', help='green laser',    default=False,  action ='store_true')
parser.add_argument('--grid',    dest='grid',    help='draw TT grid',   default=False,  action ='store_true')

args = parser.parse_args()

fed = None
if args.fed: fed = args.fed 

filename = "fits_results/temperature/FEDX_ch_split_rootfit"
if args.isgreen: filename = "fits_results/temperature/FEDX_ch_split_rootfit_green"
filename  = filename + ".csv" 
if fed: 
    df = pd.read_csv(filename.replace("X", str(fed)), index_col=[0,1],  header=[0, 1], skipinitialspace=True)
else: 
    dfs = []
    for i in range(610,646):
         if os.path.isfile(filename.replace("X", str(i))):
             df = pd.read_csv(filename.replace("X", str(i)), index_col=[0,1],  header=[0,1], skipinitialspace=True) 
             dfs.append(df)
    df = pd.concat(dfs)
    del dfs
        
df.columns = pd.MultiIndex.from_tuples(df.columns)


df = df.reset_index().set_index(["ch", "FED", ("TCDS","TCDS1"),("TCDS","TCDS2"),("TCDS","TCDS3"),("TCDS","TCDS4"),("TCDS","TCDS5"), ("TCDS","TCDS6")])
df = df[(df.T != 0).any()]

df = df.reset_index().set_index("ch")


df = df[(df["FED"] > 609)]
df = df.reset_index().set_index(["ch", "FED"])

ecal = ecalic.icCMS().iov
if fed: ecal = ecal[ecal['FED']== fed]
ecal = ecal.reset_index().set_index(["elecID", "FED"])


df['ieta']    = df.reset_index().set_index(["ch", "FED"]).index.map(ecal["ix"])
df['iphi']    = df.reset_index().set_index(["ch", "FED"]).index.map(ecal.iy)
df['TT']      = df.reset_index().set_index(["ch", "FED"]).index.map(ecal.ccu)

#add sides mask
side1 = (((df['ieta'] > 0) & (df['ieta'] > 5) & ((df['iphi'] - 1).mod(20) + 1  > 10)) |  #EB+
         ((df['ieta'] < 0) & (df['ieta'] < - 5) & ((df['iphi'] - 1).mod(20) + 1 < 11)))  #EB-

df['side'] = np.where(side1, 1, 0)


if fed:
    xline = (ecal.groupby("ccu")['iy'].max() + 1).tolist()
    if fed < 628: yline = (ecal.groupby("ccu")['ix'].max() + 1).tolist()
    if fed > 627: yline = (ecal.groupby("ccu")['ix'].max()).tolist()

else:
    xline = (df.reset_index().groupby("FED")["iphi"].max()+ 1).tolist()
    yline = (df.reset_index().groupby("FED")["ieta"].max()+ 1).tolist()

xline = list(dict.fromkeys(xline)) 
yline = list(dict.fromkeys(yline)) 

TCDSs = ["TCDS2", "TCDS3", "TCDS4"]
TCDSmean = [40.078887, 40.078963, 40.078974]

vars = ["slope", "intercept", "unc_slope_rel"]#, "chi2"]
dims = ["[ns/#circ C]", "[ns]", ""] #, "unc_slope", "/ndof"]
ROOT.gROOT.SetBatch(True)
if fed:
    c = ROOT.TCanvas("c", "c", 400,600)
else:
    c = ROOT.TCanvas()

c.SetRightMargin(0.17)
FEDs = array('d', df.reset_index()['FED'].drop_duplicates().tolist())
FEDs_ = array('d', [f+0.5 for f in FEDs])
FEDs_err = array('d', [0]*len(FEDs))
mins = [-0.05, -5.5]
maxs = [0.2, 1]
#mins = [-0.06, -5.5]
#maxs = [0.13, 1]
#mins = [0.1, -3.3]
#maxs = [0.16, -2.6]

for k, var in enumerate(vars):
    for t,TCDS in enumerate(TCDSs):
        df [("unc_slope_rel",TCDS)] = df [("unc_slope",TCDS)]/df [("slope",TCDS)]
        df = df[(df [("unc_slope_rel",TCDS)] < 3) & (df [("unc_slope_rel",TCDS)] > -3)]
        bincontent =  df.pivot(index='ieta', columns='iphi', values=(var,TCDS)) #.values
        hist =  table_to_TH2(bincontent, "map", fed)

        hist.Draw("colz")
        hist.SetTitle("")
        #if not fed:
        #hist.SetMinimum(min)
        #hist.SetMaximum(max)
        hist.GetXaxis().SetTitle("i#phi")
        hist.GetYaxis().SetTitle("i#eta")
        hist.GetZaxis().SetTitle(vars[k]+" "+dims[k])
        hist.GetZaxis().SetTitleOffset(1.2)
        ROOT.gStyle.SetOptStat(0)
        label = TextAuto(ROOT.gPad, "TCDS = %f MHz" % TCDSmean[t], align = 31)
        if fed: flabel = TextAuto(ROOT.gPad, "FED = %d" % fed, align = 11)
        Frame(ROOT.gPad)

        if args.grid:
            if fed:
                labeldf = ecal.groupby("ccu").mean()
                if fed > 627: labeldf["ieta"] = (ecal.groupby("ccu")["ix"].max()) 
                if fed < 628: labeldf["ieta"] = (ecal.groupby("ccu")["ix"].min()) 
                labeldf["iphi"] = (ecal.groupby("ccu")["iy"].min())
                
                labelcontent = labeldf.reset_index().pivot(index='ieta', columns='iphi', values='ccu')
                lhist = table_to_TH2(labelcontent, "lmap", fed)

                lhist.SetMarkerSize(1.8);
                lhist.Draw("text same")
                lhist.SetTitle("")
                c.Update()
                c.Modified()

            for line in xline: gridline(ROOT.gPad,line, axis = 1)
            for line in yline: gridline(ROOT.gPad,line, axis = 0)
        if fed: 
            c.SaveAs("/eos/home-c/camendol/www/LaserTiming/%s_t_vs_T/fed%d_%s_TCDS%d.pdf" %("green" if args.isgreen else "blue", fed, var, t))
            c.SaveAs("/eos/home-c/camendol/www/LaserTiming/%s_t_vs_T/fed%d_%s_TCDS%d.png" %("green" if args.isgreen else "blue", fed, var, t))
        else:
            c.SaveAs("/eos/home-c/camendol/www/LaserTiming/%s_t_vs_T/full_%s_TCDS%d.pdf" %("green" if args.isgreen else "blue", var, t))
            c.SaveAs("/eos/home-c/camendol/www/LaserTiming/%s_t_vs_T/full_%s_TCDS%d.png" %("green" if args.isgreen else "blue", var, t))

if not fed:
    df = df.reset_index()
    colors = [ROOT.kRed, ROOT.kBlue, ROOT.kGreen]
    cg = ROOT.TCanvas("cg", "cg", 600, 600)
    cg.SetLeftMargin(0.17)
    for k, var in enumerate(vars):
        mg = ROOT.TMultiGraph()
        legend = ROOT.TLegend(0.7, 0.89, 0.7, 0.89)
        for t,TCDS in enumerate(TCDSs):
            thisvarI     = array('d', df[df["side"] == 1].groupby('FED').mean()[(var,TCDS)].values)
            thisvarI_err = array('d', df[df["side"] == 1].groupby('FED').std()[(var,TCDS)].div(2).values)
            thisvarL     = array('d', df[df["side"] == 0].groupby('FED').mean()[(var,TCDS)].values)
            thisvarL_err = array('d', df[df["side"] == 0].groupby('FED').std()[(var,TCDS)].div(2).values)
            grI = ROOT.TGraphErrors(len(FEDs), FEDs,  thisvarI, FEDs_err, thisvarI_err)
            grL = ROOT.TGraphErrors(len(FEDs), FEDs_,  thisvarL, FEDs_err, thisvarL_err)
            
            grI.SetMarkerColor(colors[t])
            grI.SetLineColor(colors[t])
            grI.SetMarkerStyle(21)
            grL.SetMarkerColor(colors[t] + 1)
            grL.SetMarkerStyle(8)
            grL.SetLineColor(colors[t] + 1)
            
            legend.AddEntry(grI, "TCDS = %f MHz" % TCDSmean[t], "pl")
            
            mg.Add(grI)
            mg.Add(grL)

        dummyI = ROOT.TGraphErrors(len(FEDs), FEDs,  FEDs_err, FEDs_err, FEDs_err)
        dummyL = ROOT.TGraphErrors(len(FEDs), FEDs,  FEDs_err, FEDs_err, FEDs_err)
        dummyI.SetMarkerColor(ROOT.kGray)
        dummyI.SetLineColor(ROOT.kGray)
        dummyI.SetMarkerStyle(21)
        dummyL.SetMarkerColor(ROOT.kGray)
        dummyL.SetMarkerStyle(8)
        dummyL.SetLineColor(ROOT.kGray)
        legend.AddEntry(dummyI, "side: I", "pl")
        legend.AddEntry(dummyL, "side: L", "pl")
        mg.Draw("ap")


        mg.GetXaxis().SetTitle("FED")
        mg.GetYaxis().SetTitle(vars[k]+" "+dims[k])
        Frame(ROOT.gPad)

        cg.Update()
        cg.Modified()
        gridline(ROOT.gPad,627.8, axis = 1, style =1, width = 2)
        labelm = Text(ROOT.gPad, "EB- ", 0.52, 0.13, align = 31)
        labelp = Text(ROOT.gPad, " EB+", 0.55, 0.13, align = 11)
        legend.Draw("same")
        cg.SaveAs("/eos/home-c/camendol/www/LaserTiming/%s_t_vs_T/full_%s.pdf" %("green" if args.isgreen else "blue",var))
        cg.SaveAs("/eos/home-c/camendol/www/LaserTiming/%s_t_vs_T/full_%s.png" %("green" if args.isgreen else "blue",var))
        
