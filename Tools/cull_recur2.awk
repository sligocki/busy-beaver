BEGIN {
  found = 0;
}
{
  n = split($0,parts,"|");
  print length(parts[1]);
  found = 1;
  next;
}
END {
  if (found == 0) {
    print 0
  }
}
