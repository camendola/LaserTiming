import pandas as pd
import numpy as np
import sys
from array import array
import os.path
import argparse
import ecalic 

parser = argparse.ArgumentParser(description='Command line parser of plotting options')

parser.add_argument('--fed',     dest='fed',    type=int, help='fed',     default=610)
parser.add_argument('--ietamin', dest='ietamin',type=int, help='ietamin', default=-999)
parser.add_argument('--ietamax', dest='ietamax',type=int, help='ietamax', default=-999)
parser.add_argument('--iphimin', dest='iphimin',type=int, help='iphimin', default=-1)
parser.add_argument('--iphimax', dest='iphimax',type=int, help='iphimax', default=-1)
parser.add_argument('--TT',      dest='TT',     type=int, help='TT',      default=-1)
parser.add_argument('--side',    dest='side',   type=int, help='side',    default=-1)
parser.add_argument('--ch',      dest='ch',     type=int, help='ch',      default=-1)

args = parser.parse_args()

status = ecalic.xml('../elmonk/etc/data/ecalChannelStatus_run324773.xml',type='status').icCMS()
ecal = status.iov.mask(status['ic']!=0).dropna(how='all')
ecal["iy"] = (ecal['iy'] - 1).mod(20) + 1

ecal = ecal[ecal['FED']== args.fed]

if args.iphimin > -1:   ecal = ecal[ecal['iy']   >= args.iphimin]
if args.ietamin > -999: ecal = ecal[ecal['ix']   >= args.ietamin]
if args.iphimax > -1:   ecal = ecal[ecal['iy']   <= args.iphimax]
if args.ietamax > -999: ecal = ecal[ecal['ix']   <= args.ietamax]
if args.side    > -1:   ecal = ecal[ecal['side'] == args.side]
if args.TT      > -1:   ecal = ecal[ecal['ccu']  == args.TT]


print(ecal["elecID"].tolist())
if args.ch > -1:  print ("channel %d in selecton" % args.ch if args.ch in ecal["elecID"].tolist() else "channel %d not in selection" % args.ch)
