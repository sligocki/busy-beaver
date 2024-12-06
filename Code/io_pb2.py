# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: io.proto
# Protobuf Python Version: 5.28.3
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    28,
    3,
    '',
    'io.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x08io.proto\x12\x0b\x62usy_beaver\"s\n\x07\x45xpTerm\x12\x0c\n\x04\x62\x61se\x18\x01 \x01(\x04\x12!\n\x04\x63oef\x18\x04 \x01(\x0b\x32\x13.busy_beaver.BigInt\x12%\n\x08\x65xponent\x18\x03 \x01(\x0b\x32\x13.busy_beaver.BigInt\x12\x10\n\x08\x63oef_old\x18\x02 \x01(\x12\"s\n\x06\x45xpInt\x12#\n\x05terms\x18\x01 \x03(\x0b\x32\x14.busy_beaver.ExpTerm\x12\"\n\x05\x63onst\x18\x04 \x01(\x0b\x32\x13.busy_beaver.BigInt\x12\r\n\x05\x64\x65nom\x18\x03 \x01(\x04\x12\x11\n\tconst_old\x18\x02 \x01(\x12\"\xa2\x01\n\x06\x42igInt\x12\r\n\x03int\x18\x08 \x01(\x12H\x00\x12\x11\n\x07hex_str\x18\x03 \x01(\tH\x00\x12&\n\x07\x65xp_int\x18\x06 \x01(\x0b\x32\x13.busy_beaver.ExpIntH\x00\x12\x18\n\x0e\x65xp_int_pickle\x18\x07 \x01(\x0cH\x00\x12\x15\n\x0b\x65xp_int_str\x18\x04 \x01(\tH\x00\x12\x12\n\x08uint_old\x18\x01 \x01(\x04H\x00\x42\t\n\x07\x62ig_int\"F\n\x06TMList\x12\x12\n\nnum_states\x18\x01 \x01(\x11\x12\x13\n\x0bnum_symbols\x18\x02 \x01(\x11\x12\x13\n\x0bttable_list\x18\x03 \x03(\x11\"\x8b\x01\n\rTuringMachine\x12\x17\n\rttable_packed\x18\x01 \x01(\x0cH\x00\x12*\n\x0bttable_list\x18\x04 \x01(\x0b\x32\x13.busy_beaver.TMListH\x00\x12\x14\n\nttable_str\x18\x03 \x01(\tH\x00\x12\x15\n\rallow_no_halt\x18\x02 \x01(\x08\x42\x08\n\x06ttable\"\xdb\x01\n\nHaltStatus\x12\x12\n\nis_decided\x18\x01 \x01(\x08\x12\x12\n\nis_halting\x18\x02 \x01(\x08\x12\'\n\nhalt_steps\x18\x03 \x01(\x0b\x32\x13.busy_beaver.BigInt\x12\'\n\nhalt_score\x18\x04 \x01(\x0b\x32\x13.busy_beaver.BigInt\x12\x12\n\nfrom_state\x18\x06 \x01(\x04\x12\x13\n\x0b\x66rom_symbol\x18\x07 \x01(\x04\x12*\n\ninf_reason\x18\x05 \x01(\x0e\x32\x16.busy_beaver.InfReason\"\x85\x01\n\x0fQuasihaltStatus\x12\x12\n\nis_decided\x18\x01 \x01(\x08\x12\x17\n\x0fis_quasihalting\x18\x02 \x01(\x08\x12,\n\x0fquasihalt_steps\x18\x03 \x01(\x0b\x32\x13.busy_beaver.BigInt\x12\x17\n\x0fquasihalt_state\x18\x04 \x01(\x04\"p\n\x08\x42\x42Status\x12,\n\x0bhalt_status\x18\x01 \x01(\x0b\x32\x17.busy_beaver.HaltStatus\x12\x36\n\x10quasihalt_status\x18\x02 \x01(\x0b\x32\x1c.busy_beaver.QuasihaltStatus\"\xf4\x01\n\x0fSimulatorParams\x12\x12\n\nblock_size\x18\t \x01(\x04\x12\x1d\n\x15has_blocksymbol_macro\x18\n \x01(\x08\x12\x11\n\tmax_loops\x18\x01 \x01(\x04\x12\x14\n\x0cmax_time_sec\x18\x02 \x01(\x02\x12\x17\n\x0fmax_tape_blocks\x18\x03 \x01(\x04\x12\x12\n\nuse_prover\x18\x04 \x01(\x08\x12 \n\x18only_log_configs_at_edge\x18\x05 \x01(\x08\x12\x19\n\x11use_limited_rules\x18\x06 \x01(\x08\x12\x1b\n\x13use_recursive_rules\x18\x07 \x01(\x08\"\x1e\n\x08HaltInfo\x12\x12\n\nis_halting\x18\x01 \x01(\x08\"[\n\x12InfMacroRepeatInfo\x12\x14\n\x0cmacro_symbol\x18\x01 \x01(\t\x12\x13\n\x0bmacro_state\x18\x02 \x01(\t\x12\x1a\n\x12macro_dir_is_right\x18\x03 \x01(\x08\"=\n\x10InfChainMoveInfo\x12\x13\n\x0bmacro_state\x18\x01 \x01(\t\x12\x14\n\x0c\x64ir_is_right\x18\x02 \x01(\x08\"\"\n\x12InfProofSystemInfo\x12\x0c\n\x04rule\x18\x01 \x01(\t\"\xbf\x01\n\x0cInfiniteInfo\x12\x37\n\x0cmacro_repeat\x18\x01 \x01(\x0b\x32\x1f.busy_beaver.InfMacroRepeatInfoH\x00\x12\x33\n\nchain_move\x18\x02 \x01(\x0b\x32\x1d.busy_beaver.InfChainMoveInfoH\x00\x12\x37\n\x0cproof_system\x18\x03 \x01(\x0b\x32\x1f.busy_beaver.InfProofSystemInfoH\x00\x42\x08\n\x06reason\"\"\n\rOverLoopsInfo\x12\x11\n\tnum_loops\x18\x01 \x01(\x04\",\n\x0cOverTapeInfo\x12\x1c\n\x14\x63ompressed_tape_size\x18\x01 \x01(\x04\"(\n\x0cOverTimeInfo\x12\x18\n\x10\x65lapsed_time_sec\x18\x01 \x01(\x02\"]\n\x14OverStepsInMacroInfo\x12\x14\n\x0cmacro_symbol\x18\x01 \x01(\t\x12\x13\n\x0bmacro_state\x18\x02 \x01(\t\x12\x1a\n\x12macro_dir_is_right\x18\x03 \x01(\x08\"\x86\x02\n\x0bUnknownInfo\x12\x30\n\nover_loops\x18\x01 \x01(\x0b\x32\x1a.busy_beaver.OverLoopsInfoH\x00\x12.\n\tover_tape\x18\x02 \x01(\x0b\x32\x19.busy_beaver.OverTapeInfoH\x00\x12.\n\tover_time\x18\x03 \x01(\x0b\x32\x19.busy_beaver.OverTimeInfoH\x00\x12@\n\x13over_steps_in_macro\x18\x04 \x01(\x0b\x32!.busy_beaver.OverStepsInMacroInfoH\x00\x12\x19\n\x0fthrew_exception\x18\x05 \x01(\x08H\x00\x42\x08\n\x06reason\"\x9d\x04\n\x0fSimulatorResult\x12*\n\thalt_info\x18\x01 \x01(\x0b\x32\x15.busy_beaver.HaltInfoH\x00\x12\x32\n\rinfinite_info\x18\x02 \x01(\x0b\x32\x19.busy_beaver.InfiniteInfoH\x00\x12\x30\n\x0cunknown_info\x18\x03 \x01(\x0b\x32\x18.busy_beaver.UnknownInfoH\x00\x12\x17\n\x0f\x65lapsed_time_us\x18\x05 \x01(\x04\x12\x11\n\tnum_loops\x18\x06 \x01(\x04\x12\x17\n\x0fnum_macro_moves\x18\x07 \x01(\x04\x12\x17\n\x0fnum_chain_moves\x18\n \x01(\x04\x12\x16\n\x0enum_rule_moves\x18\x0b \x01(\x04\x12\x17\n\x0flog10_num_steps\x18\x04 \x01(\x04\x12\x18\n\x10num_rules_proven\x18\x08 \x01(\x04\x12\"\n\x1anum_meta_diff_rules_proven\x18\x0c \x01(\x04\x12\x1f\n\x17num_linear_rules_proven\x18\x0e \x01(\x04\x12$\n\x1cnum_exponential_rules_proven\x18\x10 \x01(\x04\x12\x1c\n\x14num_gen_rules_proven\x18\r \x01(\x04\x12\x19\n\x11num_collatz_rules\x18\x0f \x01(\x04\x12\x19\n\x11num_proofs_failed\x18\t \x01(\x04\x42\x10\n\x0e\x65xit_condition\"o\n\rSimulatorInfo\x12\x30\n\nparameters\x18\x01 \x01(\x0b\x32\x1c.busy_beaver.SimulatorParams\x12,\n\x06result\x18\x02 \x01(\x0b\x32\x1c.busy_beaver.SimulatorResult\"\x91\x01\n\x11\x42lockFinderParams\x12 \n\x18\x63ompression_search_loops\x18\x01 \x01(\x04\x12\x16\n\x0emult_sim_loops\x18\x02 \x01(\x04\x12\x16\n\x0emax_block_mult\x18\x03 \x01(\x04\x12\x16\n\x0emax_block_size\x18\x04 \x01(\x04\x12\x12\n\nblock_mult\x18\x05 \x01(\x04\"\xad\x02\n\x11\x42lockFinderResult\x12\x17\n\x0f\x62\x65st_block_size\x18\x01 \x01(\x04\x12\x17\n\x0f\x65lapsed_time_us\x18\x02 \x01(\x04\x12\x1d\n\x15least_compressed_loop\x18\x03 \x01(\x04\x12(\n least_compressed_tape_size_chain\x18\x04 \x01(\x04\x12&\n\x1eleast_compressed_tape_size_raw\x18\x05 \x01(\x04\x12#\n\x1b\x62\x65st_compression_block_size\x18\x06 \x01(\x04\x12\"\n\x1a\x62\x65st_compression_tape_size\x18\x07 \x01(\x04\x12\x11\n\tbest_mult\x18\x08 \x01(\x04\x12\x19\n\x11\x62\x65st_chain_factor\x18\t \x01(\x02\"u\n\x0f\x42lockFinderInfo\x12\x32\n\nparameters\x18\x01 \x01(\x0b\x32\x1e.busy_beaver.BlockFinderParams\x12.\n\x06result\x18\x02 \x01(\x0b\x32\x1e.busy_beaver.BlockFinderResult\"F\n\nFilterInfo\x12\x0e\n\x06tested\x18\x01 \x01(\x08\x12\x0f\n\x07success\x18\x02 \x01(\x08\x12\x17\n\x0f\x65lapsed_time_us\x18\x03 \x01(\x04\"F\n\x14LinRecurFilterParams\x12\x11\n\tmax_steps\x18\x01 \x01(\x04\x12\x1b\n\x13\x66ind_min_start_step\x18\x02 \x01(\x08\"t\n\x14LinRecurFilterResult\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x12\n\nstart_step\x18\x02 \x01(\x04\x12\x0e\n\x06period\x18\x03 \x01(\x04\x12\x0e\n\x06offset\x18\x04 \x01(\x12\x12\x17\n\x0f\x65lapsed_time_us\x18\x05 \x01(\x04\"~\n\x12LinRecurFilterInfo\x12\x35\n\nparameters\x18\x01 \x01(\x0b\x32!.busy_beaver.LinRecurFilterParams\x12\x31\n\x06result\x18\x02 \x01(\x0b\x32!.busy_beaver.LinRecurFilterResult\"?\n\tCTLParams\x12\x12\n\nblock_size\x18\x01 \x01(\x04\x12\x0e\n\x06offset\x18\x02 \x01(\x04\x12\x0e\n\x06\x63utoff\x18\x03 \x01(\x04\"H\n\tCTLResult\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x11\n\tnum_iters\x18\x03 \x01(\x04\x12\x17\n\x0f\x65lapsed_time_us\x18\x02 \x01(\x04\"]\n\x07\x43TLInfo\x12*\n\nparameters\x18\x01 \x01(\x0b\x32\x16.busy_beaver.CTLParams\x12&\n\x06result\x18\x02 \x01(\x0b\x32\x16.busy_beaver.CTLResult\"\xaf\x01\n\rCTLFilterInfo\x12$\n\x06\x63tl_as\x18\x05 \x01(\x0b\x32\x14.busy_beaver.CTLInfo\x12&\n\x08\x63tl_as_b\x18\x06 \x01(\x0b\x32\x14.busy_beaver.CTLInfo\x12&\n\x08\x63tl_a_bs\x18\x07 \x01(\x0b\x32\x14.busy_beaver.CTLInfo\x12(\n\nctl_as_b_c\x18\x08 \x01(\x0b\x32\x14.busy_beaver.CTLInfo\"=\n\x15\x42\x61\x63ktrackFilterParams\x12\x11\n\tnum_steps\x18\x01 \x01(\x04\x12\x11\n\tmax_width\x18\x02 \x01(\x04\"z\n\x15\x42\x61\x63ktrackFilterResult\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x11\n\tmax_steps\x18\x03 \x01(\x04\x12\x11\n\tmax_width\x18\x04 \x01(\x04\x12\x11\n\tnum_nodes\x18\x05 \x01(\x04\x12\x17\n\x0f\x65lapsed_time_us\x18\x02 \x01(\x04\"\x81\x01\n\x13\x42\x61\x63ktrackFilterInfo\x12\x36\n\nparameters\x18\x01 \x01(\x0b\x32\".busy_beaver.BacktrackFilterParams\x12\x32\n\x06result\x18\x02 \x01(\x0b\x32\".busy_beaver.BacktrackFilterResult\"\xb3\x01\n\x17\x43losedGraphFilterParams\x12\x16\n\x0emin_block_size\x18\x01 \x01(\x04\x12\x16\n\x0emax_block_size\x18\x02 \x01(\x04\x12\x1a\n\x12search_all_windows\x18\x03 \x01(\x08\x12\x11\n\tmax_steps\x18\x04 \x01(\x04\x12\x11\n\tmax_iters\x18\x05 \x01(\x04\x12\x13\n\x0bmax_configs\x18\x06 \x01(\x04\x12\x11\n\tmax_edges\x18\x07 \x01(\x04\"\xd2\x01\n\x17\x43losedGraphFilterResult\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x12\n\nblock_size\x18\x03 \x01(\x04\x12\x13\n\x0bwindow_size\x18\x04 \x01(\x04\x12\x11\n\tnum_steps\x18\x05 \x01(\x04\x12\x13\n\x0bnum_configs\x18\x06 \x01(\x04\x12\x11\n\tnum_edges\x18\x07 \x01(\x04\x12\x11\n\tnum_iters\x18\x08 \x01(\x04\x12\x16\n\x0e\x66ound_inf_loop\x18\t \x01(\x08\x12\x17\n\x0f\x65lapsed_time_us\x18\x02 \x01(\x04\"\x87\x01\n\x15\x43losedGraphFilterInfo\x12\x38\n\nparameters\x18\x01 \x01(\x0b\x32$.busy_beaver.ClosedGraphFilterParams\x12\x34\n\x06result\x18\x02 \x01(\x0b\x32$.busy_beaver.ClosedGraphFilterResult\"\xf1\x02\n\rFilterResults\x12-\n\tsimulator\x18\x01 \x01(\x0b\x32\x1a.busy_beaver.SimulatorInfo\x12\x32\n\x0c\x62lock_finder\x18\x02 \x01(\x0b\x32\x1c.busy_beaver.BlockFinderInfo\x12\x31\n\x10reverse_engineer\x18\x03 \x01(\x0b\x32\x17.busy_beaver.FilterInfo\x12\x32\n\tlin_recur\x18\x04 \x01(\x0b\x32\x1f.busy_beaver.LinRecurFilterInfo\x12\'\n\x03\x63tl\x18\x05 \x01(\x0b\x32\x1a.busy_beaver.CTLFilterInfo\x12\x33\n\tbacktrack\x18\x06 \x01(\x0b\x32 .busy_beaver.BacktrackFilterInfo\x12\x38\n\x0c\x63losed_graph\x18\x07 \x01(\x0b\x32\".busy_beaver.ClosedGraphFilterInfo\"\xb4\x01\n\x08TMRecord\x12\x14\n\x0cspec_version\x18\x01 \x01(\x04\x12&\n\x02tm\x18\x02 \x01(\x0b\x32\x1a.busy_beaver.TuringMachine\x12%\n\x06status\x18\x03 \x01(\x0b\x32\x15.busy_beaver.BBStatus\x12*\n\x06\x66ilter\x18\x04 \x01(\x0b\x32\x1a.busy_beaver.FilterResults\x12\x17\n\x0f\x65lapsed_time_us\x18\x05 \x01(\x04*\xb8\x01\n\tInfReason\x12\x13\n\x0fINF_UNSPECIFIED\x10\x00\x12\x12\n\x0eINF_MACRO_STEP\x10\x01\x12\x12\n\x0eINF_CHAIN_STEP\x10\x02\x12\x14\n\x10INF_PROOF_SYSTEM\x10\x03\x12\x18\n\x14INF_REVERSE_ENGINEER\x10\x04\x12\x11\n\rINF_LIN_RECUR\x10\x05\x12\x0b\n\x07INF_CTL\x10\x06\x12\x11\n\rINF_BACKTRACK\x10\x07\x12\x0b\n\x07INF_CPS\x10\x08\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'io_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_INFREASON']._serialized_start=5697
  _globals['_INFREASON']._serialized_end=5881
  _globals['_EXPTERM']._serialized_start=25
  _globals['_EXPTERM']._serialized_end=140
  _globals['_EXPINT']._serialized_start=142
  _globals['_EXPINT']._serialized_end=257
  _globals['_BIGINT']._serialized_start=260
  _globals['_BIGINT']._serialized_end=422
  _globals['_TMLIST']._serialized_start=424
  _globals['_TMLIST']._serialized_end=494
  _globals['_TURINGMACHINE']._serialized_start=497
  _globals['_TURINGMACHINE']._serialized_end=636
  _globals['_HALTSTATUS']._serialized_start=639
  _globals['_HALTSTATUS']._serialized_end=858
  _globals['_QUASIHALTSTATUS']._serialized_start=861
  _globals['_QUASIHALTSTATUS']._serialized_end=994
  _globals['_BBSTATUS']._serialized_start=996
  _globals['_BBSTATUS']._serialized_end=1108
  _globals['_SIMULATORPARAMS']._serialized_start=1111
  _globals['_SIMULATORPARAMS']._serialized_end=1355
  _globals['_HALTINFO']._serialized_start=1357
  _globals['_HALTINFO']._serialized_end=1387
  _globals['_INFMACROREPEATINFO']._serialized_start=1389
  _globals['_INFMACROREPEATINFO']._serialized_end=1480
  _globals['_INFCHAINMOVEINFO']._serialized_start=1482
  _globals['_INFCHAINMOVEINFO']._serialized_end=1543
  _globals['_INFPROOFSYSTEMINFO']._serialized_start=1545
  _globals['_INFPROOFSYSTEMINFO']._serialized_end=1579
  _globals['_INFINITEINFO']._serialized_start=1582
  _globals['_INFINITEINFO']._serialized_end=1773
  _globals['_OVERLOOPSINFO']._serialized_start=1775
  _globals['_OVERLOOPSINFO']._serialized_end=1809
  _globals['_OVERTAPEINFO']._serialized_start=1811
  _globals['_OVERTAPEINFO']._serialized_end=1855
  _globals['_OVERTIMEINFO']._serialized_start=1857
  _globals['_OVERTIMEINFO']._serialized_end=1897
  _globals['_OVERSTEPSINMACROINFO']._serialized_start=1899
  _globals['_OVERSTEPSINMACROINFO']._serialized_end=1992
  _globals['_UNKNOWNINFO']._serialized_start=1995
  _globals['_UNKNOWNINFO']._serialized_end=2257
  _globals['_SIMULATORRESULT']._serialized_start=2260
  _globals['_SIMULATORRESULT']._serialized_end=2801
  _globals['_SIMULATORINFO']._serialized_start=2803
  _globals['_SIMULATORINFO']._serialized_end=2914
  _globals['_BLOCKFINDERPARAMS']._serialized_start=2917
  _globals['_BLOCKFINDERPARAMS']._serialized_end=3062
  _globals['_BLOCKFINDERRESULT']._serialized_start=3065
  _globals['_BLOCKFINDERRESULT']._serialized_end=3366
  _globals['_BLOCKFINDERINFO']._serialized_start=3368
  _globals['_BLOCKFINDERINFO']._serialized_end=3485
  _globals['_FILTERINFO']._serialized_start=3487
  _globals['_FILTERINFO']._serialized_end=3557
  _globals['_LINRECURFILTERPARAMS']._serialized_start=3559
  _globals['_LINRECURFILTERPARAMS']._serialized_end=3629
  _globals['_LINRECURFILTERRESULT']._serialized_start=3631
  _globals['_LINRECURFILTERRESULT']._serialized_end=3747
  _globals['_LINRECURFILTERINFO']._serialized_start=3749
  _globals['_LINRECURFILTERINFO']._serialized_end=3875
  _globals['_CTLPARAMS']._serialized_start=3877
  _globals['_CTLPARAMS']._serialized_end=3940
  _globals['_CTLRESULT']._serialized_start=3942
  _globals['_CTLRESULT']._serialized_end=4014
  _globals['_CTLINFO']._serialized_start=4016
  _globals['_CTLINFO']._serialized_end=4109
  _globals['_CTLFILTERINFO']._serialized_start=4112
  _globals['_CTLFILTERINFO']._serialized_end=4287
  _globals['_BACKTRACKFILTERPARAMS']._serialized_start=4289
  _globals['_BACKTRACKFILTERPARAMS']._serialized_end=4350
  _globals['_BACKTRACKFILTERRESULT']._serialized_start=4352
  _globals['_BACKTRACKFILTERRESULT']._serialized_end=4474
  _globals['_BACKTRACKFILTERINFO']._serialized_start=4477
  _globals['_BACKTRACKFILTERINFO']._serialized_end=4606
  _globals['_CLOSEDGRAPHFILTERPARAMS']._serialized_start=4609
  _globals['_CLOSEDGRAPHFILTERPARAMS']._serialized_end=4788
  _globals['_CLOSEDGRAPHFILTERRESULT']._serialized_start=4791
  _globals['_CLOSEDGRAPHFILTERRESULT']._serialized_end=5001
  _globals['_CLOSEDGRAPHFILTERINFO']._serialized_start=5004
  _globals['_CLOSEDGRAPHFILTERINFO']._serialized_end=5139
  _globals['_FILTERRESULTS']._serialized_start=5142
  _globals['_FILTERRESULTS']._serialized_end=5511
  _globals['_TMRECORD']._serialized_start=5514
  _globals['_TMRECORD']._serialized_end=5694
# @@protoc_insertion_point(module_scope)
