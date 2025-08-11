"""
Test for "MPI_Work_Queue.py".

To test, run:
$ mpirun -np 8 python Code/test_MPI_Work_Queue.py
"""

import time

import MPI_Work_Queue

if __name__ == "__main__":
  assert MPI_Work_Queue.num_proc > 1, "Must have at least 2 processes."

  # Lower parameters
  MPI_Work_Queue.NUM_JOBS_PER_BATCH = 10

  if MPI_Work_Queue.rank == 0:
    master = MPI_Work_Queue.Master()
    for n in range(100 * MPI_Work_Queue.num_proc):
      master.push_job(n)
    success = master.run_master()
    if not success:
      sys.exit(1)
  else:
    queue = MPI_Work_Queue.MPI_Worker_Work_Queue(master_proc_num=0)
    file = open("test_MPI_Work_Queue_%d" % (MPI_Work_Queue.rank,),"w")
    while True:
      job = queue.pop_job()
      if job == None:
        file.close()
        break
      file.write("Process %d received job %d\n" % (MPI_Work_Queue.rank, job))
      time.sleep(0.0001 * job)
