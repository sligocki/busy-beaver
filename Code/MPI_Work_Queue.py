import sys

from mpi4py import MPI

import Work_Queue

comm = MPI.COMM_WORLD
rank = comm.Get_rank()

# MPI tags
PUSH_JOB = 1
WAITING_FOR_POP = 2
POP_JOB = 3

class MPI_Work_Queue(Work_Queue.Work_Queue):
  """Work queue based on mpi4py MPI libary. Allows maintaining a global work
  queue for many processes possibly distributed across many machines."""

  def pop_job(self):
    # Naive implementation just pulls every job directly from master.
    # TODO(shawn): We should buffer a larger number of jobs locally.
    #print "Worker %d: Waiting for pop." % rank
    comm.send(rank, dest=0, tag=WAITING_FOR_POP)
    job = comm.recv(source=0, tag=POP_JOB)
    #print "Worker %d: Recieved job %r." % (rank, job)
    return job

  def push_job(self, job):
    # Naive implementation just pushes every job directly to master.
    # TODO(shawn): We should store a local queue of tasks and only push to
    # master when we get too many jobs locally (or when master wants more jobs).
    #print "Worker %d: Pushing job %r." % (rank, job)
    comm.send(job, dest=0, tag=PUSH_JOB)


# Master code
if rank == 0:
  # Queue for storing jobs from all workers and waiting to be sent back to them.
  master_queue = []
  # States of all workers. False iff that worker is WAITING_FOR_POP.
  worker_state = [True] * comm.Get_size()
  worker_state[0] = None  # Proc 0 is not a worker.
  while True:
    # Update worker state.
    while comm.Iprobe(source=MPI.ANY_SOURCE, tag=WAITING_FOR_POP):
      rank_waiting = comm.recv(source=MPI.ANY_SOURCE, tag=WAITING_FOR_POP)
      worker_state[rank_waiting] = False
      #print "Master: Worker %d is waiting for a job: %r" % (rank_waiting, worker_state)

    # Collect all jobs pushed from workers.
    while comm.Iprobe(source=MPI.ANY_SOURCE, tag=PUSH_JOB):
      job = comm.recv(source=MPI.ANY_SOURCE, tag=PUSH_JOB)
      #print "Master: Recieved job %r." % job
      master_queue.append(job)

    # Quit when all workers are waiting for work.
    if not master_queue and True not in worker_state:
      #print "Master: All jobs waiting for work, shutting down."
      for n in range(1, comm.Get_size()):
        comm.send(None, dest=n, tag=POP_JOB)
      sys.exit()

    # Send top job to first worker who requests it.
    while master_queue and False in worker_state:
      job = master_queue.pop()
      rank_waiting = worker_state.index(False)
      #print "Master: Sent job %r to worker %d." % (job, rank_waiting)
      comm.send(job, dest=rank_waiting, tag=POP_JOB)
      worker_state[rank_waiting] = True
