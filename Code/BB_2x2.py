#!/usr/bin/env python3
import argparse
import sys

import IO
import Work_Queue
from Enumerate import Enumerator, enum_initial_tms
from Pipeline import Pipeline, SimulatorDecider, RevEngDecider, LinRecurDecider

def main():
    parser = argparse.ArgumentParser(description="Run BB(2,2) pipeline.")
    parser.add_argument("outfile", help="Output protobuf file.")
    args = parser.parse_args()

    pipeline = Pipeline([
        RevEngDecider(),
        SimulatorDecider(),
        LinRecurDecider(127),
    ])
    
    import optparse
    # Mock options required by Enumerate and Simulator
    options = optparse.Values({
        "states": 2,
        "symbols": 2,
        "infilename": None,
        "first_1rb": True,
        "max_transitions": None,
        "allow_no_halt": False,
        "only_reversible": False,
        "save_freq": 100_000,
        "randomize": False,
        "seed": None,
        "num_enum": None,
        "debug_print_current": False,
        
        # Macro_Simulator & Block_Finder options
        "max_loops": 1000,
        "time": 15.0,
        "tape_limit": 50,
        "max_steps_per_macro": 10_000,
        "lin_steps": 127,
        "lin_min": False,
        "reverse_engineer": True,
        "ctl": True,
        "run_sim": True,
        "max_block_size": 5,
        "block_size": None,
        "block_mult": 0,
        "max_block_mult": 2,
        "verbose_block_finder": False,
        "verbose_simulator": False,
        
        # Simulator & Prover options
        "compute_steps": True,
        "prover": True,
        "html_format": False,
        "full_reps": False,
        "verbose_prover": False,
        "recursive": False,
        "limited_rules": False,
        "exp_linear_rules": False,
        "exp_meta_linear_rules": False,
        "max_prover_configs": 100_000,
        "max_num_reps": 10,
        "backsymbol": True,
        
        # Other standard option
        "outfilename": args.outfile
    })

    stack = Work_Queue.Basic_LIFO_Work_Queue()
    pout = sys.stdout

    with IO.Proto.Writer(options.outfilename) as writer:
        enumerator = Enumerator(options, stack, writer, pout, pipeline=pipeline)
        
        # Push initial TMs
        for tm_record in enum_initial_tms(options):
            stack.push_job(tm_record)
            
        enumerator.continue_enum()
        enumerator.save()

if __name__ == "__main__":
    main()
