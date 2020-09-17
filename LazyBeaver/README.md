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

Checkpointing and restarting is possible but somemwhat clunky at the moment - as this matures more documentation will be added.

## Results

With this code we can verify the following values for the Lazy Beaver function:

```
              +-------------------------------------------+
              |                 # of States               |
              +--------+------+------+------+------+------+
              |     2  |    3 |    4 |    5 |    6 |    7 |
+---------+---+========+======+======+======+======+======+
|   # of  | 2 ||     7 |   22 |   72 |  427 | 8407 |      |
| Symbols +---+--------+------+------+------+------+------+
|         | 3 ||    23 |  351 |      |      |      |      |
|         +---+--------+------+------+------+------+------+
|         | 4 ||    93 |      |      |      |      |      |
|         +---+--------+------+------+------+------+------+
|         | 5 ||   956 |      |      |      |      |      |
|         +---+--------+------+------+------+------+------+
|         | 6 || 33851 |      |      |      |      |      |
+---------+---+--------+------+------+------+------+------+
```

## Runtimes

These computation escalate quickly in runtime:
* 2x2, 3x2, 2x3 all compute in milliseconds using serial enumeration.
* 4x2 and 2x4 both compute in ~1s.
* 3x3 takes ~2 min serially.
* 5x2 takes ~10 min serially or ~2 min with 10x parallelism.
* 6x2 took __4.5 days__ running in parallel on a __48 core machine__.
* 2x6 took about __7 days__ running in parallel on a __48 core machine__.

