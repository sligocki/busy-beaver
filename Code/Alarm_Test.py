#! /usr/bin/env python
#
# Alarm_Test.py
#
"""
Test the Python alarms...
"""

from Alarm import ALARM, AlarmException

try:
  ALARM.set_alarm(1.5)

  count = 0
  while True:
    count += 1
    if (count % 200000 == 0):
      print count

except AlarmException:
  print "loop interrupted at",count
