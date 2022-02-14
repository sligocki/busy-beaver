#! /usr/bin/env python3
#
# Alarm_Test.py
#
"""
Test the Python alarms...
"""

from mpi4py import MPI

import signal

class AlarmException(Exception):
  """An exception to be tied to a timer running out."""

def alarm_handler(signum, frame):
  raise AlarmException("Timeout!")

# Attach the alarm signal to the alarm exception.
#   so signal.alarm will cause a catchable exception.
signal.signal(signal.SIGALRM, alarm_handler)

try:
  signal.alarm(1)

  count = 0
  while count < 12000000:
    count += 1
    if (count % 400000 == 0):
      print(count)

  print("loop completed - doh...")

except AlarmException:
  print("loop interrupted at",count)
