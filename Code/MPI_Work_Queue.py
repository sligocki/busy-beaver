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
UPDATE_MAX_QUEUE_SIZE = 5  # Master updating max queue size of workers.

# Optimization parameters
# TODO(shawn): These probably need to increase 5x2 case is spending 96% of time
# in communication.
MIN_NUM_JOBS_PER_BATCH = 10
MAX_NUM_JOBS_PER_BATCH = 25

DEFAULT_MAX_LOCAL_JOBS    = 30
DEFAULT_TARGET_LOCAL_JOBS = 25

# Worker code
class MPI_Worker_Work_Queue(Work_Queue.Work_Queue):
  """Work queue based on mpi4py MPI library. Allows maintaining a global work
  queue for many processes possibly distributed across many machines."""

  def __init__(self, master_proc_num, pout = sys.stdout):
    self.master = master_proc_num
    self.local_queue = []  # Used to buffer up jobs locally.
    self.pout = pout

    # Parameters
    # Maximum queue size before pushing back to master.
    self.max_queue_size = DEFAULT_MAX_LOCAL_JOBS
    # Queue size to go down to when pushing back to master.
    self.target_queue_size = DEFAULT_TARGET_LOCAL_JOBS

    # Stats
    self.jobs_popped = 0
    self.jobs_pushed = 0

    # Time and interval used for reporting queue size.
    self.last_report_time = time.time()
    self.report_interval = 10
    
    # Where we spend our time.
    self.get_time     = 0.0
    self.put_time     = 0.0
    self.report_queue_time = 0.0
    self.update_max_queue_size_time = 0.0
    # Time waiting to get at the end, where we don't actually get 
    # anything, just waiting for all other workers to finish.
    self.end_time     = 0.0
    self.compute_time = 0.0  # Rest of the time.

    # Used for keeping track of stat times above.
    self.last_stat_time = time.time()

  def __getstate__(self):
    d = self.__dict__.copy()
    del d["pout"]
    return d

  def time_diff(self):
    now = time.time()
    diff = now - self.last_stat_time
    self.last_stat_time = now
    return diff

  def pop_job(self):
    if self.local_queue:
      self._report_queue_size()
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
      self.local_queue += comm.recv(source=self.master, tag=POP_JOBS)

      if self.local_queue:
        self.get_time += self.time_diff()

        self.jobs_popped += 1
        return self.local_queue.pop()
      else:
        self.end_time += self.time_diff()
        self.print_stats()
        # If server sent us no work, we are done.
        return None

  def push_job(self, job):
    self.push_jobs([job])

  def push_jobs(self, jobs):
    self.jobs_pushed += len(jobs)
    self.local_queue += jobs
    self._update_max_queue_size()
    self._send_extra()
    self._report_queue_size()

  def print_stats(self):
    # Output timings
    self.pout.write("\n")
    self.pout.write("Get time             : %8.2f\n" % self.get_time)
    self.pout.write("Put time             : %8.2f\n" % self.put_time)
    self.pout.write("Report queue time    : %8.2f\n" % self.report_queue_time)
    self.pout.write("Update max queue time: %8.2f\n" %
                    self.update_max_queue_size_time)
    self.pout.write("Compute time         : %8.2f\n" % self.compute_time)
    self.pout.write("End time             : %8.2f\n" % self.end_time)
    self.pout.write("Total time           : %8.2f\n" % (
        self.get_time + self.put_time + self.report_queue_time +
        self.update_max_queue_size_time + self.compute_time + self.end_time))

    self.pout.flush()

  def _update_max_queue_size(self):
    self.compute_time += self.time_diff()
    while comm.Iprobe(source=self.master, tag=UPDATE_MAX_QUEUE_SIZE):
      self.max_queue_size = comm.recv(source=self.master,
                                      tag=UPDATE_MAX_QUEUE_SIZE)
      self.target_queue_size = self.max_queue_size * 3 // 4
    self.update_max_queue_size_time += self.time_diff()

  def _send_extra(self):
    """Not for external use. Sends extra jobs back to master."""
    if len(self.local_queue) > self.max_queue_size:
      self.compute_time += self.time_diff()

      extra_jobs = self.local_queue[:-self.target_queue_size]
      self.local_queue = self.local_queue[-self.target_queue_size:]
      comm.send(extra_jobs, dest=self.master, tag=PUSH_JOBS)

      self.put_time += self.time_diff()

  def _report_queue_size(self):
    if time.time() - self.last_report_time > self.report_interval:
      self.compute_time += self.time_diff()
      comm.send(len(self.local_queue), dest=self.master, tag=REPORT_QUEUE_SIZE)
      self.report_queue_time += self.time_diff()
      self.last_report_time = time.time()


