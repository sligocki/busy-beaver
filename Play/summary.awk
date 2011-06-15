NF > 0 && substr($0,1,1) != " " {
  tm = $0;
  next;
}
substr($2,1,2) == "((" {
  stripped = $0;
  next
}
substr($1,1,1) == "[" {
  sequence = $0;
  next
}
$0 ~ "success" {
  success = $0;
  next;
}
$1 == "True" {
  print tm;
  print stripped;
  print sequence;
  print success;
  print "";
}
