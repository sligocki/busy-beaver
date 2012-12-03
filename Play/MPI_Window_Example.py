from mpi4py import MPI
import numpy

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
num_proc = comm.Get_size()


other_data = numpy.array([0])

if rank % 2 == 0:
  data = numpy.array([(rank + 1)**2])
  win = MPI.Win.Create(data, comm=comm)

  #data2 = numpy.array([-(rank + 1)])
  #win2 = MPI.Win.Create(data2, comm=comm)

  win.Fence()
  win.Get([other_data, MPI.INT], (rank + 1) % num_proc)
  win.Fence()

  print rank, data, other_data

  win.Free()
  #win2.Free()

else:
  data2 = numpy.array([(rank + 1) * 10])
  win2 = MPI.Win.Create(data2, comm=comm)

  win2.Fence()
  win2.Get([other_data, MPI.INT], (rank + 1) % num_proc)
  win2.Fence()

  print rank, data2, other_data

  win2.Free()