# Master code
class Master(object):
  """Only one process should create and MPI Master object and all workers
  Should refer to it. You can use push_job() to add initial jobs and then
  run_master() to run the select loop for listening for workers."""

  def __init__(self, pout = sys.stdout):
    self.master_queue = []
    self.pout = pout

    # Time and interval used for updating worker max queue size.
    self.last_update_time = 0
    self.update_interval = 10  # Seconds

    # Where we spend our time.
    # Downtime waiting for message from workers.
    self.waiting_time = 0.0
    # Time spent receiving WAITING_FOR_POP messages from workers.
    self.receiving_waiting_for_pop_time = 0.0
    # Time spent receiving jobs from workers with PUSH_JOBS tag.
    self.receiving_jobs_time = 0.0
    # Time spent receiving REPORT_QUEUE_SIZE messages from workers.
    self.receiving_queue_size_time = 0.0
    # Time spent sending UPDATE_MAX_QUEUE_SIZE messages.
    self.update_max_queue_sizes_time = 0.0
    # Time spent sending jobs to workers with POP_JOBS tag.
    self.sending_jobs_time = 0.0

    # Used for keeping track of stat times above.
    self.last_stat_time  = time.time()

    self.last_report_time = time.time()
    self.report_interval = 120

  def __getstate__(self):
    d = self.__dict__.copy()
    del d["pout"]
    return d

  def time_diff(self):
    now = time.time()
    diff = now - self.last_stat_time
    self.last_stat_time = now
    return diff

  def push_job(self, job):
    self.master_queue.append(job)

  def print_stats(self):
    # Output timings
    self.pout.write("\n")
    self.pout.write("Waiting time               : %8.2f\n" % self.waiting_time)
    self.pout.write("WAITING_FOR_POP time       : %8.2f\n" %
                    self.receiving_waiting_for_pop_time)
    self.pout.write("Receiving jobs time        : %8.2f\n" %
                    self.receiving_jobs_time)
    self.pout.write("Receiving queue size time  : %8.2f\n" %
                    self.receiving_queue_size_time)
    self.pout.write("Update max queue sizes time: %8.2f\n" %
                    self.update_max_queue_sizes_time)
    self.pout.write("Sending jobs time          : %8.2f\n" %
                    self.sending_jobs_time)
    self.pout.write("Total time                 : %8.2f\n" %
                    (self.waiting_time + self.receiving_waiting_for_pop_time +
                     self.receiving_jobs_time + self.receiving_queue_size_time +
                     self.update_max_queue_sizes_time + self.sending_jobs_time))

    self.pout.flush()

  def run_master(self):
    # States of all workers. False iff that worker is WAITING_FOR_POP.
    worker_state = [True] * num_proc
    worker_state[0] = None  # Proc 0 is not a worker.
    worker_queue_size = [0] * num_proc
    update_requests = [None] * num_proc
    while True:
      # Wait for a worker to push us work or request to pop work.
      comm.Probe(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG)
      self.waiting_time += self.time_diff()

      # Update worker state.
      while comm.Iprobe(source=MPI.ANY_SOURCE, tag=WAITING_FOR_POP):
        status = MPI.Status()
        # We ignore the actual message contents.
        comm.recv(source=MPI.ANY_SOURCE, tag=WAITING_FOR_POP, status=status)
        rank_waiting = status.Get_source()
        worker_state[rank_waiting] = False
        worker_queue_size[rank_waiting] = 0
      self.receiving_waiting_for_pop_time += self.time_diff()

      # Collect all jobs pushed from workers.
      while comm.Iprobe(source=MPI.ANY_SOURCE, tag=PUSH_JOBS):
        self.master_queue += comm.recv(source=MPI.ANY_SOURCE, tag=PUSH_JOBS)
      self.receiving_jobs_time += self.time_diff()

      # Collect reported queue sizes from workers.
      while comm.Iprobe(source=MPI.ANY_SOURCE, tag=REPORT_QUEUE_SIZE):
        status = MPI.Status()
        size = comm.recv(source=MPI.ANY_SOURCE, tag=REPORT_QUEUE_SIZE,
                         status=status)
        rank = status.Get_source()
        worker_queue_size[rank] = size
      self.receiving_queue_size_time += self.time_diff()

      # Push out max queue sizes to workers.
      worker_queue_size[0] = len(self.master_queue)
      max_queue_size = max(sum(worker_queue_size) // len(worker_queue_size),
                           MAX_NUM_JOBS_PER_BATCH)
      target_queue_size = max_queue_size * 3 // 4
      if time.time() - self.last_update_time > self.update_interval:
        for rank in range(1, num_proc):
          if update_requests[rank]:
            update_requests[rank].Cancel()
            update_requests[rank].Wait()
          update_requests[rank] = comm.isend(max_queue_size, dest=rank,
                                             tag=UPDATE_MAX_QUEUE_SIZE)
        self.last_update_time = time.time()
      self.update_max_queue_sizes_time += self.time_diff()

      # Periodically report info.
      if time.time() - self.last_report_time > self.report_interval:
        self.print_stats()
        self.pout.write("%r\n" % worker_queue_size)
        self.last_report_time = time.time()

      # Quit when all workers are waiting for work.
      # TODO(shawn): If we pre-emptively request jobs we will need a new
      # request type to distinguish workers which have no jobs and are thus
      # waiting and workers which are simply pre-emptively requesting new jobs.
      if not self.master_queue and True not in worker_state:
        for n in range(1, num_proc):
          # Sending [] tells workers there is no work left and they should quit.
          comm.send([], dest=n, tag=POP_JOBS)
        self.print_stats()
        return True

      num_waiting = worker_state.count(False)

      if num_waiting > 0:
        queue_length = len(self.master_queue)

        # Number of jobs to send to each worker.
        num_jobs_per_batch = min(max(MIN_NUM_JOBS_PER_BATCH,
                                      queue_length // num_waiting),
                                  target_queue_size)

        # When we get down to the end, we want to send all jobs out.
        # This is the process num after which to send +1 jobs to workers.
        increase_count = (num_jobs_per_batch + 1) * num_waiting - queue_length

        # Send top job to first worker who requests it.
        count = 0
        while self.master_queue and False in worker_state:
          # TODO(shawn): Should we send jobs from the top rather than bottom of
          # the queue?
          jobs_block = self.master_queue[:num_jobs_per_batch]
          self.master_queue = self.master_queue[num_jobs_per_batch:]
          rank_waiting = worker_state.index(False)
          comm.send(jobs_block, dest=rank_waiting, tag=POP_JOBS)
          worker_queue_size[rank_waiting] += len(jobs_block)
          
          worker_state[rank_waiting] = True
          count += 1
          if count == increase_count:
            num_jobs_per_batch += 1
      self.sending_jobs_time += self.time_diff()
