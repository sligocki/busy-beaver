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
        
    def run(self, tm_record, options, time_limit=None):
        """Try each decider in pipeline on this TM until one successfully decides it (or all fail)."""
        for decider in self.deciders:
            decider.apply(tm_record, options, time_limit)
            if not tm_record.is_unknown_halting():
                self.stats[decider.name] += 1
                break

    def print_stats(self, pout):
        pout.write(f"--- Pipeline Filter Stats ---\n")
        for name, count in self.stats.items():
            if count > 0:
                pout.write(f"  {name}: {count:_}\n")
        pout.write("-----------------------------\n")


class SimulatorDecider:
    def __init__(self, block_size=None, name=None):
        self.block_size = block_size
        self.name = name or ("Simulator" if block_size is None else f"Simulator_b{block_size}")

    def apply(self, tm_record, options, time_limit=None):
        if self.block_size is not None:
            options.block_size = self.block_size
            
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
    def __init__(self, type, min_block_size, max_block_size, cutoff=200, all_offsets=True, no_backsymbol=False, name=None):
        self.name = name or f"{type}_{min_block_size}-{max_block_size}"
        self.type = type
        self.min_block_size = min_block_size
        self.max_block_size = max_block_size
        self.cutoff = cutoff
        self.all_offsets = all_offsets
        self.no_backsymbol = no_backsymbol

    def apply(self, tm_record, options, time_limit=None):
        args = argparse.Namespace(
            type=self.type,
            min_block_size=self.min_block_size,
            max_block_size=self.max_block_size,
            cutoff=self.cutoff,
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
