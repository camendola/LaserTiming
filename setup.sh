cd /afs/cern.ch/user/c/camendol/elmonk
sed -i 's%clang8%gcc9%g' setup.sh
source setup.sh 
sed -i 's%gcc9%clang8%g' setup.sh
cd /afs/cern.ch/user/c/camendol/LaserTiming
export PYTHONPATH=$PYTHONPATH:/afs/cern.ch/user/c/camendol/recal/lib
