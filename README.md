Studies on laser dst files usign [elmonk](https://gitlab.cern.ch/blenzi/elmonk) utilities

```
git clone ssh://git@gitlab.cern.ch:7999/fcouderc/elmonk.git
cd elmonk
source etc/scripts/setup.sh # add -c if you want to use CMSSW on lxplus
pip3 install -e . --no-index --user # remove --user if you are in a virtual environment
cd ..
git clone git@github.com:camendola/LaserTiming.git
cd LaserTiming
source setup.sh 
```