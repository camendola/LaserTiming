import pandas as pd
import numpy as np
import sys
from array import array
import os.path
import argparse
import ecalic 

parser = argparse.ArgumentParser(description='Command line parser of plotting options')

parser.add_argument('--fed',     dest='fed',    type=int, help='fed',     default=610)
parser.add_argument('--ietamin', dest='ietamin',type=int, help='ietamin', default=None)
parser.add_argument('--ietamax', dest='ietamax',type=int, help='ietamax', default=None)
parser.add_argument('--iphimin', dest='iphimin',type=int, help='iphimin', default=None)
parser.add_argument('--iphimax', dest='iphimax',type=int, help='iphimax', default=None)
parser.add_argument('--TT',      dest='TT',     type=int, help='TT',      default=None)
parser.add_argument('--side',    dest='side',   type=int, help='side',    default=None)

args = parser.parse_args()

status = ecalic.xml('../elmonk/etc/data/ecalChannelStatus_run324773.xml',type='status').icCMS()
ecal = status.iov.mask(status['ic']!=0).dropna(how='all')
#ecal = ecalic.icCMS().iov


ecal["iy"] = (ecal['iy'] - 1).mod(20) + 1

if args.fed:     ecal = ecal[ecal['FED']== args.fed]
print(ecal)
if args.iphimin: ecal = ecal[ecal['iy'] > args.iphimin]
if args.ietamin: ecal = ecal[ecal['ix'] > args.ietamin]
if args.iphimax: ecal = ecal[ecal['iy'] < args.iphimax]
if args.ietamax: ecal = ecal[ecal['ix'] < args.ietamax]
if args.side:    ecal = ecal[ecal['side'] == side]
if args.TT:      ecal = ecal[ecal['ccu'] == TT]

print(ecal["elecID"].tolist())

