#! /usr/bin/env python3
"""
Unit test for "Macro_Simulator.py"
"""

import Macro_Simulator

from optparse import OptionParser
import os
import sys
import unittest

import Exp_Int
import Halting_Lib
import IO
from IO import TM_Record
from Macro import Simulator, Turing_Machine
from Macro.Tape import INF
import TM_Enum

import io_pb2


class MacroSimulatorTest(unittest.TestCase):
  # Test that Macro_Simulator simulates known machines for the correct number
  # of steps and symbols.

  def setUp(self):
    # Get busy-beaver root directory.
    test_dir = os.path.dirname(sys.argv[0])
    self.root_dir = os.path.join(test_dir, os.pardir)
    self.root_dir = os.path.normpath(self.root_dir)
    # Setup default options.
    parser = OptionParser()
    Macro_Simulator.add_option_group(parser)
    self.options, args = parser.parse_args([])
    # Don't use time limits during test.
    self.options.time = 0
    self.maxDiff = None

  def load_tm_record_filename(self, filename):
    tm = IO.load_tm(filename, 0)
    tm_enum = TM_Enum.TM_Enum(tm, allow_no_halt = False)
    return TM_Record.TM_Record(tm_enum = tm_enum)

  def test_bug_qhalt(self):
    # This machine failed:
    #   File ".../Code/Macro/Simulator.py", line 120, in calc_quasihalt
    #     if last_seen > q_state_last_seen:
    # while proving a rule because last_seen / q_state_last_seen were
    # Algebraic_Expressions.
    tm = IO.parse_tm("1RB1RC_0LC1LA_0LD1LB_0RD1RE_1LC0RA")
    tm = Turing_Machine.Backsymbol_Macro_Machine(tm)
    sim = Simulator.Simulator(tm, self.options)
    sim.loop_run(100)
    self.assertEqual(sim.op_state, Turing_Machine.INF_REPEAT)

  def test_bug_rec_diff(self):
    # This machine failed:
    #   File ".../Code/Macro/Proof_System.py", line 1113, in apply_diff_rule
    #     assert len(term.vars) == 1, term
    # AssertionError: 16 h j
    tm = IO.parse_tm("1RB1RD_1LC1RA_1RB1LD_1RE0LC_0LC0RA")
    tm = Turing_Machine.Block_Macro_Machine(tm, 2)
    tm = Turing_Machine.Backsymbol_Macro_Machine(tm)
    self.options.recursive = True
    self.options.exp_linear_rules = True
    sim = Simulator.Simulator(tm, self.options)
    # The failure happened at loop 919 on 7 Apr 2022.
    sim.loop_run(10_000)
    # Just make sure that we run long enough (and actually prove the rec rule)
    # we don't expect to actually prove the machine.

  def test_bug_rec_comp(self):
    # This machine failed:
    #   File ".../Code/Macro/Proof_System.py", line 1356, in config_is_above_min
    #     if current_val < min_val:
    # Algebraic_Expression.BadOperation
    tm = IO.parse_tm("1RB0LC_0RC0RD_1LA1RE_1RC0LE_0LD0RC")
    tm = Turing_Machine.Block_Macro_Machine(tm, 2)
    tm = Turing_Machine.Backsymbol_Macro_Machine(tm)
    self.options.recursive = True
    self.options.exp_linear_rules = True
    sim = Simulator.Simulator(tm, self.options)
    # The failure happened at loop 123 on 7 Apr 2022 (before fix).
    # TM is proven infinite at loop 333 (after fix).
    sim.loop_run(1000)
    self.assertEqual(sim.op_state, Turing_Machine.INF_REPEAT)

  def test_bug_rec_rule_mins(self):
    # See: https://github.com/sligocki/busy-beaver/issues/4
    tm = IO.parse_tm("1RB1LA_1RC0LE_1RD1LC_1LA0RF_1RD0LA_1RZ0RE")
    tm = Turing_Machine.Backsymbol_Macro_Machine(tm)
    self.options.recursive = True
    self.options.exp_linear_rules = True
    sim = Simulator.Simulator(tm, self.options)
    # TM was declared Halting (incorrect) at loop 96 on 26 Apr 2022 (before fix).
    # Then, same issue at loop 164 after partial fix.
    sim.loop_run(1000)
    self.assertNotEqual(sim.op_state, Turing_Machine.HALT)


  def test_small_halting(self):
    self.options.max_loops = 10_000
    # TODO(shawn): Should we just list the machine ttables directly instead?
    data = [("Machines/2x2-6-4", 6, 4),
            ("Machines/2x3-38-9", 38, 9),
            ("Machines/2x4-3932964-2050", 3932964, 2050),
            ("Machines/3x2-14-6", 14, 6),
            ("Machines/3x2-21-5", 21, 5),
            ("Machines/3x3-e17", 119112334170342540, 374676383),
            ("Machines/4x2-107-13", 107, 13),
            ("Machines/5x2-47176870-4098", 47176870, 4098),
            ("Machines/6x2-1", 13122572797, 136612),
            ("Machines/6x2-Green", 436, 35),
            ]
    for name, expected_steps, expected_score in data:
      filename = os.path.join(self.root_dir, name)
      tm_record = self.load_tm_record_filename(filename)
      try:
        Macro_Simulator.run_options(tm_record, self.options, 0.0)
      except:
        print("Error")
        print(name)
        raise
      self.assertFalse(tm_record.is_unknown_halting())
      self.assertTrue(tm_record.is_halting())
      self.assertEqual(Halting_Lib.get_big_int(tm_record.proto.status.halt_status.halt_steps),
                       expected_steps)
      self.assertEqual(Halting_Lib.get_big_int(tm_record.proto.status.halt_status.halt_score),
                       expected_score)

  def test_medium_halting(self):
    self.options.max_loops = 100_000
    data = [("Machines/2x5-e704",
             190282916614912976971178894914993423154449611310999556082522091580398024988179871263976771152617039324687422073674727556033765365815249814149279324440868411015096012479322048511264818866734215557976327245860530987070322862134260620002750847931226933305215449178921430294254511331593380579565596462250251756508571695291245917982611765119501158512949469897328673850184299624231030222372437154213503321136877877896606586851396019185159834879387000600955087580733165363673666786112829270952177017805116456278722546358429249188194516978022818365972073826588310015724870584042958950865442583137061907541982878261306211149968318903489501309660869300105000568503668204823982632164815051695298707924186734604934655, 17808374276114827179409165501110094347458953925524201057539295445498984038114371347629489952511050406043006585390507303594212813536645162904075575572206987865745833932117157019354966523037693527328238415191227013720305505859015489988006341788486725058461290508808960478051231024106456742446113814498720521570272294127488716030618060028602983180967071713),
            ("Machines/6x2-r",
             300232771652356282895510301834134018514775433724675250037338180173521424076038326588191208297820287669898401786071345848280422383492822716051848585583668153797251438618561730209415487685570078538658757304857487222040030769844045098871367087615079138311034353164641077919209890837164477363289374225531955126023251172259034570155087303683654630874155990822516129938425830691378607273670708190160525534077040039226593073997923170154775358629850421712513378527086223112680677973751790032937578520017666792246839908855920362933767744760870128446883455477806316491601855784426860769027944542798006152693167452821336689917460886106486574189015401194034857577718253065541632656334314242325592486700118506716581303423271748965426160409797173073716688827281435904639445605928175254048321109306002474658968108793381912381812336227992839930833085933478853176574702776062858289156568392295963586263654139383856764728051394965554409688456578122743296319960808368094536421039149584946758006509160985701328997026301708760235500239598119410592142621669614552827244429217416465494363891697113965316892660611709290048580677566178715752354594049016719278069832866522332923541370293059667996001319376698551683848851474625152094567110615451986839894490885687082244978774551453204358588661593979763935102896523295803940023673203101744986550732496850436999753711343067328676158146269292723375662015612826924105454849658410961574031211440611088975349899156714888681952366018086246687712098553077054825367434062671756760070388922117434932633444773138783714023735898712790278288377198260380065105075792925239453450622999208297579584893448886278127629044163292251815410053522246084552761513383934623129083266949377380950466643121689746511996847681275076313206, 12914951964730997250673433546819849509549358087128690053958730050912043114050444850240131432687888779698205017959267279467247759159594822175225305432481859864495796137909683447198447312843568880129905330630692235127777655264853382670979398926663934043364554169509365540834461843577841574296433860268929575034928793440722283883496539655948945100141899429447468817367569604813038150912656805487172475593041843712279467853624749989147054303748499093249845855395105658447844504456040960051641314951220524824061775814634738272664481030066727094186265135749803147803742486664009592180119421672821913958840123231130890028804306931645773916087727281493526404733170198979765603424776606833684409529730007044118561624874873652997002032667344587137859002909978872928814647043325481327200728882173015355211743620254438041767965892742035979306286763642267313721146548318330807873)
            ]
    for name, expected_steps, expected_score in data:
      filename = os.path.join(self.root_dir, name)
      tm_record = self.load_tm_record_filename(filename)
      try:
        Macro_Simulator.run_options(tm_record, self.options, 0.0)
      except:
        print("Error")
        print(name)
        raise
      self.assertFalse(tm_record.is_unknown_halting())
      self.assertTrue(tm_record.is_halting())
      self.assertEqual(Halting_Lib.get_big_int(tm_record.proto.status.halt_status.halt_steps),
                       expected_steps)
      self.assertEqual(Halting_Lib.get_big_int(tm_record.proto.status.halt_status.halt_score),
                       expected_score)

  def test_large_halting(self):
    self.options.recursive = True
    self.options.exp_linear_rules = True
    self.options.compute_steps = False
    self.options.max_loops = 1_000_000
    self.options.max_block_size = 100
    data = [("Machines/6x2-e21132-Pavel",  2.604, "((25 + 3^22147)/2)"),
            ("Machines/6x2-e36534-Pavel",  2.629, "((23 + 25 * 2^60682)/9)"),
            ("Machines/6x2-e78913",        2.662, "(1 + 3 * 2^131071)"),
            ("Machines/6x2-e197282-Pavel", 2.698, "(-4 + 5 * 2^((-6 + 5 * 2^17)/2))"),
            ]
    for name, expected_tower, expected_formula in data:
      filename = os.path.join(self.root_dir, name)
      tm_record = self.load_tm_record_filename(filename)
      try:
        Macro_Simulator.run_options(tm_record, self.options, 0.0)
      except:
        print("Error")
        print(name)
        raise
      self.assertFalse(tm_record.is_unknown_halting())
      self.assertTrue(tm_record.is_halting())
      self.assertEqual(Halting_Lib.get_big_int(tm_record.proto.status.halt_status.halt_steps),
                       0)
      score = Halting_Lib.get_big_int(tm_record.proto.status.halt_status.halt_score)
      self.assertEqual(score.formula_str, expected_formula)
      self.assertAlmostEqual(Exp_Int.fractional_height(score), expected_tower, 2)

  def test_giant_halting(self):
    self.options.recursive = True
    self.options.exp_linear_rules = True
    self.options.compute_steps = False
    self.options.max_loops = 1_000_000
    self.options.max_block_size = 100
    data = [("Machines/6x2-t5", None, 5.635,
             "((49 + 19 * 2^((-17 + 7 * 2^((-11 + 7 * 2^((-11 + 19 * 2^69175)/9))/9))/9))/9)"),
            ("Machines/6x2-t15-Pavel", None, 15.604,
             "((-11 + 3^((13 + 3^((23 + 3^((7 + 3^((21 + 3^((7 + 3^((23 + 3^((7 + 3^((23 + 3^((7 + 3^((21 + 3^((7 + 3^((23 + 3^((7 + 3^22146)/8))/8))/8))/8))/8))/8))/8))/8))/8))/8))/8))/8))/8))/2)"),
            # TODO: Improve block_finder so that it finds optimal block size 2 here.
            ("Machines/2x6-t70", 2, 70.275,
             "(14 + 2^(-1 + 2^(2 + 2^(1 + 2^(-1 + 2^(4 + 2^(2^(-1 + 2^(2^(2 + 2^(2^(2 + 2^(2^(-1 + 2^(2^(-1 + 2^(2^(3 + 2^(2^(3 + 2^(2^(2 + 2^(2^(-1 + 2^(2^(-1 + 2^(2^(2 + 2^(2^(4 + 2^(2^(-1 + 2^(2^(2 + 2^(2^(2 + 2^(2^(-1 + 2^(2^(3 + 2^(2^(-1 + 2^(4 + 2^(2^(-1 + 2^(2^(-1 + 2^(2^(-1 + 2^(2^(4 + 2^(2^(-1 + 2^(2^(-1 + 2^(2^(1 + 2^(1 + 2^(-1 + 2^(4 + 2^(2^(-1 + 2^(2^(2 + 2^(2^(2 + 2^(2^(-1 + 2^(2^258)))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))"),
            ]
    for name, force_block_size, expected_tower, expected_formula in data:
      filename = os.path.join(self.root_dir, name)
      tm_record = self.load_tm_record_filename(filename)
      if force_block_size:
        self.options.block_size = force_block_size
      try:
        Macro_Simulator.run_options(tm_record, self.options, 0.0)
      except:
        print("Error")
        print(name)
        raise
      self.assertFalse(tm_record.is_unknown_halting())
      self.assertTrue(tm_record.is_halting())
      self.assertEqual(Halting_Lib.get_big_int(tm_record.proto.status.halt_status.halt_steps),
                       0)
      score = Halting_Lib.get_big_int(tm_record.proto.status.halt_status.halt_score)
      self.assertEqual(score.formula_str, expected_formula)
      self.assertAlmostEqual(Exp_Int.fractional_height(score), expected_tower, 2)

  def test_non_halting(self):
    self.options.recursive = True
    self.options.exp_linear_rules = True
    tm = IO.parse_tm("1RB---2LA_2LB2RA0LB")
    tm_enum = TM_Enum.TM_Enum(tm, allow_no_halt = False)
    tm_record = TM_Record.TM_Record(tm_enum = tm_enum)
    simulated_result = Macro_Simulator.run_options(tm_record, self.options, 0.0)

    # Non halting
    self.assertFalse(tm_record.is_unknown_halting())
    self.assertFalse(tm_record.is_halting())
    self.assertEqual(tm_record.proto.status.halt_status.inf_reason,
                     io_pb2.INF_CTL)

if __name__ == '__main__':
  unittest.main()
