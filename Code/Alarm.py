#! /usr/bin/env python3
#
# Alarm.py
#
"""
A class to manipulate alarms down the the millisecond level if SignalPlus
is available...
"""

import signal

# SignalPlus allows millisecond alarm, but needs to be compiled seperately.
# Fall back to inferior signal.alarm if we have to.
try:
  from signalPlus import alarm
  using_signal_plus = True
except ImportError:
  import sys; print("Alarm.py: Failed to import signalPlus, falling back to signal.", file=sys.stderr)
  from signal import alarm
  using_signal_plus = False

class AlarmException(Exception):
  """An exception to be tied to a timer running out."""

class Alarm(object):
  """Singleton class that takes care of setting and turning off timer."""
  def __init__(self):
    self.is_alarm_on = False

  def set_alarm(self, time):
    if not using_signal_plus:
      time = int(time)
    self.is_alarm_on = True
    alarm(time)

  def cancel_alarm(self):
    self.is_alarm_on = False
    alarm(0)

  def alarm_handler(self, signum, frame):
    if self.is_alarm_on:
      raise AlarmException("Timeout!")

ALARM = Alarm()

# Attach the alarm signal to the alarm exception.
#   so signalPlus.alarm will cause a catchable exception.
signal.signal(signal.SIGALRM, ALARM.alarm_handler)
