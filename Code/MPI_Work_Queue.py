import sys, time

from mpi4py import MPI

import Work_Queue

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
num_proc = comm.Get_size()

# MPI tags. Values are arbitrary, but must be distinct.
PUSH_JOBS         = 1  # Workers pushing jobs back to master.
WAITING_FOR_POP   = 2  # Message workers send to master when waiting for jobs.
POP_JOBS          = 3  # Master pushes jobs back to workers.
REPORT_QUEUE_SIZE = 4  # Message workers send to master to report queue size.

# Optimization parameters
# TODO(shawn): These probably need to increase 5x2 case is spending 96% of time
# in communication.
MIN_NUM_JOBS_PER_BATCH = 10
MAX_NUM_JOBS_PER_BATCH = 1000

DEFAULT_MAX_LOCAL_JOBS    = 30
DEFAULT_TARGET_LOCAL_JOBS = 25

# Worker code
class MPI_Worker_Work_Queue(Work_Queue.Work_Queue):
  """Work queue based on mpi4py MPI libary. Allows maintaining a global work
  queue for many processes possibly distributed across many machines."""

  def __init__(self, master_proc_num, pout = sys.stdout, sample_time = 1.0):
    self.master = master_proc_num
    self.local_queue = []  # Used to buffer up jobs locally.
    self.size_queue = 0
    self.min_queue = 0
    self.max_queue = 0
    self.pout = pout

    # Parameters
    # Maximum queue size before pushing back to master.
    self.max_local_jobs = DEFAULT_MAX_LOCAL_JOBS
    # Queue size to go down to when pushing back to master.
    self.target_local_jobs = DEFAULT_TARGET_LOCAL_JOBS

    # Stats
    self.jobs_popped = 0
    self.jobs_pushed = 0
    
    # Where we spend our time.
    self.get_time     = 0.0
    self.put_time     = 0.0
    self.report_queue_time = 0.0
    # Time waiting to get at the end, where we don't actually get 
    # anything, just waiting for all other workers to finish.
    self.end_time     = 0.0
    self.compute_time = 0.0  # Rest of the time.

    self.last_time = time.time()

  def __getstate__(self):
    d = self.__dict__.copy()
    del d["pout"]
    return d

  def time_diff(self):
    now = time.time()
    diff = now - self.last_time
    self.last_time = now
    return diff

  def pop_job(self):
    self.save_stats()

    self._report_queue_size()

    if self.local_queue:
      # Perform all jobs in the local queue first.
      self.jobs_popped += 1
      return self.local_queue.pop()
    else:
      # When local queue is empty, request more work from the master.
      self.compute_time += self.time_diff()

      # Tell master that we are waiting.
      # Note: The contents of this message are ignored, only the fact that it
      # was sent and the tag matter.
      comm.send(None, dest=self.master, tag=WAITING_FOR_POP)
      # And wait for more work in response.
      jobs, self.max_local_jobs, self.target_local_jobs = \
          comm.recv(source=self.master, tag=POP_JOBS)
      self.local_queue += jobs

      if self.local_queue:
        self.get_time += self.time_diff()

        self.jobs_popped += 1
        return self.local_queue.pop()
      else:
        sefl.end_time += self.time_diff()

        # Output timings
        self.pout.write("Get     time: %6.2f\n" % self.get_time)
        self.pout.write("Put     time: %6.2f\n" % self.put_time)
        self.pout.write("Report Queue time: %6.2f\n" % self.report_queue_time)
        self.pout.write("Compute time: %6.2f\n" % self.compute_time)
        self.pout.write("End     time: %6.2f\n" % self.end_time)
        self.pout.write("Total   time: %6.2f\n" % (self.get_time+self.put_time+self.report_queue_time+self.compute_time+self.end_time))

        # If server sent us no work, we are done.
        return None

  def push_job(self, job):
    self.push_jobs([job])

  def push_jobs(self, jobs):
    self.save_stats()

    self.jobs_pushed += len(jobs)
    self.local_queue += jobs
    self._report_queue_size()
    self._send_extra()

  def _send_extra(self):
    """Not for external use. Sends extra jobs back to master."""
    if len(self.local_queue) > self.max_local_jobs:
      self.compute_time += self.time_diff()

      extra_jobs = self.local_queue[:-self.target_local_jobs]
      self.local_queue = self.local_queue[-self.target_local_jobs:]
      comm.send(extra_jobs, dest=self.master, tag=PUSH_JOBS)

      self.put_time += self.time_diff()

  def _report_queue_size(self):
    self.compute_time += self.time_diff()
    comm.send(len(self.local_queue), dest=self.master, tag=REPORT_QUEUE_SIZE)
    self.report_queue_time += self.time_diff()

  def save_stats(self):
    self.size_queue = len(self.local_queue)
    self.min_queue  = min(self.min_queue, self.size_queue)
    self.max_queue  = max(self.max_queue, self.size_queue)

  def get_stats(self):
    size_queue = self.size_queue
    min_queue  = self.min_queue
    max_queue  = self.max_queue

    self.size_queue = len(self.local_queue)
    self.min_queue  = self.size_queue
    self.max_queue  = self.size_queue

    return (size_queue, min_queue, max_queue, self.get_time, self.put_time)


