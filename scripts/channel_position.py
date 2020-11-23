import pandas as pd
import numpy as np
import sys
from array import array
import os.path
import argparse
import ecalic 

parser = argparse.ArgumentParser(description='Command line parser of plotting options')

parser.add_argument('--fed',     dest='fed',    type=int, help='fed',     default=610)
parser.add_argument('--ch',      dest='ch',     type=int, help='ch',      default=0)

args = parser.parse_args()

status = ecalic.xml('../elmonk/etc/data/ecalChannelStatus_run324773.xml',type='status').icCMS()
goodecal = status.iov.mask(status['ic']!=0).dropna(how='all')
goodchannels = goodecal["elecID"].tolist()

ecal = ecalic.icCMS().iov

ecal = ecal[(ecal['FED']    == args.fed) &
            (ecal['elecID'] == args.ch)]


print ("{: <5} {: >5}".format("iphi", ecal['iy'].values[0]))
print ("{: <5} {: >5}".format("ieta", ecal['ix'].values[0]))
print ("{: <5} {: >5}".format("side", ecal['side'].values[0]))
print ("{: <5} {: >5}".format("TT",   ecal['ccu'].values[0]))


if args.ch > -1:  print ("Is channel %d good? %s" % (args.ch, "Yes" if args.ch in goodchannels else "No"))
