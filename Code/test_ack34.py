import unittest
import IO
from Macro import Simulator
from Macro import Turing_Machine
import optparse

class TestAck34(unittest.TestCase):

  def test_sim_rules(self):
    tm = IO.parse_tm("1RB3LB1RZ2RA_2LC3RB1LC2RA_3RB1LB3LC2RC")
    
    class Options(optparse.Values):
      def __init__(self):
        super().__init__()
        self.block_size = 2
        self.backsymbol = True
        self.prover = True
        self.recursive = True
        self.compute_steps = False
        self.verbose_prover = False
        self.verbose_simulator = False
        self.verbose_prover_run = False
        self.exp_linear_rules = True
        self.exp_meta_linear_rules = True
        self.print_loops = 0
        self.max_loops = 10000
        self.verbose_prefix = ""
        self.max_steps_in_backsymbol = 250
        self.max_num_reps = 10
        self.limited_rules = False
        self.allow_collatz = False
        self.max_prover_configs = 100000

    options = Options()
    
    machine = Turing_Machine.Block_Macro_Machine(tm, options.block_size)
    machine = Turing_Machine.Backsymbol_Macro_Machine(machine, max_sim_steps_per_symbol=options.max_steps_in_backsymbol)
    sim = Simulator.Simulator(machine, options)
    
    # Run for up to 10000 loops
    sim.loop_seek(10000)
    
    # Verify that higher-level rules were proven
    print("\nRules proven by level:", sim.prover.num_rules_by_level)
    print("Total Rules:", sim.prover.num_rules)
    print("Iterated Rules:", sim.prover.num_linear_rules)
    print("General Rules:", sim.prover.num_gen_rules)
    self.assertGreaterEqual(sim.prover.num_rules_by_level.get(4, 0), 1)

if __name__ == '__main__':
  unittest.main()
