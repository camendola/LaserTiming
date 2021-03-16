era=$1
laser="b"

for iov in /afs/cern.ch/work/c/camendol/LaserIOVs_new/2018/${era}/*
do 
if [[ $iov ==  *"IOV${laser}"* ]]
then
if [ ${iov: -8} == "_628.txt" ]
then
iov=${iov%.*}
pattern=$(echo $iov | sed 's/_[0-9]\+$//')
echo $pattern
echo $pattern".txt"
for fed in $pattern"_"*; 
do 
cat $fed >> $pattern".txt"
done
rm $pattern"_610.txt"
rm $pattern"_628.txt"
fi
fi
done
