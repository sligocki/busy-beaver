BEGIN {
  FS = "|"
  exitCode = 1
}
NF == 6 {
  n = split($1,lognum," ")
  if (lognum[1] == "1")
  {
    n = split($6,counts," ")
    if (n == 4) {
      exitCode = 0
    }
  }
}
END {
  exit exitCode
}
