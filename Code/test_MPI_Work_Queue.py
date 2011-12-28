"""
Test for "MPI_Work_Queue.py".

To test, run:
$ mpirun -np 8 python Code/test_MPI_Work_Queue.py
"""

import MPI_Work_Queue

if __name__ == "__main__":
  assert MPI_Work_Queue.num_proc > 1, "Must have at least 2 processes."
  if MPI_Work_Queue.rank == 0:
    master = MPI_Work_Queue.Master()
    for n in range(100):
      master.push_job(n)
    success = master.run_master()
    if not success:
      sys.exit(1)
  else:
    queue = MPI_Work_Queue.MPI_Worker_Work_Queue(master_proc_num=0)
    while True:
      job = queue.pop_job()
      if job == None:
        break
      print "Process %d recieved job %d" % (MPI_Work_Queue.rank, job)