# Master code
class Master(object):
  """Only one process should create and MPI Master object and all workers
  Should refer to it. You can use push_job() to add initial jobs and then
  run_master() to run the select loop for listening for workers."""

  def __init__(self, pout = sys.stdout, sample_time = 1.0):
    self.master_queue = []
    self.size_queue = 0
    self.min_queue = 0
    self.max_queue = 0
    self.pout = pout
    self.sample_time = sample_time
    self.start_time = time.time()
    self.last_time  = self.start_time

  def __getstate__(self):
    d = self.__dict__.copy()
    del d["pout"]
    return d

  def push_job(self, job):
    self.master_queue.append(job)

  def run_master(self):
    # States of all workers. False iff that worker is WAITING_FOR_POP.
    worker_state = [True] * num_proc
    worker_state[0] = None  # Proc 0 is not a worker.
    worker_queue_size = [None] * num_proc
    while True:
      self.save_stats()
      self.print_stats()

      # Wait for a worker to push us work or request to pop work.
      comm.Probe(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG)

      # Update worker state.
      while comm.Iprobe(source=MPI.ANY_SOURCE, tag=WAITING_FOR_POP):
        status = MPI.Status()
        # We ignore the actual message contents.
        comm.recv(source=MPI.ANY_SOURCE, tag=WAITING_FOR_POP, status=status)
        rank_waiting = status.Get_source()
        worker_state[rank_waiting] = False
        worker_queue_size[rank_waiting] = 0

      # Update our knowledge of worker queue sizes.
      while comm.Iprobe(source=MPI.ANY_SOURCE, tag=REPORT_QUEUE_SIZE):
        status = MPI.Status()
        size = comm.recv(source=MPI.ANY_SOURCE, tag=REPORT_QUEUE_SIZE,
                         status=status)
        rank = status.Get_source()
        worker_queue_size[rank] = size

      # Collect all jobs pushed from workers.
      while comm.Iprobe(source=MPI.ANY_SOURCE, tag=PUSH_JOBS):
        status = MPI.Status()
        jobs = comm.recv(source=MPI.ANY_SOURCE, tag=PUSH_JOBS, status=status)
        self.master_queue += jobs
        rank = status.Get_source()
        worker_queue_size[rank] -= len(jobs)

      # Quit when all workers are waiting for work.
      # TODO(shawn): If we pre-emptively request jobs we will need a new
      # request type to distingush workers which have no jobs and are thus
      # waiting and workers which are simply pre-emptively requesting new jobs.
      if not self.master_queue and True not in worker_state:
        for n in range(1, num_proc):
          # Sending [] tells workers there is no work left and they should quit.
          comm.send([], dest=n, tag=POP_JOBS)
        return True

      num_waiting = worker_state.count(False)

      if num_waiting > 0:
        queue_length = len(self.master_queue)

        num_jobs_per_batch = min(max(MIN_NUM_JOBS_PER_BATCH,
                                     queue_length / num_waiting),
                                 MAX_NUM_JOBS_PER_BATCH)

        increase_num_per_batch = (num_jobs_per_batch + 1) * num_waiting - queue_length

        # Send top job to first worker who requests it.
        count = 0
        while self.master_queue and False in worker_state:
          # TODO(shawn): Should we send jobs from the top rather than bottom of
          # the queue?
          jobs_block = self.master_queue[:num_jobs_per_batch]
          self.master_queue = self.master_queue[num_jobs_per_batch:]
          rank_waiting = worker_state.index(False)
          # Push jobs and allow worker queue to grow to 3/2 this size,
          # but push back excess at that point.
          comm.send((jobs_block, len(jobs_block) * 3/2, len(jobs_block)),
                    dest=rank_waiting, tag=POP_JOBS)
          worker_queue_size[rank_waiting] += len(jobs_block)
          
          worker_state[rank_waiting] = True
          count += 1
          if count == increase_num_per_batch:
            num_jobs_per_batch += 1

  def save_stats(self):
    self.size_queue = len(self.master_queue)
    self.min_queue  = min(self.min_queue, self.size_queue)
    self.max_queue  = max(self.max_queue, self.size_queue)

  def get_stats(self):
    size_queue = self.size_queue
    min_queue  = self.min_queue
    max_queue  = self.max_queue

    self.size_queue = len(self.master_queue)
    self.min_queue  = self.size_queue
    self.max_queue  = self.size_queue

    return (size_queue, min_queue, max_queue)

  def print_stats(self):
    cur_time = time.time()
    if cur_time - self.last_time >= self.sample_time:
      # if self.pout:
        # self.pout.write("Master queue info: %s\n" % (self.get_stats(),))
        # self.pout.flush()

      self.last_time = cur_time
