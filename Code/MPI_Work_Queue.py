import sys

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
MAX_NUM_JOBS_PER_BATCH =  10

MAX_LOCAL_JOBS         =  20

# Worker code
class MPI_Worker_Work_Queue(Work_Queue.Work_Queue):
  """Work queue based on mpi4py MPI libary. Allows maintaining a global work
  queue for many processes possibly distributed across many machines."""

  def __init__(self, master_proc_num):
    self.master = master_proc_num
    self.local_queue = []  # Used to buffer up jobs locally.

  def pop_job(self):
    if self.local_queue:
      # Perform all jobs in the local queue first.
      return self.local_queue.pop()
    else:
      # When local queue is empty, request more work from the master.
      # TODO(shawn): If we pre-emptively request jobs we will need a new
      # request type to distingush workers which have no jobs and are thus
      # waiting and workers which are simply pre-emptively requesting new jobs.
      #print "Worker %d: Waiting for pop." % rank

      # Tell master that we are waiting.
      # Note: The contents of this message are ignored, only the fact that it
      # was sent and the tag matter.
      comm.send(None, dest=self.master, tag=WAITING_FOR_POP)
      # And wait for more work in response.
      self.local_queue += comm.recv(source=self.master, tag=POP_JOBS)
      if self.local_queue:
        return self.local_queue.pop()
      else:
        # If server sent us no work, we are done.
        return None

  def push_job(self, job):
    #print "Worker %d: Pushing job %r." % (rank, job)
    self.local_queue.append(job)
    self.send_extra()

  def push_jobs(self, jobs):
    self.local_queue += jobs
    self.send_extra()

  def send_extra(self):
    """Not for external use. Sends extra jobs back to master."""
    if len(self.local_queue) > MAX_LOCAL_JOBS:
      # TODO(shawn): Should we send the bottom jobs back to master instead of
      # the top jobs?
      extra_jobs = self.local_queue[MAX_NUM_JOBS_PER_BATCH:]
      self.local_queue = self.local_queue[:MAX_NUM_JOBS_PER_BATCH]
      comm.send(extra_jobs, dest=self.master, tag=PUSH_JOBS)


# Master code
class Master(object):
  """Only one process should create and MPI Master object and all workers
  Should refer to it. You can use push_job() to add initial jobs and then
  run_master() to run the select loop for listening for workers."""

  def __init__(self):
    self.master_queue = []

  def push_job(self, job):
    self.master_queue.append(job)

  def run_master(self):
    # States of all workers. False iff that worker is WAITING_FOR_POP.
    worker_state = [True] * num_proc
    worker_state[0] = None  # Proc 0 is not a worker.
    while True:
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
          # the queue.
          jobs_block = self.master_queue[:num_jobs_per_batch]
          self.master_queue = self.master_queue[num_jobs_per_batch:]
          rank_waiting = worker_state.index(False)
          #print "Master: Sent job %r to worker %d." % (job, rank_waiting)
          comm.send(jobs_block, dest=rank_waiting, tag=POP_JOBS)
          worker_state[rank_waiting] = True
          count += 1
          if count == increase_num_per_batch:
            num_jobs_per_batch += 1
