# Lazy Beaver

Custom code to search for Lazy Beaver numbers.

```
LB(n, m) = min { k | does not exist an n state, m symbol TM which runs for exactly k steps before halting }
```

We search for Lazy Beavers naively by enumerate Turing Machines in Tree Normal Form and running each for a fixed number of steps noting the halt times.

## Dependencies

This code depends on cmake, C++17 and python3.

## Building

In order to build, run:

```bash
cmake .
make
```

## Running

There are two version of the enumeration. Serial code and parallel code. The serial version can be run as:

```
./lazy_beaver_enum 4 2 100 4x2_witness_file.txt
```

Which will enumerate all 4 state, 2 symbol TMs and run them up to 100 steps. It saves example TMs which "witness" each distinct num steps run into `4x2_witness_file.txt`.

The parallel version can be run as:

```
./enum_local_parallel.sh 5 2 6 500 10
```

Which will enumerate all 5 state, 2 symbol TMs serially for 6 steps, collect all non-halting machines and split them randomly 10 ways and then run 10 processes in parallel extending each of those partial enumerations out to 500 steps.
