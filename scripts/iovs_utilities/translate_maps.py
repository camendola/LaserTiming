#!/usr/bin/env python3

# Translate python eta/phi maps into conddb_dumper-style maps (IOV like)
# Output:
#   ieta  iphi  region  value
# where region is 0 for EB.
# The translation of EE maps has not been tested yet.

import re
import sys

if len(sys.argv) == 1:
    print('Usage: %s <file1> [<file2> ... <fileN>]' % sys.argv[0])

def process_file(ifile):
    r = re.findall(r"\D(\d{3})\D", ' '+ifile+' ') 
    if len(r) > 1:
        print('Error: unable to guess FED number, getting', r)
    fed = int(r[0])
    region = 0
    if fed < 610:
        region = -1 # EE-
    if fed > 645:
        region = +1 # EE+
    cnt = 0
    phi = []
    for l in open(ifile):
        v = list(map(str.strip, l.split(',')))
        if cnt == 0:
            phi.append(0)
            phi.extend(list(map(int, v[1:])))
            cnt = 1
            continue
        for i in range(1, len(v)):
            tmp_phi, tmp_v = phi[i], -100
            if v[i] != '':
                tmp_v = v[i]
            print(v[0], tmp_phi, region, tmp_v)

for f in sys.argv[1:]:
    #print('# input file: ' + f)
    process_file(f)
    #print('\n')
