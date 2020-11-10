# Full year: without first runs with constant temperature
python single_ch.py --rmin 313800 --fed 610 --ch 0 --show
## in ieta bins
python plot_histories.py --rmin 313800 --rmax 314750 --fed 610 --ietamax -1 --ietamin -10 --show
python plot_histories.py --rmin 313800 --rmax 314750 --fed 628 --ietamin 1  --ietamax 10 --show
for i in {610..627}
do
python plot_histories.py --rmin 313800 --rmax 314750 --fed $i --ietamax -1 --ietamin -10 
python plot_histories.py --rmin 313800 --rmax 314750 --fed $i --ietamax -11 --ietamin -20
python plot_histories.py --rmin 313800 --rmax 314750 --fed $i --ietamax -21 --ietamin -30
python plot_histories.py --rmin 313800 --rmax 314750 --fed $i --ietamax -31 --ietamin -40
python plot_histories.py --rmin 313800 --rmax 314750 --fed $i --ietamax -41 --ietamin -50
python plot_histories.py --rmin 313800 --rmax 314750 --fed $i --ietamax -51 --ietamin -60
done

for i in {629..645}
do
python plot_histories.py --rmin 313800 --rmax 314750 --fed $i --ietamin 1  --ietamax 10
python plot_histories.py --rmin 313800 --rmax 314750 --fed $i --ietamin 11 --ietamax 20
python plot_histories.py --rmin 313800 --rmax 314750 --fed $i --ietamin 21 --ietamax 30
python plot_histories.py --rmin 313800 --rmax 314750 --fed $i --ietamin 31 --ietamax 40
python plot_histories.py --rmin 313800 --rmax 314750 --fed $i --ietamin 41 --ietamax 50
python plot_histories.py --rmin 313800 --rmax 314750 --fed $i --ietamin 51 --ietamax 60
done

# Beginning of the year: constant APD/PN
python single_ch.py --rmin 313800 --rmax 314750 --fed 610 --ch 0 --show
# Collisions: long run
python single_ch.py --rmin 319579 --rmax 319579 --fed 610 --ch 0 --show

