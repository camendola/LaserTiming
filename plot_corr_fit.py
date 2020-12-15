import ROOT
import ecalic 
import pandas as pd
import numpy as np
import sys
from array import array
import os.path
import argparse

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
    print(t,b,l,r)    
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

def read_fit(filename, fed, ecal):
    df = pd.read_csv(filename.replace("X", str(fed)), index_col=[0,1],  header=[0, 1], skipinitialspace=True)
    df.columns = pd.MultiIndex.from_tuples(df.columns)
    df = df.reset_index().set_index(["ch", "FED", ("TCDS","TCDS1"),("TCDS","TCDS2"),("TCDS","TCDS3"),("TCDS","TCDS4"),("TCDS","TCDS5"), ("TCDS","TCDS6")])
    df = df[(df.T != 0).any()]
    
    df = df.reset_index().set_index("ch")
    
    df = df[(df["FED"] > 609)]
    df = df.reset_index().set_index(["ch", "FED"])
    
    df['ieta']    = df.reset_index().set_index(["ch", "FED"]).index.map(ecal["ix"])
    df['iphi']    = df.reset_index().set_index(["ch", "FED"]).index.map(ecal.iy)
    df['TT']      = df.reset_index().set_index(["ch", "FED"]).index.map(ecal.ccu)
    
    #add sides mask
    side1 = (((df['ieta'] > 0) & (df['ieta'] > 5) & ((df['iphi'] - 1).mod(20) + 1  > 10)) |  #EB+
             ((df['ieta'] < 0) & (df['ieta'] < - 5) & ((df['iphi'] - 1).mod(20) + 1 < 11)))  #EB-

    df['side'] = np.where(side1, 1, 0)
    df = df.sort_values(by=['ieta','iphi'])
    
    return df



parser = argparse.ArgumentParser(description='Command line parser of plotting options')

parser.add_argument('--fed',     dest='fed',     type=int, help='fed',  default=None)
parser.add_argument('--isgreen', dest='isgreen', help='green laser',    default=False,  action ='store_true')
parser.add_argument('--grid',    dest='grid',    help='draw TT grid',   default=False,  action ='store_true')

args = parser.parse_args()

fed = 610
if args.fed: fed = args.fed 

filename_blue = "fits_results/temperature/FEDX_ch_split_rootfit.csv"
filename_green = "fits_results/temperature/FEDX_ch_split_rootfit_green.csv"

ecal = ecalic.icCMS().iov
if fed: ecal = ecal[ecal['FED']== fed]
ecal = ecal.reset_index().set_index(["elecID", "FED"])

df_blue = read_fit(filename_blue, fed, ecal).reset_index().set_index(["ieta","iphi","TT","side","ch", "FED"])
df_green = read_fit(filename_green, fed, ecal).reset_index().set_index(["ieta","iphi","TT", "side","ch", "FED"])

print(df_blue)
df = pd.concat([df_blue, df_green], axis = 1, keys = ["blue","green"])
print(df)
df = df.reset_index().set_index(["ch", "FED"])

TCDSs = ["TCDS2", "TCDS3", "TCDS4"]
TCDSmean = [40.078887, 40.078963, 40.078974]

x = np.asarray(df['iphi'].tolist(), dtype = np.float64)
y = np.asarray(df['ieta'].tolist(), dtype = np.float64)    
x = np.unique(x)
y = np.unique(y)


vars = ["slope", "intercept"] #, "chi2"]
dims = ["[ns/#circ C]", "[ns]"] #, "unc_slope", "/ndof"]
ROOT.gROOT.SetBatch(True)

if fed:
    c = ROOT.TCanvas("c", "c", 400,600)
else:
    c = ROOT.TCanvas()

c.SetRightMargin(0.17)

c1 = ROOT.TCanvas("c1", "c1", 700,600)
c1.SetRightMargin(0.17)
c1.SetLeftMargin(0.17)

FEDs = array('d', df.reset_index()['FED'].drop_duplicates().tolist())
FEDs_ = array('d', [f+0.5 for f in FEDs])
FEDs_err = array('d', [0]*len(FEDs))


