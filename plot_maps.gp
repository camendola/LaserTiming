# plot dump files from laser timing sequences
# [requires `paste' utility, in debian from the `coreutiles' package]
# to prepare the files (in fish shell), supposing they are in the directory `319579':
#   - rename them preserving the ordering, i.e. sequence 2 before 10
#     (`mv' errors on most of the files are harmless)
#   for i in 319579/**txt; mv $i (echo $i | sed -E 's/_([0-9])\.txt/_0\1\.txt/'); end
#   - dump the maps in a format suitable for easy comparisons and plotting
#   for i in (seq 00 27); ./translate_maps.py 319579/**_(printf %02d $i).txt | sort -u -gk 2 -gk 1 ; echo -e "\n"; end > maps_run319579_27seq.dat
#   - enjoy
#   gnuplot plot_maps.gp
#
# N.B.: sequence 27 is excluded from the comparison as incomplete, and
# gnuplot "with image" option screws up if the input matrix has only
# some of the row/columns values (workarounds are not worth the effort)

reset

ifile = 'maps_run319579_27seq.dat'

load 'moreland.pal'

set auto fix

set ylabel 'ieta'
set xlabel 'iphi'

set cbrange [-0.2:0.2]

set table 'tmp_izero.dat'
p ifile u 1:2:3:4 index 0 with table
unset table
do for [i=1:26] {
        print 'plotting sequence '.i.' - sequence 0... press any key to continue'
        set table 'tmp_i.dat'
        p ifile u 1:2:3:4 index i with table
        unset table
        system('paste tmp_i.dat tmp_izero.dat > tmp_i_izero.dat')
        p 'tmp_i_izero.dat' u 2:1:($4 - $8) not w image
        pause mouse any
}
