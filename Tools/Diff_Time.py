#! /usr/bin/env python

import sys, time

begin_time = time.mktime(time.strptime(sys.argv[1],"%a %b %d %H:%M:%S %Z %Y"))
end_time   = time.mktime(time.strptime(sys.argv[2],"%a %b %d %H:%M:%S %Z %Y"))

print int(end_time - begin_time)
