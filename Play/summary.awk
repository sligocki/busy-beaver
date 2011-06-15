NF > 0 && substr($0,1,1) != " " {
  tm = $0;
  next;
}
$0 ~ "success" {
  success = $0;
  next;
}
$1 == "True" {
  print tm;
  print success;
  print $0;
  print "";
}
