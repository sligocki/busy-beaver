#! /usr/bin/env python3

import Direct_Simulator

import unittest

import IO


def read_range(tape : Direct_Simulator.DirectTape,
               start_pos : int, end_pos : int) -> list[Direct_Simulator.Symbol]:
  return [tape.read_pos(pos) for pos in range(start_pos, end_pos)]

class SystemTest(unittest.TestCase):
  def test_simple(self):
    tm = IO.parse_tm("1RB1LA_0LA1RA")
    sim = Direct_Simulator.DirectSimulator(tm)

    self.assertFalse(sim.halted)
    self.assertEqual(sim.state, 0)
    self.assertEqual(sim.tape.read(), 0)
    self.assertEqual(sim.tape.position, 0)
    self.assertEqual(sim.tape.pos_leftmost(), 0)
    self.assertEqual(sim.tape.pos_rightmost(), 0)
    self.assertEqual(read_range(sim.tape, -10, 10), [0]*20)

    sim.step()
    self.assertFalse(sim.halted)
    self.assertEqual(sim.state, 1)
    self.assertEqual(sim.tape.read(), 0)
    self.assertEqual(sim.tape.position, 1)
    self.assertEqual(sim.tape.pos_leftmost(), 0)
    self.assertEqual(sim.tape.pos_rightmost(), 1)
    self.assertEqual(read_range(sim.tape, -10, 10), [0]*10 + [1] + [0]*9)

    sim.seek(100)
    self.assertFalse(sim.halted)
    self.assertEqual(sim.state, 0)
    self.assertEqual(sim.tape.read(), 0)
    self.assertEqual(sim.tape.position, -20)
    self.assertEqual(sim.tape.pos_leftmost(), -20)
    self.assertEqual(sim.tape.pos_rightmost(), 2)
    self.assertEqual(read_range(sim.tape, -20, 3), [0] + [1]*21 + [0])

  def test_halt(self):
    # BB4 champion
    tm = IO.parse_tm("1RB1LB_1LA0LC_1RZ1LD_1RD0RA")
    sim = Direct_Simulator.DirectSimulator(tm)
    sim.seek(1000)
    self.assertTrue(sim.halted)
    self.assertEqual(sim.step_num, 107)
    self.assertEqual(sim.tape.read(), 0)
    self.assertEqual(list(sim.tape.tape), [1, 0] + [1]*12)

  def test_example(self):
    # This is testing a speicific TM that was broken by a change I was working on.
    tm = IO.parse_tm("1RB3LA1RB2LA1RA_1LB2LA3RA4RB---")
    sim = Direct_Simulator.DirectSimulator(tm)
    sim.seek(1000)
    self.assertFalse(sim.halted)
    self.assertEqual(sim.state, 0)
    self.assertEqual(sim.tape.read(), 2)
    self.assertEqual(list(sim.tape.tape), [1, 4, 1, 2, 2, 2, 3, 3, 2, 3, 2, 3, 3, 3] + [2]*9 + [3, 3, 2, 3, 2, 2, 3, 3, 3, 2, 3, 3, 3, 2, 2, 3, 3, 3, 2, 3])

  def test_expand_tape(self):
    tm = IO.parse_tm("1RB1LB_1LA0LC_1RZ1LD_1RD0RA")
    sim = Direct_Simulator.DirectSimulator(tm)
    sim.seek(100)

    start_pos = sim.tape.pos_leftmost()
    end_pos = sim.tape.pos_rightmost() + 1
    tape_before = read_range(sim.tape, start_pos, end_pos)

    sim.tape._expand_tape(start_pos - 1)
    self.assertEqual(read_range(sim.tape, start_pos, end_pos), tape_before)
    sim.tape._expand_tape(end_pos + 1)
    self.assertEqual(read_range(sim.tape, start_pos, end_pos), tape_before)
    sim.tape._expand_tape(start_pos - 138)
    self.assertEqual(read_range(sim.tape, start_pos, end_pos), tape_before)
    sim.tape._expand_tape(end_pos + 813)
    self.assertEqual(read_range(sim.tape, start_pos, end_pos), tape_before)

    # Ensure that all new symbols are the blank symbol (0).
    self.assertEqual(read_range(sim.tape, start_pos - 200, start_pos), [0]*200)
    self.assertEqual(read_range(sim.tape, end_pos, end_pos + 1000), [0]*1000)

  def test_update_tape(self):
    tm = IO.parse_tm("1RB1LB_1LA0LC_1RZ1LD_1RD0RA")
    sim = Direct_Simulator.DirectSimulator(tm)
    sim.seek(100)

    new_section = [5, 6, 7, 8]
    # No expansion necessary
    sim.tape.update_tape(2, new_section)
    self.assertEqual(read_range(sim.tape, 2, 6), new_section)

    # Expansion to the right
    sim.tape.update_tape(100, new_section)
    self.assertEqual(read_range(sim.tape, 100, 104), new_section)

    # Expansion to the left
    sim.tape.update_tape(-100, new_section)
    self.assertEqual(read_range(sim.tape, -100, -96), new_section)


if __name__ == "__main__":
  unittest.main()
