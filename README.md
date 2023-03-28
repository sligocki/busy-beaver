Collection of Busy Beaver search tools developed by Shawn and Terry Ligocki.

This README tends to go out of date, so the best documentation is by running a program with `-h`.

The main use of this codebase is to enumerate an entire class of TMs(ex: all 5 state, 2 symbol TMs), iteratively apply deciders to them and reduce that set of TMs over time.

The second use is to analyze individual machines for human analysis and record confirmations.

## General overview

Top level directories:

* `Code/` - OG Python codebase. This is where most things are.
* `Machines/` - Various lists of champions and other interesting TMs.
* `Tools/` - Assortment of old tools to help facilitate running filters. At this point I think `filter.sh` is probably the only one of use.
* `cpp/` - C++ rewrites of a few things (Direct Simulation, Lin Recurrence, Lazy Beaver). About 1000x faster than the Python versions! These are imperative for beginning an enumeration these days!
* `rust/` - Start of some Rust experiments for deciders/tools. Nothing to see yet.


## Simulators

* `Code/Quick_Sim.py` - Simulate TM using tape compression and automated proof system. This is the standard simulator to run on machines you expect to halt (ex: record confirmations) or to see what patterns the computer can find. There are lots of options, but some of note are `--recursive` (allow level 2 proofs), `--block-size` (force a specific block size), `--verbose` (show everything it does), `--no-backsymbol` (turn off backsymbol-macro machine), `--no-steps` (turn off step calculation which is way faster for large TMs).
* `Code/Visual_Simulator` - Uses terminal graphics to visually simulate a TM.
* `Code/Curses_Sim.py` - Uses "curses" library for better terminal graphics.
* `Code/Direct_Simulator.py` - Directly simulate TM (no tape compression). This is rarely useful, but some TMs don't accelerate well, so useful to have.
* `cpp/direct_sim` - 1000x faster (C++) version of direct simulation.


## Deciders (single TM)

These are deciders that can be run on a single TM:

* `Code/Lin_Recur_Detect.py` - Decide Translated Cyclers / Lin Recurrence.
* `cpp/lin_recur` - 1000x faster C++ version of LR detection.
* `Code/CPS.py` - Decide CPS (Closed Position Set) proofs.
* `Code/CTL?.py` - Decide CTL (Closed Tape Language) proofs of certain limited types.


## Deciders (multiple TMs)

These decider scripts can be applied to a file of TMs. See also "Data formats" section.

* `Code/Enumerate.py` - Generates and enumerates all Turing Machines of a give class (in TNF) and runs them through the Reverse_Engineer, Lin_Recur, CTL, Quick_Sim deciders. It can also take an `--infile` and filter a set of TMs. This is the main way to apply the Lin_Recur and Quick_Sim deciders to a file full of TMs.
* `Code/Reverse_Engineer_Filter.py` - Check a simple condition of transition-table that assures some TMs will never halt. Extremely fast.
* `Code/Backtracking_Filter.py` - Decider that searches backwards from halting configurations in order to prove that they are unreachable.

As described above:
* `Code/CPS_Filter.py`
* `Code/CTL_Filter.py`


## Data formats

These files support both text (One TM in standard notation per line) and our custom protobuf binary format as inputs. They generally output only in protobuf format. There is also a little support for bbchallenge.org seed id format. There are a variety of tools for working with output files:

* `Code/IO_Convert.py` - Convert between formats.
* `Code/IO_Categorize.py` - Split output file into different files for each type (halting, proven infinite, unknown)
* `Code/IO_Count.py` - Count # records in a file quickly.
* `Code/TM_Analyze.py` - Show summary stats about an output file.
* `Code/Read_Record.py` - See results for one specific TM in a file.
* `Code/TM_Print.py` - Print TM transition table in visual table format.


## Misc

* `Code/Adjacent.py` - Enumerate all machines adjacent to a given one. Ex: to explore the neighborhood of a successful machine.
* `Code/Count.py` - Count the number of TMs represented by each machine which is in tree normal form. When run over all machines in TNF, this should sum up to the total number of machines (QS-1) * (2QS)^(QS-2).
* `Code/Multiple_Halt_Find.py` - Provide statistics for how many machines have multiple halts and how many. Useful to know how likely it is that more machines will be created if one of the halts is reached.
* `Code/Random_Sample.py` - Samples a specified number of machines (lines really) from a specified file. Useful when trying to examine (or test more thoroughly) an extremely large population to get an idea for what might work, what the composition of the population is, etc.
* `Code/TNF.py` - Convert a TM into TNF (Tree Normal Form).
