{
  found = 0;
  for (i = 1; i <= NF; i++) {
    if (found == 0) {
      n = split($i,parts,"^")
      if (n == 2) {
        save_base = parts[1];
        save_expo = parts[2];
        found = 1;
      } else {
        printf(" %s",$i);
      }
    } else {
      n = split($i,parts,"^")
      if (n == 2) {
        cur_base = parts[1];
        cur_expo = parts[2];
        if (cur_base == save_base) {
          save_expo += cur_expo;
        } else {
          printf(" %s^%d",save_base,save_expo);
          save_base = cur_base;
          save_expo = cur_expo;
        }
      } else {
        printf(" %s^%d",save_base,save_expo);
        printf(" %s",$i);
        found = 0;
      }
    }
  }

  if (found == 1) {
    printf(" %s^%d",save_base,save_expo);
  }

  printf("\n");
}
