{
  start = 1
  seek = 3
  if ($1 > 6) {
    seek = 2
  }
  for (i = seek; i <= NF; i++) {
    if ($i == $1) {
      found = 1
      for (j = 1; j < i; j++) {
        k = i+j-1
        if ($k != $j) {
          found = 0
          break
        }
      }
      if (found == 1) {
        start = i
        break
      }
    }
  }
  for (i = start; i <= NF; i++) {
    printf("%s ",$i)
  }
  printf("\n",$NF)
}
