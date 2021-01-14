for iov in /afs/cern.ch/work/c/camendol/LaserIOVs/2018/B/*
do 
if [ ${iov: -8} == "_610.txt" ]
then
iov=${iov%.*}
pattern=$(echo $iov | sed 's/_[0-9]\+$//')
echo $pattern
echo $pattern".txt"
for fed in $pattern"_"*; 
do 
cat $fed >> $pattern".txt"
done
fi
done
