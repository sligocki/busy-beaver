import sys, time

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

class Single_Process_Work_Queue(Work_Queue):
  """Single process implementation of Work_Queue using a single queue."""

  def __init__(self, pout = sys.stdout, sample_time = 1.0):
    self.queue = []
    self.pout = pout
    self.sample_time = sample_time
    self.last_time = time.time()
    self.min_queue = 0
    self.max_queue = 0

  def __getstate__(self):
    d = self.__dict__.copy()
    del d["pout"]
    return d

  def pop_job(self):
    self.queue_stats()

    if self.queue:
      return self.queue.pop()
    else:
      return None

  def push_job(self, job):
    self.queue_stats()

    return self.queue.append(job)

  def push_jobs(self, jobs):
    self.queue_stats()

    return self.queue.extend(jobs)

  def queue_stats(self):
    size = len(self.queue)
    self.min_queue = min(self.min_queue,size)
    self.max_queue = max(self.max_queue,size)

    cur_time = time.time()
    if cur_time - self.last_time >= self.sample_time:
      self.pout.write("Queue size: %d (%d %d)\n" % (size,self.min_queue,self.max_queue))
      self.last_time = cur_time
      self.min_queue = size
      self.max_queue = size
