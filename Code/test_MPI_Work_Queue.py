#! /usr/bin/env python
"""
Unit test for "MPI_Work_Queue.py".
"""

import MPI_Work_Queue

if __name__ == "__main__":
  queue = MPI_Work_Queue.MPI_Work_Queue()
  if MPI_Work_Queue.rank == 1:
    for n in range(100):
      queue.push_job(n)
  while True:
    job = queue.pop_job()
    if job == None:
      break
    print "Process %d recieved job %d" % (MPI_Work_Queue.rank, job)
