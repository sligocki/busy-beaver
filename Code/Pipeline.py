import argparse

import Macro_Simulator
import Reverse_Engineer_Filter
import CTL_Filter
import Backtracking_Filter
import Halting_Lib
import IO
import io_pb2

class Pipeline:
    def __init__(self, deciders):
        self.deciders = deciders
        self.stats = {decider.name: 0 for decider in deciders}
        self.stats["Undecided"] = 0
        
    def run(self, tm_record, options, time_limit=None):
        """Try each decider in pipeline on this TM until one successfully decides it (or all fail)."""
        for decider in self.deciders:
            decider.apply(tm_record, options, time_limit)
            if not tm_record.is_unknown_halting():
                self.stats[decider.name] += 1
                break
        else:
            self.stats["Undecided"] += 1

    def print_stats(self, pout):
        pout.write(f"--- Pipeline Filter Stats ---\n")
        for name, count in self.stats.items():
            pout.write(f"  {name}: {count:_}\n")
        pout.write("-----------------------------\n")


class SimulatorDecider:
    def __init__(self, max_loops, block_size=None, recursive=False, name=None):
        self.max_loops = max_loops
        self.block_size = block_size
        self.recursive = recursive

        self.name = name or f"Simulator_{max_loops}"
        if block_size:
            self.name += f"_b{block_size}"
        if recursive:
            self.name += "_rec"

    def apply(self, tm_record, options, time_limit=None):
        # Override options based on our decider's explicit config
        options.max_loops = self.max_loops
        options.block_size = self.block_size
        options.recursive = self.recursive

        machine = tm_record.tm()
        if time_limit is not None:
            machine.time_limit = time_limit
            
        # Get wrapped macro-machine
        machine, best_block_size = Macro_Simulator.setup_macromachine(machine, options, tm_record)
        
        sim_info = tm_record.proto.filter.simulator
        sim_info.parameters.block_size = best_block_size
        # Setup has_blocksymbol_macro correctly as requested!
        sim_info.parameters.has_blocksymbol_macro = getattr(options, "backsymbol", True)
        
        Macro_Simulator.simulate_machine(machine, options, sim_info, tm_record.proto.status)


class RevEngDecider:
    def __init__(self, name="RevEng"):
        self.name = name

    def apply(self, tm_record, options, time_limit=None):
        with IO.Timer(tm_record.proto.filter.reverse_engineer):
            tm_record.proto.filter.reverse_engineer.tested = True
            if Reverse_Engineer_Filter.is_infinite(tm_record.tm()):
                tm_record.proto.filter.reverse_engineer.success = True
                Halting_Lib.set_not_halting(tm_record.proto.status, io_pb2.INF_REVERSE_ENGINEER)
                tm_record.proto.status.quasihalt_status.is_decided = False


class CTLDecider:
    def __init__(self, type: str, max_block_size: int,
                 cutoff : int = 200, all_offsets=False, no_backsymbol=False, name=None):
        self.name = name or f"{type}_mb{max_block_size}"
        self.type = type
        self.max_block_size = max_block_size
        self.cutoff = cutoff
        self.all_offsets = all_offsets
        self.no_backsymbol = no_backsymbol

    def apply(self, tm_record, options, time_limit=None):
        args = argparse.Namespace(
            type=self.type,
            min_block_size=1,
            max_block_size=self.max_block_size,
            cutoff=self.cutoff,
            offset=0,
            all_offsets=self.all_offsets,
            no_backsymbol=self.no_backsymbol,
            max_block_size_for_all_offsets=self.max_block_size
        )
        # Note: CTL_Filter uses max_block_size but we also have block_size
        CTL_Filter.filter_all(tm_record, args)


class BacktrackingDecider:
    def __init__(self, num_steps, max_width=None, name=None):
        self.name = name or f"Backtrack_{num_steps}"
        self.num_steps = num_steps
        self.max_width = max_width if max_width is not None else 100000

    def apply(self, tm_record, options, time_limit=None):
        Backtracking_Filter.backtrack_filter(tm_record, self.num_steps, self.max_width)

class LinRecurDecider:
    def __init__(self, max_steps, find_min_start_step=False, name=None):
        self.name = name or f"LinRecur_{max_steps}"
        self.max_steps = max_steps
        self.find_min_start_step = find_min_start_step

    def apply(self, tm_record, options, time_limit=None):
        import Lin_Recur_Detect
        lr_info = tm_record.proto.filter.lin_recur
        lr_info.parameters.max_steps = self.max_steps
        lr_info.parameters.find_min_start_step = self.find_min_start_step
        Lin_Recur_Detect.filter(tm_record.tm(), lr_info, tm_record.proto.status)

class CpsDecider:
    def __init__(self, max_block_size : int, fixed_history=None, lru_history=False,
                 max_steps=1_000_000, max_iters=500, max_configs=10_000, max_edges=10_000,
                 name=None):
        self.name = f"CPS_mb{max_block_size}"
        if fixed_history:
            self.name += f"_h{fixed_history}"
        if lru_history:
            self.name += "_lru"
            
        self.max_block_size = max_block_size
        self.fixed_history = fixed_history
        self.lru_history = lru_history
        self.max_steps = max_steps
        self.max_iters = max_iters
        self.max_configs = max_configs
        self.max_edges = max_edges
        
    def apply(self, tm_record, options, time_limit=None):
        import CPS_Filter
        import argparse
        args = argparse.Namespace(
            max_window_size=None,
            min_block_size=1,
            max_block_size=self.max_block_size,
            fixed_history=self.fixed_history,
            lru_history=self.lru_history,
            max_steps=self.max_steps,
            max_iters=self.max_iters,
            max_configs=self.max_configs,
            max_edges=self.max_edges
        )
        CPS_Filter.filter_all(tm_record, args)