for k, var in enumerate(vars):
    for t,TCDS in enumerate(TCDSs):
        c.cd()
        df[("blue_over_green", var,TCDS)] = df[("blue", var,TCDS)]/df[("green", var,TCDS)]

        bincontent =  df.pivot(index='iphi', columns='ieta', values=("blue_over_green", var,TCDS)).values
        


        hist = ROOT.TH2F("map", "map", len(x)-1, x, len(y) -1 , y) 
        for i in range(1, len(x)):
            for j in range(1, len(y)):
                hist.SetBinContent(i,j, bincontent[i,j])
        
        hist.Draw("colz")
        hist.SetTitle("")
        #if not fed:
        #hist.SetMinimum(min)
        #hist.SetMaximum(max)
        hist.GetXaxis().SetTitle("i#phi")
        hist.GetYaxis().SetTitle("i#eta")
        hist.GetZaxis().SetTitle("blue/green " + vars[k]+" "+dims[k])
        hist.GetZaxis().SetTitleOffset(1.2)
        ROOT.gStyle.SetOptStat(0)
        label = TextAuto(ROOT.gPad, "TCDS = %f MHz" % TCDSmean[t], align = 31)
        if fed: flabel = TextAuto(ROOT.gPad, "FED = %d" % fed, align = 11)
        Frame(ROOT.gPad)

        if not fed:
            for line in xline:  gridline(ROOT.gPad,line, axis = 0)
            for line in yline:  gridline(ROOT.gPad,line, axis = 1)
        elif args.grid:
            for line in xTT:  gridline(ROOT.gPad,line, axis = 0)
            for line in yTT:  gridline(ROOT.gPad,line, axis = 1)
            
            labeldf = ecal.groupby("ccu").mean()
            labeldf["ieta"] = (ecal.groupby("ccu").max()+ecal.groupby("ccu").min())["iy"]/2
            labeldf["iphi"] = (ecal.groupby("ccu").max()+ecal.groupby("ccu").min())["ix"]/2
            labelcontent = labeldf.reset_index().pivot(index='iphi', columns='ieta', values='ccu').values

            lhist = ROOT.TH2F("lmap", "lmap", len(xTT), xTT, len(yTT), yTT) 

            for i in range(0, len(xTT) - 1):
                for j in range(0, len(yTT) - 1):
                    
                    lhist.SetBinContent(i,j, labelcontent[i,j])
            lhist.SetMarkerSize(1.8);
            lhist.Draw("text same")
            lhist.SetTitle("")
            c.Update()
            c.Modified()

        if fed: 
            c.SaveAs("/eos/home-c/camendol/www/LaserTiming/bg_t_vs_T/fed%d_%s_TCDS%d.pdf" %( fed, var, t))
            c.SaveAs("/eos/home-c/camendol/www/LaserTiming/bg_t_vs_T/fed%d_%s_TCDS%d.png" %( fed, var, t))
        else:
            c.SaveAs("/eos/home-c/camendol/www/LaserTiming/bg_t_vs_T/full_%s_TCDS%d.pdf" %( var, t))
            c.SaveAs("/eos/home-c/camendol/www/LaserTiming/bg_t_vs_T/full_%s_TCDS%d.png" %( var, t))

        c1.cd()
        xmean = df[("blue", var,TCDS)].mean()
        xmin = df[("blue", var,TCDS)].min()
        xmin = xmin - (xmean - xmin)/5
        xmax = df[("blue", var,TCDS)].max() 
        xmax = xmax + (xmax-xmean)/5
        ymean = df[("green", var,TCDS)].mean()
        ymin = df[("green", var,TCDS)].min()
        ymin = ymin - (ymean - ymin)/5
        ymax = df[("green", var,TCDS)].max()
        ymax = ymax + (ymax-ymean)/5


        hcorr = ROOT.TH2F("corr", "corr", 40, xmin, xmax, 40, ymin, ymax)
        
        for chname, chgr in df.groupby("ch"):
            print chname
            hcorr.Fill(chgr[("blue", var,TCDS)].loc[(chname, fed)],  chgr[("green", var,TCDS)].loc[(chname,fed)]) 
            
        hcorr.Draw("colz")
        hcorr.SetTitle("")


        hcorr.GetXaxis().SetTitle("blue " + vars[k]+" "+dims[k])
        hcorr.GetYaxis().SetTitle("green "+ vars[k]+" "+dims[k])
        hcorr.GetZaxis().SetTitle("channels")
        hcorr.GetZaxis().SetTitleOffset(1.2)
        ROOT.gStyle.SetOptStat(0)
        label = TextAuto(ROOT.gPad, "TCDS = %f MHz" % TCDSmean[t], align = 31)
        if fed: flabel = TextAuto(ROOT.gPad, "FED = %d" % fed, align = 11)
        Frame(ROOT.gPad)
        c1.Update()
        c1.Modified()


        hcorr1 = ROOT.TH2F("corr1", "corr1", 40, xmin, xmax, 40, ymin, ymax)
        
        for chname, chgr in df[df["side"] == 1].groupby("ch"):
            print chname
            hcorr1.Fill(chgr[("blue", var,TCDS)].loc[(chname, fed)],  chgr[("green", var,TCDS)].loc[(chname,fed)]) 
            
        hcorr1.Draw("colz")
        hcorr1.SetTitle("")


        hcorr1.GetXaxis().SetTitle("blue " + vars[k]+" "+dims[k])
        hcorr1.GetYaxis().SetTitle("green "+ vars[k]+" "+dims[k])
        hcorr1.GetZaxis().SetTitle("channels")
        hcorr1.GetZaxis().SetTitleOffset(1.2)
        ROOT.gStyle.SetOptStat(0)
        label = TextAuto(ROOT.gPad, "TCDS = %f MHz" % TCDSmean[t], align = 31)
        if fed: flabel = TextAuto(ROOT.gPad, "FED = %d, side 1" % fed, align = 11)
        Frame(ROOT.gPad)
        c1.Update()
        c1.Modified()

        c1.SaveAs("/eos/home-c/camendol/www/LaserTiming/bg_t_vs_T/corr_fed%d_side1_%s_TCDS%d.pdf" %( fed, var, t))
        c1.SaveAs("/eos/home-c/camendol/www/LaserTiming/bg_t_vs_T/corr_fed%d_side1_%s_TCDS%d.png" %( fed, var, t))


        hcorr0 = ROOT.TH2F("corr0", "corr0", 40, xmin, xmax, 40, ymin, ymax)
        
        for chname, chgr in df[df["side"] == 0].groupby("ch"):
            print chname
            hcorr0.Fill(chgr[("blue", var,TCDS)].loc[(chname, fed)],  chgr[("green", var,TCDS)].loc[(chname,fed)]) 
            
        hcorr0.Draw("colz")
        hcorr0.SetTitle("")


        hcorr0.GetXaxis().SetTitle("blue " + vars[k]+" "+dims[k])
        hcorr0.GetYaxis().SetTitle("green "+ vars[k]+" "+dims[k])
        hcorr0.GetZaxis().SetTitle("channels")
        hcorr0.GetZaxis().SetTitleOffset(1.2)
        ROOT.gStyle.SetOptStat(0)
        label = TextAuto(ROOT.gPad, "TCDS = %f MHz" % TCDSmean[t], align = 31)
        if fed: flabel = TextAuto(ROOT.gPad, "FED = %d, side 0" % fed, align = 11)
        Frame(ROOT.gPad)
        c1.Update()
        c1.Modified()

        c1.SaveAs("/eos/home-c/camendol/www/LaserTiming/bg_t_vs_T/corr_fed%d_side0_%s_TCDS%d.pdf" %( fed, var, t))
        c1.SaveAs("/eos/home-c/camendol/www/LaserTiming/bg_t_vs_T/corr_fed%d_side0_%s_TCDS%d.png" %( fed, var, t))

