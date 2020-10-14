reset

ifile = 'dump_EcalTimeCalibConstants_Run2_2018.dat'

region = '98ch'

def_cut(r) = r eq '98ch' ? "cut = \"$3 == 0 && $1 >= -5 && $1 < 0 && $2 <= 20\"" : r eq 'EEp' ? "cut = \"$3 == +1\"" : r eq 'EEm' ? "cut = \"$3 == -1\"" : "cut = \"$3 == 0\""
eval def_cut(region)

since = system("grep '#' ".ifile." | awk '{print $5}' | tr '\n' ' '")

set print "out_iov_".region.".dat"
set table 'izero_'.region.'.dat'
p ifile u 1:2:3:4 index 0 with table
unset table
set print "out_iov_relative_".region.".dat"
do for [i=0:words(since)-1] {
	set table 'i_'.region.'.dat'
	p ifile u 1:2:3:4 index i with table
	unset table
	system('paste i_'.region.'.dat izero_'.region.'.dat > i_izero_'.region.'.dat')
	stats 'i_izero_'.region.'.dat' u (@cut ? $4      : NaN) name "i" nooutput
	stats 'i_izero_'.region.'.dat' u (@cut ? $4 - $8 : NaN) name "diff" nooutput
	print word(since, i + 1), ' ', i_mean, i_stddev, diff_mean, diff_stddev, i_records
}
set print
