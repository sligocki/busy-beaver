BEGIN {
  FS = "|"
  exitCode = 1
}
NF == 4 && $1 == 1 {
  n = split($4,counts," ")
  if (n == 4) {
    exitCode = 0
  }
}
END {
  exit exitCode
}
