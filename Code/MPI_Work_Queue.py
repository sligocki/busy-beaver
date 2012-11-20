import sys, time

from mpi4py import MPI

import Work_Queue

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
num_proc = comm.Get_size()

# MPI tags. Values are arbitrary, but distinct.
PUSH_JOBS       = 1
WAITING_FOR_POP = 2
POP_JOBS        = 3

# Optimization parameters
MIN_NUM_JOBS_PER_BATCH =  10
MAX_NUM_JOBS_PER_BATCH =  25

MAX_LOCAL_JOBS         =  30

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

    # Stats
    self.jobs_popped = 0
    self.jobs_pushed = 0
    
    # Where we spend our time.
    self.get_time     = 0.0
    self.put_time     = 0.0
    # Time waiting to get at the end, where we don't actually get 
    # anything, just waiting for all other workers to finish.
    self.end_time     = 0.0
    self.compute_time = 0.0  # Rest of the time.

    self.last_time = time.time()

  def __getstate__(self):
    d = self.__dict__.copy()
    del d["pout"]
    return d

  def pop_job(self):
    self.save_stats()

    if self.local_queue:
      # Perform all jobs in the local queue first.
      self.jobs_popped += 1
      return self.local_queue.pop()
    else:
      # When local queue is empty, request more work from the master.
      # TODO(shawn): If we pre-emptively request jobs we will need a new
      # request type to distingush workers which have no jobs and are thus
      # waiting and workers which are simply pre-emptively requesting new jobs.
      #print "Worker %d: Waiting for pop." % rank
      #print "Worker %d: Popped %d, Pushed %d." % (rank, self.jobs_popped, self.jobs_pushed)

      now = time.time()
      self.compute_time += now - self.last_time
      self.last_time = now

      # Tell master that we are waiting.
      # Note: The contents of this message are ignored, only the fact that it
      # was sent and the tag matter.
      comm.send(None, dest=self.master, tag=WAITING_FOR_POP)
      # And wait for more work in response.
      self.local_queue += comm.recv(source=self.master, tag=POP_JOBS)

      if self.local_queue:
        now = time.time()
        self.get_time += now - self.last_time
        self.last_time = now

        self.jobs_popped += 1
        return self.local_queue.pop()
      else:
        now = time.time()
        self.end_time += now - self.last_time
        self.last_time = now

        # Output timings
        self.pout.write("Get     time: %6.2f\n" % self.get_time)
        self.pout.write("Put     time: %6.2f\n" % self.put_time)
        self.pout.write("Compute time: %6.2f\n" % self.compute_time)
        self.pout.write("End     time: %6.2f\n" % self.end_time)
        self.pout.write("Total   time: %6.2f\n" % self.get_time+self.put_time+self.compute_time+self.end_time)

        # If server sent us no work, we are done.
        return None

  def push_job(self, job):
    self.save_stats()

    #print "Worker %d: Pushing job %r." % (rank, job)
    self.jobs_pushed += 1
    self.local_queue.append(job)
    self.send_extra()

  def push_jobs(self, jobs):
    self.save_stats()

    self.jobs_pushed += len(jobs)
    self.local_queue += jobs
    self.send_extra()

  def send_extra(self):
    """Not for external use. Sends extra jobs back to master."""
    if len(self.local_queue) > MAX_LOCAL_JOBS:

      now = time.time()
      self.compute_time += now - self.last_time
      self.last_time = now

      extra_jobs = self.local_queue[:-MAX_NUM_JOBS_PER_BATCH]
      self.local_queue = self.local_queue[-MAX_NUM_JOBS_PER_BATCH:]
      comm.send(extra_jobs, dest=self.master, tag=PUSH_JOBS)

      now = time.time()
      self.put_time += now - self.last_time
      self.last_time = now

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
    while True:
      self.save_stats()
      self.print_stats()

      # Wait for a worker to push us work or request to pop work.
      comm.Probe(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG)

      # Update worker state.
      while comm.Iprobe(source=MPI.ANY_SOURCE, tag=WAITING_FOR_POP):
        status = MPI.Status()
        comm.recv(source=MPI.ANY_SOURCE, tag=WAITING_FOR_POP, status=status)
        rank_waiting = status.Get_source()
        worker_state[rank_waiting] = False
        #print "Master: Worker %d is waiting for a job: %r" % (rank_waiting, worker_state)

      # Collect all jobs pushed from workers.
      while comm.Iprobe(source=MPI.ANY_SOURCE, tag=PUSH_JOBS):
        self.master_queue += comm.recv(source=MPI.ANY_SOURCE, tag=PUSH_JOBS)

      # Quit when all workers are waiting for work.
      if not self.master_queue and True not in worker_state:
        #print "Master: All jobs waiting for work, shutting down."
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
          #print "Master: Sent job %r to worker %d." % (job, rank_waiting)
          comm.send(jobs_block, dest=rank_waiting, tag=POP_JOBS)
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
