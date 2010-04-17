BEGIN {
  FS = "|"
  exitCode = 1
  total_count[1] = 0
  total_count[2] = 0
  total_count[3] = 0
  total_count[4] = 0
}
NF == 4 && $1 == 1 {
  n = split($4,counts," ")
  if (n == 4) {
    total_count[1] += counts[1]
    total_count[2] += counts[2]
    total_count[3] += counts[3]
    total_count[4] += counts[4]
  }
}
END {
  print total_count[1],total_count[2],total_count[3],total_count[4]
}
