import sys, time, collections

class Work_Queue(object):
  """A generic interface for sending and recieving work."""

  def pop_job(self):
    """Take a job off of the queue. The implementation may buffer up
    several jobs from a central server if this is a distributed computation.
    Returns None if there are no jobs to pop."""
    raise NotImplemented

  def push_job(self, job):
    """Add a job into the queue. The implementation may push these jobs back
    to a central server if there are enough local jobs buffered."""
    raise NotImplemented

  def push_jobs(self, jobs):
    """Add several jobs into the queue at once."""
    raise NotImplemented

  def print_stats(self):
    """Hook for printing stats, default implemenation does nothing."""
    pass

class Basic_LIFO_Work_Queue(Work_Queue):
  """Single process implementation of Work_Queue using stack-order."""

  def __init__(self):
    self.queue = []
    self.size_queue = 0
    self.min_queue  = 0
    self.max_queue  = 0

  def pop_job(self):
    self.save_stats()

    if self.queue:
      return self.queue.pop()
    else:
      return None

  def push_job(self, job):
    self.save_stats()

    return self.queue.append(job)

  def push_jobs(self, jobs):
    self.save_stats()

    return self.queue.extend(jobs)

  def save_stats(self):
    self.size_queue = len(self.queue)
    self.min_queue  = min(self.min_queue, self.size_queue)
    self.max_queue  = max(self.max_queue, self.size_queue)

  def get_stats(self):
    size_queue = self.size_queue
    min_queue  = self.min_queue
    max_queue  = self.max_queue

    self.size_queue = len(self.queue)
    self.min_queue  = self.size_queue
    self.max_queue  = self.size_queue

    return (size_queue, min_queue, max_queue)


class Basic_FIFO_Work_Queue(Work_Queue):
  """Single process implementation of Work_Queue using queue-order."""

  def __init__(self):
    self.queue = collections.deque()

  def pop_job(self):
    if self.queue:
      return self.queue.popleft()
    else:
      return None

  def push_job(self, job):
    return self.queue.append(job)

  def push_jobs(self, jobs):
    return self.queue.extend(jobs)
