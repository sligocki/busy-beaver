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

  def __init__(self):
    self.queue = []

  def pop_job(self):
    if self.queue:
      return self.queue.pop()
    else:
      return None

  def push_job(self, job):
    return self.queue.append(job)

  def push_jobs(self, jobs):
    return self.queue.extend(jobs)
