import time


class Timer:
  """Timer for use in `with` statement for protobufs with `elapsed_time_us` field:

  with Timer(foo):
    ...
  print("Elapsed time in µs:", foo.elapsed_time_us)
  """
  def __init__(self, message):
    self.message = message

  def __enter__(self):
    self.start_time = time.time()
    return self

  def __exit__(self, *args):
    self.end_time = time.time()
    self.elapsed_s = self.end_time - self.start_time
    # Convert to µs integer.
    self.message.elapsed_time_us = int(self.elapsed_s * 1_000_000)
