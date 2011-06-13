BEGIN {
  found = 0;
}
NF > 0 && substr($0,1,1) != " " {
  n = split($0,parts,"|");
  mach_line = parts[1];
  found = 1;
  next;
}
NF == 1 && ($1 == "True" || $1 == "False") {
  if (found == 1) {
    if ($1 == "True") {
      print mach_line;
    }
    found = 0;
  } else {
    printf("%s found, line %d, without a TM\n",$1,NR);
  }
  next;
}
