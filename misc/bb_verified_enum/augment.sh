set -u
set -e
set -x

domain=$1

infile=input/BB${domain}_verified_enumeration.csv
outdir=output/bb${domain}/
halt_tms=${outdir}/halt.txt
halt_results=${outdir}/halt.out.txt
outfile=${outdir}/BB${domain}_verified_enumeration_augmented.csv
certfile=${outdir}/cert_sligocki.txt
mkdir -p $outdir

awk -F, '$2 == "halt" {print $1}' $infile > $halt_tms

time ../cpp/direct_sim_all $halt_tms 100000000 $halt_results

time python merge_halt.py $infile $halt_results $outfile

echo sligocki > $certfile
cat $outfile >> $certfile
# Delete trailing newline
truncate -s -1 $certfile

time shasum -a 256 $certfile