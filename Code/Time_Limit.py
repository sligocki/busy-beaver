import threading

class TimeLimit:
    """Explicit timeout token. Created by Enumerate, propagated through the machine hierarchy."""
    def __init__(self):
        self._timed_out = False
        self._timer = None

    def start(self, seconds):
        """Start a timer to expire this limit after `seconds`. No-op if seconds == 0.0."""
        if seconds != 0.0:
            self._timer = threading.Timer(seconds, self.expire)
            self._timer.start()

    def cancel(self):
        """Cancel the timer if one was started."""
        if self._timer is not None:
            self._timer.cancel()

    def expire(self):
        self._timed_out = True

    @property
    def timed_out(self):
        return self._timed_out
