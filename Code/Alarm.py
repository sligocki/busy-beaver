#! /usr/bin/env python3
#
# Alarm.py
#
"""
A class to manipulate alarms and turn them into Exceptions.
"""

import signal

class AlarmException(Exception):
  """An exception to be tied to a timer running out."""

class Alarm(object):
  """Singleton class that takes care of setting and turning off timer."""
  def __init__(self):
    self.is_alarm_on = False

  def set_alarm(self, time):
    self.is_alarm_on = True
    signal.setitimer(signal.ITIMER_REAL,time)

  def cancel_alarm(self):
    self.is_alarm_on = False
    signal.setitimer(signal.ITIMER_REAL,0.0)

  def alarm_handler(self, signum, frame):
    if self.is_alarm_on:
      raise AlarmException("Timeout!")

# Singleton object
ALARM = Alarm()

# Attach the alarm signal to the alarm exception.
#   so signalPlus.alarm will cause a catchable exception.
signal.signal(signal.SIGALRM, ALARM.alarm_handler)
