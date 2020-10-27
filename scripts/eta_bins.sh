#Full year
#python single_ch.py --fed 610 --ch 0
#Beginning of the year: constant APD/PN
#python single_ch.py --rmin 314163 --rmax 314750 --fed 610 --ch 0
#python single_ch.py --rmin 313800 --rmax 314750 --fed 610 --ch 0
## in ieta bins
#for i in {611..627}
#do
#python eta_bins.py --rmin 313800 --rmax 314750 --fed $i --ietamax -1 --ietamin -10 
#python eta_bins.py --rmin 313800 --rmax 314750 --fed $i --ietamax -11 --ietamin -20
#python eta_bins.py --rmin 313800 --rmax 314750 --fed $i --ietamax -21 --ietamin -30
#python eta_bins.py --rmin 313800 --rmax 314750 --fed $i --ietamax -31 --ietamin -40
#python eta_bins.py --rmin 313800 --rmax 314750 --fed $i --ietamax -41 --ietamin -50
#python eta_bins.py --rmin 313800 --rmax 314750 --fed $i --ietamax -51 --ietamin -60
#done

for i in {629..645}
do
python eta_bins.py --rmin 313800 --rmax 314750 --fed $i --ietamin 1  --ietamax 10
python eta_bins.py --rmin 313800 --rmax 314750 --fed $i --ietamin 11 --ietamax 20
python eta_bins.py --rmin 313800 --rmax 314750 --fed $i --ietamin 21 --ietamax 30
python eta_bins.py --rmin 313800 --rmax 314750 --fed $i --ietamin 31 --ietamax 40
python eta_bins.py --rmin 313800 --rmax 314750 --fed $i --ietamin 41 --ietamax 50
python eta_bins.py --rmin 313800 --rmax 314750 --fed $i --ietamin 51 --ietamax 60
done
#python single_ch.py --rmin 319579 --rmax 319579 --fed 610 --ch 0
