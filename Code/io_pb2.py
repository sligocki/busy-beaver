# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: io.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x08io.proto\x12\x0b\x62usy_beaver\"1\n\x06\x42igInt\x12\r\n\x03int\x18\x01 \x01(\x04H\x00\x12\r\n\x03str\x18\x02 \x01(\tH\x00\x42\t\n\x07\x62ig_int\"=\n\rTuringMachine\x12\x15\n\rttable_packed\x18\x01 \x01(\x0c\x12\x15\n\rallow_no_halt\x18\x02 \x01(\x08\"\xdb\x01\n\nHaltStatus\x12\x12\n\nis_decided\x18\x01 \x01(\x08\x12\x12\n\nis_halting\x18\x02 \x01(\x08\x12\'\n\nhalt_steps\x18\x03 \x01(\x0b\x32\x13.busy_beaver.BigInt\x12\'\n\nhalt_score\x18\x04 \x01(\x0b\x32\x13.busy_beaver.BigInt\x12\x12\n\nfrom_state\x18\x06 \x01(\x04\x12\x13\n\x0b\x66rom_symbol\x18\x07 \x01(\x04\x12*\n\ninf_reason\x18\x05 \x01(\x0e\x32\x16.busy_beaver.InfReason\"\x85\x01\n\x0fQuasihaltStatus\x12\x12\n\nis_decided\x18\x01 \x01(\x08\x12\x17\n\x0fis_quasihalting\x18\x02 \x01(\x08\x12,\n\x0fquasihalt_steps\x18\x03 \x01(\x0b\x32\x13.busy_beaver.BigInt\x12\x17\n\x0fquasihalt_state\x18\x04 \x01(\x04\"p\n\x08\x42\x42Status\x12,\n\x0bhalt_status\x18\x01 \x01(\x0b\x32\x17.busy_beaver.HaltStatus\x12\x36\n\x10quasihalt_status\x18\x02 \x01(\x0b\x32\x1c.busy_beaver.QuasihaltStatus\"\x8f\x02\n\x0fSimulatorParams\x12\x12\n\nblock_size\x18\t \x01(\x04\x12\x1d\n\x15has_blocksymbol_macro\x18\n \x01(\x08\x12\x11\n\tmax_loops\x18\x01 \x01(\x04\x12\x14\n\x0cmax_time_sec\x18\x02 \x01(\x02\x12\x17\n\x0fmax_tape_blocks\x18\x03 \x01(\x04\x12\x12\n\nuse_prover\x18\x04 \x01(\x08\x12 \n\x18only_log_configs_at_edge\x18\x05 \x01(\x08\x12\x19\n\x11use_limited_rules\x18\x06 \x01(\x08\x12\x1b\n\x13use_recursive_rules\x18\x07 \x01(\x08\x12\x19\n\x11use_collatz_rules\x18\x08 \x01(\x08\"\x1e\n\x08HaltInfo\x12\x12\n\nis_halting\x18\x01 \x01(\x08\"[\n\x12InfMacroRepeatInfo\x12\x14\n\x0cmacro_symbol\x18\x01 \x01(\t\x12\x13\n\x0bmacro_state\x18\x02 \x01(\t\x12\x1a\n\x12macro_dir_is_right\x18\x03 \x01(\x08\"=\n\x10InfChainMoveInfo\x12\x13\n\x0bmacro_state\x18\x01 \x01(\t\x12\x14\n\x0c\x64ir_is_right\x18\x02 \x01(\x08\"\"\n\x12InfProofSystemInfo\x12\x0c\n\x04rule\x18\x01 \x01(\t\"\xbf\x01\n\x0cInfiniteInfo\x12\x37\n\x0cmacro_repeat\x18\x01 \x01(\x0b\x32\x1f.busy_beaver.InfMacroRepeatInfoH\x00\x12\x33\n\nchain_move\x18\x02 \x01(\x0b\x32\x1d.busy_beaver.InfChainMoveInfoH\x00\x12\x37\n\x0cproof_system\x18\x03 \x01(\x0b\x32\x1f.busy_beaver.InfProofSystemInfoH\x00\x42\x08\n\x06reason\"\"\n\rOverLoopsInfo\x12\x11\n\tnum_loops\x18\x01 \x01(\x04\",\n\x0cOverTapeInfo\x12\x1c\n\x14\x63ompressed_tape_size\x18\x01 \x01(\x04\"(\n\x0cOverTimeInfo\x12\x18\n\x10\x65lapsed_time_sec\x18\x01 \x01(\x02\"]\n\x14OverStepsInMacroInfo\x12\x14\n\x0cmacro_symbol\x18\x01 \x01(\t\x12\x13\n\x0bmacro_state\x18\x02 \x01(\t\x12\x1a\n\x12macro_dir_is_right\x18\x03 \x01(\x08\"\xeb\x01\n\x0bUnknownInfo\x12\x30\n\nover_loops\x18\x01 \x01(\x0b\x32\x1a.busy_beaver.OverLoopsInfoH\x00\x12.\n\tover_tape\x18\x02 \x01(\x0b\x32\x19.busy_beaver.OverTapeInfoH\x00\x12.\n\tover_time\x18\x03 \x01(\x0b\x32\x19.busy_beaver.OverTimeInfoH\x00\x12@\n\x13over_steps_in_macro\x18\x04 \x01(\x0b\x32!.busy_beaver.OverStepsInMacroInfoH\x00\x42\x08\n\x06reason\"\xbb\x03\n\x0fSimulatorResult\x12*\n\thalt_info\x18\x01 \x01(\x0b\x32\x15.busy_beaver.HaltInfoH\x00\x12\x32\n\rinfinite_info\x18\x02 \x01(\x0b\x32\x19.busy_beaver.InfiniteInfoH\x00\x12\x30\n\x0cunknown_info\x18\x03 \x01(\x0b\x32\x18.busy_beaver.UnknownInfoH\x00\x12\x17\n\x0f\x65lapsed_time_us\x18\x05 \x01(\x04\x12\x11\n\tnum_loops\x18\x06 \x01(\x04\x12\x17\n\x0fnum_macro_moves\x18\x07 \x01(\x04\x12\x17\n\x0fnum_chain_moves\x18\n \x01(\x04\x12\x16\n\x0enum_rule_moves\x18\x0b \x01(\x04\x12\x17\n\x0flog10_num_steps\x18\x04 \x01(\x04\x12\x18\n\x10num_rules_proven\x18\x08 \x01(\x04\x12\"\n\x1anum_meta_diff_rules_proven\x18\x0c \x01(\x04\x12\x1c\n\x14num_gen_rules_proven\x18\r \x01(\x04\x12\x19\n\x11num_proofs_failed\x18\t \x01(\x04\x42\x10\n\x0e\x65xit_condition\"o\n\rSimulatorInfo\x12\x30\n\nparameters\x18\x01 \x01(\x0b\x32\x1c.busy_beaver.SimulatorParams\x12,\n\x06result\x18\x02 \x01(\x0b\x32\x1c.busy_beaver.SimulatorResult\"y\n\x11\x42lockFinderParams\x12 \n\x18\x63ompression_search_loops\x18\x01 \x01(\x04\x12\x16\n\x0emult_sim_loops\x18\x02 \x01(\x04\x12\x12\n\nextra_mult\x18\x03 \x01(\x04\x12\x16\n\x0emax_block_size\x18\x04 \x01(\x04\"\xad\x02\n\x11\x42lockFinderResult\x12\x17\n\x0f\x62\x65st_block_size\x18\x01 \x01(\x04\x12\x17\n\x0f\x65lapsed_time_us\x18\x02 \x01(\x04\x12\x1d\n\x15least_compressed_loop\x18\x03 \x01(\x04\x12(\n least_compressed_tape_size_chain\x18\x04 \x01(\x04\x12&\n\x1eleast_compressed_tape_size_raw\x18\x05 \x01(\x04\x12#\n\x1b\x62\x65st_compression_block_size\x18\x06 \x01(\x04\x12\"\n\x1a\x62\x65st_compression_tape_size\x18\x07 \x01(\x04\x12\x11\n\tbest_mult\x18\x08 \x01(\x04\x12\x19\n\x11\x62\x65st_chain_factor\x18\t \x01(\x02\"u\n\x0f\x42lockFinderInfo\x12\x32\n\nparameters\x18\x01 \x01(\x0b\x32\x1e.busy_beaver.BlockFinderParams\x12.\n\x06result\x18\x02 \x01(\x0b\x32\x1e.busy_beaver.BlockFinderResult\"F\n\nFilterInfo\x12\x0e\n\x06tested\x18\x01 \x01(\x08\x12\x0f\n\x07success\x18\x02 \x01(\x08\x12\x17\n\x0f\x65lapsed_time_us\x18\x03 \x01(\x04\"F\n\x14LinRecurFilterParams\x12\x11\n\tmax_steps\x18\x01 \x01(\x04\x12\x1b\n\x13\x66ind_min_start_step\x18\x02 \x01(\x08\"t\n\x14LinRecurFilterResult\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x12\n\nstart_step\x18\x02 \x01(\x04\x12\x0e\n\x06period\x18\x03 \x01(\x04\x12\x0e\n\x06offset\x18\x04 \x01(\x12\x12\x17\n\x0f\x65lapsed_time_us\x18\x05 \x01(\x04\"~\n\x12LinRecurFilterInfo\x12\x35\n\nparameters\x18\x01 \x01(\x0b\x32!.busy_beaver.LinRecurFilterParams\x12\x31\n\x06result\x18\x02 \x01(\x0b\x32!.busy_beaver.LinRecurFilterResult\"?\n\tCTLParams\x12\x12\n\nblock_size\x18\x01 \x01(\x04\x12\x0e\n\x06offset\x18\x02 \x01(\x04\x12\x0e\n\x06\x63utoff\x18\x03 \x01(\x04\"H\n\tCTLResult\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x11\n\tnum_iters\x18\x03 \x01(\x04\x12\x17\n\x0f\x65lapsed_time_us\x18\x02 \x01(\x04\"]\n\x07\x43TLInfo\x12*\n\nparameters\x18\x01 \x01(\x0b\x32\x16.busy_beaver.CTLParams\x12&\n\x06result\x18\x02 \x01(\x0b\x32\x16.busy_beaver.CTLResult\"\xaf\x01\n\rCTLFilterInfo\x12$\n\x06\x63tl_as\x18\x05 \x01(\x0b\x32\x14.busy_beaver.CTLInfo\x12&\n\x08\x63tl_as_b\x18\x06 \x01(\x0b\x32\x14.busy_beaver.CTLInfo\x12&\n\x08\x63tl_a_bs\x18\x07 \x01(\x0b\x32\x14.busy_beaver.CTLInfo\x12(\n\nctl_as_b_c\x18\x08 \x01(\x0b\x32\x14.busy_beaver.CTLInfo\"=\n\x15\x42\x61\x63ktrackFilterParams\x12\x11\n\tnum_steps\x18\x01 \x01(\x04\x12\x11\n\tmax_width\x18\x02 \x01(\x04\"z\n\x15\x42\x61\x63ktrackFilterResult\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x11\n\tmax_steps\x18\x03 \x01(\x04\x12\x11\n\tmax_width\x18\x04 \x01(\x04\x12\x11\n\tnum_nodes\x18\x05 \x01(\x04\x12\x17\n\x0f\x65lapsed_time_us\x18\x02 \x01(\x04\"\x81\x01\n\x13\x42\x61\x63ktrackFilterInfo\x12\x36\n\nparameters\x18\x01 \x01(\x0b\x32\".busy_beaver.BacktrackFilterParams\x12\x32\n\x06result\x18\x02 \x01(\x0b\x32\".busy_beaver.BacktrackFilterResult\"\xb6\x01\n\x17\x43losedGraphFilterParams\x12\x16\n\x0emin_block_size\x18\x01 \x01(\x04\x12\x16\n\x0emax_block_size\x18\x02 \x01(\x04\x12\x1d\n\x15searched_all_subtapes\x18\x03 \x01(\x08\x12\x11\n\tmax_steps\x18\x04 \x01(\x04\x12\x11\n\tmax_iters\x18\x05 \x01(\x04\x12\x13\n\x0bmax_configs\x18\x06 \x01(\x04\x12\x11\n\tmax_edges\x18\x07 \x01(\x04\"\xd3\x01\n\x17\x43losedGraphFilterResult\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x12\n\nblock_size\x18\x03 \x01(\x04\x12\x14\n\x0csubtape_size\x18\x04 \x01(\x04\x12\x11\n\tnum_steps\x18\x05 \x01(\x04\x12\x13\n\x0bnum_configs\x18\x06 \x01(\x04\x12\x11\n\tnum_edges\x18\x07 \x01(\x04\x12\x11\n\tnum_iters\x18\x08 \x01(\x04\x12\x16\n\x0e\x66ound_inf_loop\x18\t \x01(\x08\x12\x17\n\x0f\x65lapsed_time_us\x18\x02 \x01(\x04\"\x87\x01\n\x15\x43losedGraphFilterInfo\x12\x38\n\nparameters\x18\x01 \x01(\x0b\x32$.busy_beaver.ClosedGraphFilterParams\x12\x34\n\x06result\x18\x02 \x01(\x0b\x32$.busy_beaver.ClosedGraphFilterResult\"\xf1\x02\n\rFilterResults\x12-\n\tsimulator\x18\x01 \x01(\x0b\x32\x1a.busy_beaver.SimulatorInfo\x12\x32\n\x0c\x62lock_finder\x18\x02 \x01(\x0b\x32\x1c.busy_beaver.BlockFinderInfo\x12\x31\n\x10reverse_engineer\x18\x03 \x01(\x0b\x32\x17.busy_beaver.FilterInfo\x12\x32\n\tlin_recur\x18\x04 \x01(\x0b\x32\x1f.busy_beaver.LinRecurFilterInfo\x12\'\n\x03\x63tl\x18\x05 \x01(\x0b\x32\x1a.busy_beaver.CTLFilterInfo\x12\x33\n\tbacktrack\x18\x06 \x01(\x0b\x32 .busy_beaver.BacktrackFilterInfo\x12\x38\n\x0c\x63losed_graph\x18\x07 \x01(\x0b\x32\".busy_beaver.ClosedGraphFilterInfo\"\xb4\x01\n\x08TMRecord\x12\x14\n\x0cspec_version\x18\x01 \x01(\x04\x12&\n\x02tm\x18\x02 \x01(\x0b\x32\x1a.busy_beaver.TuringMachine\x12%\n\x06status\x18\x03 \x01(\x0b\x32\x15.busy_beaver.BBStatus\x12*\n\x06\x66ilter\x18\x04 \x01(\x0b\x32\x1a.busy_beaver.FilterResults\x12\x17\n\x0f\x65lapsed_time_us\x18\x05 \x01(\x04*\xc1\x01\n\tInfReason\x12\x13\n\x0fINF_UNSPECIFIED\x10\x00\x12\x12\n\x0eINF_MACRO_STEP\x10\x01\x12\x12\n\x0eINF_CHAIN_STEP\x10\x02\x12\x14\n\x10INF_PROOF_SYSTEM\x10\x03\x12\x18\n\x14INF_REVERSE_ENGINEER\x10\x04\x12\x11\n\rINF_LIN_RECUR\x10\x05\x12\x0b\n\x07INF_CTL\x10\x06\x12\x11\n\rINF_BACKTRACK\x10\x07\x12\x14\n\x10INF_CLOSED_GRAPH\x10\x08\x62\x06proto3')

_INFREASON = DESCRIPTOR.enum_types_by_name['InfReason']
InfReason = enum_type_wrapper.EnumTypeWrapper(_INFREASON)
INF_UNSPECIFIED = 0
INF_MACRO_STEP = 1
INF_CHAIN_STEP = 2
INF_PROOF_SYSTEM = 3
INF_REVERSE_ENGINEER = 4
INF_LIN_RECUR = 5
INF_CTL = 6
INF_BACKTRACK = 7
INF_CLOSED_GRAPH = 8


_BIGINT = DESCRIPTOR.message_types_by_name['BigInt']
_TURINGMACHINE = DESCRIPTOR.message_types_by_name['TuringMachine']
_HALTSTATUS = DESCRIPTOR.message_types_by_name['HaltStatus']
_QUASIHALTSTATUS = DESCRIPTOR.message_types_by_name['QuasihaltStatus']
_BBSTATUS = DESCRIPTOR.message_types_by_name['BBStatus']
_SIMULATORPARAMS = DESCRIPTOR.message_types_by_name['SimulatorParams']
_HALTINFO = DESCRIPTOR.message_types_by_name['HaltInfo']
_INFMACROREPEATINFO = DESCRIPTOR.message_types_by_name['InfMacroRepeatInfo']
_INFCHAINMOVEINFO = DESCRIPTOR.message_types_by_name['InfChainMoveInfo']
_INFPROOFSYSTEMINFO = DESCRIPTOR.message_types_by_name['InfProofSystemInfo']
_INFINITEINFO = DESCRIPTOR.message_types_by_name['InfiniteInfo']
_OVERLOOPSINFO = DESCRIPTOR.message_types_by_name['OverLoopsInfo']
_OVERTAPEINFO = DESCRIPTOR.message_types_by_name['OverTapeInfo']
_OVERTIMEINFO = DESCRIPTOR.message_types_by_name['OverTimeInfo']
_OVERSTEPSINMACROINFO = DESCRIPTOR.message_types_by_name['OverStepsInMacroInfo']
_UNKNOWNINFO = DESCRIPTOR.message_types_by_name['UnknownInfo']
_SIMULATORRESULT = DESCRIPTOR.message_types_by_name['SimulatorResult']
_SIMULATORINFO = DESCRIPTOR.message_types_by_name['SimulatorInfo']
_BLOCKFINDERPARAMS = DESCRIPTOR.message_types_by_name['BlockFinderParams']
_BLOCKFINDERRESULT = DESCRIPTOR.message_types_by_name['BlockFinderResult']
_BLOCKFINDERINFO = DESCRIPTOR.message_types_by_name['BlockFinderInfo']
_FILTERINFO = DESCRIPTOR.message_types_by_name['FilterInfo']
_LINRECURFILTERPARAMS = DESCRIPTOR.message_types_by_name['LinRecurFilterParams']
_LINRECURFILTERRESULT = DESCRIPTOR.message_types_by_name['LinRecurFilterResult']
_LINRECURFILTERINFO = DESCRIPTOR.message_types_by_name['LinRecurFilterInfo']
_CTLPARAMS = DESCRIPTOR.message_types_by_name['CTLParams']
_CTLRESULT = DESCRIPTOR.message_types_by_name['CTLResult']
_CTLINFO = DESCRIPTOR.message_types_by_name['CTLInfo']
_CTLFILTERINFO = DESCRIPTOR.message_types_by_name['CTLFilterInfo']
_BACKTRACKFILTERPARAMS = DESCRIPTOR.message_types_by_name['BacktrackFilterParams']
_BACKTRACKFILTERRESULT = DESCRIPTOR.message_types_by_name['BacktrackFilterResult']
_BACKTRACKFILTERINFO = DESCRIPTOR.message_types_by_name['BacktrackFilterInfo']
_CLOSEDGRAPHFILTERPARAMS = DESCRIPTOR.message_types_by_name['ClosedGraphFilterParams']
_CLOSEDGRAPHFILTERRESULT = DESCRIPTOR.message_types_by_name['ClosedGraphFilterResult']
_CLOSEDGRAPHFILTERINFO = DESCRIPTOR.message_types_by_name['ClosedGraphFilterInfo']
_FILTERRESULTS = DESCRIPTOR.message_types_by_name['FilterResults']
_TMRECORD = DESCRIPTOR.message_types_by_name['TMRecord']
BigInt = _reflection.GeneratedProtocolMessageType('BigInt', (_message.Message,), {
  'DESCRIPTOR' : _BIGINT,
  '__module__' : 'io_pb2'
  # @@protoc_insertion_point(class_scope:busy_beaver.BigInt)
  })
_sym_db.RegisterMessage(BigInt)

TuringMachine = _reflection.GeneratedProtocolMessageType('TuringMachine', (_message.Message,), {
  'DESCRIPTOR' : _TURINGMACHINE,
  '__module__' : 'io_pb2'
  # @@protoc_insertion_point(class_scope:busy_beaver.TuringMachine)
  })
_sym_db.RegisterMessage(TuringMachine)

HaltStatus = _reflection.GeneratedProtocolMessageType('HaltStatus', (_message.Message,), {
  'DESCRIPTOR' : _HALTSTATUS,
  '__module__' : 'io_pb2'
  # @@protoc_insertion_point(class_scope:busy_beaver.HaltStatus)
  })
_sym_db.RegisterMessage(HaltStatus)

QuasihaltStatus = _reflection.GeneratedProtocolMessageType('QuasihaltStatus', (_message.Message,), {
  'DESCRIPTOR' : _QUASIHALTSTATUS,
  '__module__' : 'io_pb2'
  # @@protoc_insertion_point(class_scope:busy_beaver.QuasihaltStatus)
  })
_sym_db.RegisterMessage(QuasihaltStatus)

BBStatus = _reflection.GeneratedProtocolMessageType('BBStatus', (_message.Message,), {
  'DESCRIPTOR' : _BBSTATUS,
  '__module__' : 'io_pb2'
  # @@protoc_insertion_point(class_scope:busy_beaver.BBStatus)
  })
_sym_db.RegisterMessage(BBStatus)

SimulatorParams = _reflection.GeneratedProtocolMessageType('SimulatorParams', (_message.Message,), {
  'DESCRIPTOR' : _SIMULATORPARAMS,
  '__module__' : 'io_pb2'
  # @@protoc_insertion_point(class_scope:busy_beaver.SimulatorParams)
  })
_sym_db.RegisterMessage(SimulatorParams)

HaltInfo = _reflection.GeneratedProtocolMessageType('HaltInfo', (_message.Message,), {
  'DESCRIPTOR' : _HALTINFO,
  '__module__' : 'io_pb2'
  # @@protoc_insertion_point(class_scope:busy_beaver.HaltInfo)
  })
_sym_db.RegisterMessage(HaltInfo)

InfMacroRepeatInfo = _reflection.GeneratedProtocolMessageType('InfMacroRepeatInfo', (_message.Message,), {
  'DESCRIPTOR' : _INFMACROREPEATINFO,
  '__module__' : 'io_pb2'
  # @@protoc_insertion_point(class_scope:busy_beaver.InfMacroRepeatInfo)
  })
_sym_db.RegisterMessage(InfMacroRepeatInfo)

InfChainMoveInfo = _reflection.GeneratedProtocolMessageType('InfChainMoveInfo', (_message.Message,), {
  'DESCRIPTOR' : _INFCHAINMOVEINFO,
  '__module__' : 'io_pb2'
  # @@protoc_insertion_point(class_scope:busy_beaver.InfChainMoveInfo)
  })
_sym_db.RegisterMessage(InfChainMoveInfo)

InfProofSystemInfo = _reflection.GeneratedProtocolMessageType('InfProofSystemInfo', (_message.Message,), {
  'DESCRIPTOR' : _INFPROOFSYSTEMINFO,
  '__module__' : 'io_pb2'
  # @@protoc_insertion_point(class_scope:busy_beaver.InfProofSystemInfo)
  })
_sym_db.RegisterMessage(InfProofSystemInfo)

InfiniteInfo = _reflection.GeneratedProtocolMessageType('InfiniteInfo', (_message.Message,), {
  'DESCRIPTOR' : _INFINITEINFO,
  '__module__' : 'io_pb2'
  # @@protoc_insertion_point(class_scope:busy_beaver.InfiniteInfo)
  })
_sym_db.RegisterMessage(InfiniteInfo)

OverLoopsInfo = _reflection.GeneratedProtocolMessageType('OverLoopsInfo', (_message.Message,), {
  'DESCRIPTOR' : _OVERLOOPSINFO,
  '__module__' : 'io_pb2'
  # @@protoc_insertion_point(class_scope:busy_beaver.OverLoopsInfo)
  })
_sym_db.RegisterMessage(OverLoopsInfo)

OverTapeInfo = _reflection.GeneratedProtocolMessageType('OverTapeInfo', (_message.Message,), {
  'DESCRIPTOR' : _OVERTAPEINFO,
  '__module__' : 'io_pb2'
  # @@protoc_insertion_point(class_scope:busy_beaver.OverTapeInfo)
  })
_sym_db.RegisterMessage(OverTapeInfo)

OverTimeInfo = _reflection.GeneratedProtocolMessageType('OverTimeInfo', (_message.Message,), {
  'DESCRIPTOR' : _OVERTIMEINFO,
  '__module__' : 'io_pb2'
  # @@protoc_insertion_point(class_scope:busy_beaver.OverTimeInfo)
  })
_sym_db.RegisterMessage(OverTimeInfo)

OverStepsInMacroInfo = _reflection.GeneratedProtocolMessageType('OverStepsInMacroInfo', (_message.Message,), {
  'DESCRIPTOR' : _OVERSTEPSINMACROINFO,
  '__module__' : 'io_pb2'
  # @@protoc_insertion_point(class_scope:busy_beaver.OverStepsInMacroInfo)
  })
_sym_db.RegisterMessage(OverStepsInMacroInfo)

UnknownInfo = _reflection.GeneratedProtocolMessageType('UnknownInfo', (_message.Message,), {
  'DESCRIPTOR' : _UNKNOWNINFO,
  '__module__' : 'io_pb2'
  # @@protoc_insertion_point(class_scope:busy_beaver.UnknownInfo)
  })
_sym_db.RegisterMessage(UnknownInfo)

SimulatorResult = _reflection.GeneratedProtocolMessageType('SimulatorResult', (_message.Message,), {
  'DESCRIPTOR' : _SIMULATORRESULT,
  '__module__' : 'io_pb2'
  # @@protoc_insertion_point(class_scope:busy_beaver.SimulatorResult)
  })
_sym_db.RegisterMessage(SimulatorResult)

SimulatorInfo = _reflection.GeneratedProtocolMessageType('SimulatorInfo', (_message.Message,), {
  'DESCRIPTOR' : _SIMULATORINFO,
  '__module__' : 'io_pb2'
  # @@protoc_insertion_point(class_scope:busy_beaver.SimulatorInfo)
  })
_sym_db.RegisterMessage(SimulatorInfo)

BlockFinderParams = _reflection.GeneratedProtocolMessageType('BlockFinderParams', (_message.Message,), {
  'DESCRIPTOR' : _BLOCKFINDERPARAMS,
  '__module__' : 'io_pb2'
  # @@protoc_insertion_point(class_scope:busy_beaver.BlockFinderParams)
  })
_sym_db.RegisterMessage(BlockFinderParams)

BlockFinderResult = _reflection.GeneratedProtocolMessageType('BlockFinderResult', (_message.Message,), {
  'DESCRIPTOR' : _BLOCKFINDERRESULT,
  '__module__' : 'io_pb2'
  # @@protoc_insertion_point(class_scope:busy_beaver.BlockFinderResult)
  })
_sym_db.RegisterMessage(BlockFinderResult)

BlockFinderInfo = _reflection.GeneratedProtocolMessageType('BlockFinderInfo', (_message.Message,), {
  'DESCRIPTOR' : _BLOCKFINDERINFO,
  '__module__' : 'io_pb2'
  # @@protoc_insertion_point(class_scope:busy_beaver.BlockFinderInfo)
  })
_sym_db.RegisterMessage(BlockFinderInfo)

FilterInfo = _reflection.GeneratedProtocolMessageType('FilterInfo', (_message.Message,), {
  'DESCRIPTOR' : _FILTERINFO,
  '__module__' : 'io_pb2'
  # @@protoc_insertion_point(class_scope:busy_beaver.FilterInfo)
  })
_sym_db.RegisterMessage(FilterInfo)

LinRecurFilterParams = _reflection.GeneratedProtocolMessageType('LinRecurFilterParams', (_message.Message,), {
  'DESCRIPTOR' : _LINRECURFILTERPARAMS,
  '__module__' : 'io_pb2'
  # @@protoc_insertion_point(class_scope:busy_beaver.LinRecurFilterParams)
  })
_sym_db.RegisterMessage(LinRecurFilterParams)

LinRecurFilterResult = _reflection.GeneratedProtocolMessageType('LinRecurFilterResult', (_message.Message,), {
  'DESCRIPTOR' : _LINRECURFILTERRESULT,
  '__module__' : 'io_pb2'
  # @@protoc_insertion_point(class_scope:busy_beaver.LinRecurFilterResult)
  })
_sym_db.RegisterMessage(LinRecurFilterResult)

LinRecurFilterInfo = _reflection.GeneratedProtocolMessageType('LinRecurFilterInfo', (_message.Message,), {
  'DESCRIPTOR' : _LINRECURFILTERINFO,
  '__module__' : 'io_pb2'
  # @@protoc_insertion_point(class_scope:busy_beaver.LinRecurFilterInfo)
  })
_sym_db.RegisterMessage(LinRecurFilterInfo)

CTLParams = _reflection.GeneratedProtocolMessageType('CTLParams', (_message.Message,), {
  'DESCRIPTOR' : _CTLPARAMS,
  '__module__' : 'io_pb2'
  # @@protoc_insertion_point(class_scope:busy_beaver.CTLParams)
  })
_sym_db.RegisterMessage(CTLParams)

CTLResult = _reflection.GeneratedProtocolMessageType('CTLResult', (_message.Message,), {
  'DESCRIPTOR' : _CTLRESULT,
  '__module__' : 'io_pb2'
  # @@protoc_insertion_point(class_scope:busy_beaver.CTLResult)
  })
_sym_db.RegisterMessage(CTLResult)

CTLInfo = _reflection.GeneratedProtocolMessageType('CTLInfo', (_message.Message,), {
  'DESCRIPTOR' : _CTLINFO,
  '__module__' : 'io_pb2'
  # @@protoc_insertion_point(class_scope:busy_beaver.CTLInfo)
  })
_sym_db.RegisterMessage(CTLInfo)

CTLFilterInfo = _reflection.GeneratedProtocolMessageType('CTLFilterInfo', (_message.Message,), {
  'DESCRIPTOR' : _CTLFILTERINFO,
  '__module__' : 'io_pb2'
  # @@protoc_insertion_point(class_scope:busy_beaver.CTLFilterInfo)
  })
_sym_db.RegisterMessage(CTLFilterInfo)

BacktrackFilterParams = _reflection.GeneratedProtocolMessageType('BacktrackFilterParams', (_message.Message,), {
  'DESCRIPTOR' : _BACKTRACKFILTERPARAMS,
  '__module__' : 'io_pb2'
  # @@protoc_insertion_point(class_scope:busy_beaver.BacktrackFilterParams)
  })
_sym_db.RegisterMessage(BacktrackFilterParams)

BacktrackFilterResult = _reflection.GeneratedProtocolMessageType('BacktrackFilterResult', (_message.Message,), {
  'DESCRIPTOR' : _BACKTRACKFILTERRESULT,
  '__module__' : 'io_pb2'
  # @@protoc_insertion_point(class_scope:busy_beaver.BacktrackFilterResult)
  })
_sym_db.RegisterMessage(BacktrackFilterResult)

BacktrackFilterInfo = _reflection.GeneratedProtocolMessageType('BacktrackFilterInfo', (_message.Message,), {
  'DESCRIPTOR' : _BACKTRACKFILTERINFO,
  '__module__' : 'io_pb2'
  # @@protoc_insertion_point(class_scope:busy_beaver.BacktrackFilterInfo)
  })
_sym_db.RegisterMessage(BacktrackFilterInfo)

ClosedGraphFilterParams = _reflection.GeneratedProtocolMessageType('ClosedGraphFilterParams', (_message.Message,), {
  'DESCRIPTOR' : _CLOSEDGRAPHFILTERPARAMS,
  '__module__' : 'io_pb2'
  # @@protoc_insertion_point(class_scope:busy_beaver.ClosedGraphFilterParams)
  })
_sym_db.RegisterMessage(ClosedGraphFilterParams)

ClosedGraphFilterResult = _reflection.GeneratedProtocolMessageType('ClosedGraphFilterResult', (_message.Message,), {
  'DESCRIPTOR' : _CLOSEDGRAPHFILTERRESULT,
  '__module__' : 'io_pb2'
  # @@protoc_insertion_point(class_scope:busy_beaver.ClosedGraphFilterResult)
  })
_sym_db.RegisterMessage(ClosedGraphFilterResult)

ClosedGraphFilterInfo = _reflection.GeneratedProtocolMessageType('ClosedGraphFilterInfo', (_message.Message,), {
  'DESCRIPTOR' : _CLOSEDGRAPHFILTERINFO,
  '__module__' : 'io_pb2'
  # @@protoc_insertion_point(class_scope:busy_beaver.ClosedGraphFilterInfo)
  })
_sym_db.RegisterMessage(ClosedGraphFilterInfo)

FilterResults = _reflection.GeneratedProtocolMessageType('FilterResults', (_message.Message,), {
  'DESCRIPTOR' : _FILTERRESULTS,
  '__module__' : 'io_pb2'
  # @@protoc_insertion_point(class_scope:busy_beaver.FilterResults)
  })
_sym_db.RegisterMessage(FilterResults)

TMRecord = _reflection.GeneratedProtocolMessageType('TMRecord', (_message.Message,), {
  'DESCRIPTOR' : _TMRECORD,
  '__module__' : 'io_pb2'
  # @@protoc_insertion_point(class_scope:busy_beaver.TMRecord)
  })
_sym_db.RegisterMessage(TMRecord)

if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _INFREASON._serialized_start=5079
  _INFREASON._serialized_end=5272
  _BIGINT._serialized_start=25
  _BIGINT._serialized_end=74
  _TURINGMACHINE._serialized_start=76
  _TURINGMACHINE._serialized_end=137
  _HALTSTATUS._serialized_start=140
  _HALTSTATUS._serialized_end=359
  _QUASIHALTSTATUS._serialized_start=362
  _QUASIHALTSTATUS._serialized_end=495
  _BBSTATUS._serialized_start=497
  _BBSTATUS._serialized_end=609
  _SIMULATORPARAMS._serialized_start=612
  _SIMULATORPARAMS._serialized_end=883
  _HALTINFO._serialized_start=885
  _HALTINFO._serialized_end=915
  _INFMACROREPEATINFO._serialized_start=917
  _INFMACROREPEATINFO._serialized_end=1008
  _INFCHAINMOVEINFO._serialized_start=1010
  _INFCHAINMOVEINFO._serialized_end=1071
  _INFPROOFSYSTEMINFO._serialized_start=1073
  _INFPROOFSYSTEMINFO._serialized_end=1107
  _INFINITEINFO._serialized_start=1110
  _INFINITEINFO._serialized_end=1301
  _OVERLOOPSINFO._serialized_start=1303
  _OVERLOOPSINFO._serialized_end=1337
  _OVERTAPEINFO._serialized_start=1339
  _OVERTAPEINFO._serialized_end=1383
  _OVERTIMEINFO._serialized_start=1385
  _OVERTIMEINFO._serialized_end=1425
  _OVERSTEPSINMACROINFO._serialized_start=1427
  _OVERSTEPSINMACROINFO._serialized_end=1520
  _UNKNOWNINFO._serialized_start=1523
  _UNKNOWNINFO._serialized_end=1758
  _SIMULATORRESULT._serialized_start=1761
  _SIMULATORRESULT._serialized_end=2204
  _SIMULATORINFO._serialized_start=2206
  _SIMULATORINFO._serialized_end=2317
  _BLOCKFINDERPARAMS._serialized_start=2319
  _BLOCKFINDERPARAMS._serialized_end=2440
  _BLOCKFINDERRESULT._serialized_start=2443
  _BLOCKFINDERRESULT._serialized_end=2744
  _BLOCKFINDERINFO._serialized_start=2746
  _BLOCKFINDERINFO._serialized_end=2863
  _FILTERINFO._serialized_start=2865
  _FILTERINFO._serialized_end=2935
  _LINRECURFILTERPARAMS._serialized_start=2937
  _LINRECURFILTERPARAMS._serialized_end=3007
  _LINRECURFILTERRESULT._serialized_start=3009
  _LINRECURFILTERRESULT._serialized_end=3125
  _LINRECURFILTERINFO._serialized_start=3127
  _LINRECURFILTERINFO._serialized_end=3253
  _CTLPARAMS._serialized_start=3255
  _CTLPARAMS._serialized_end=3318
  _CTLRESULT._serialized_start=3320
  _CTLRESULT._serialized_end=3392
  _CTLINFO._serialized_start=3394
  _CTLINFO._serialized_end=3487
  _CTLFILTERINFO._serialized_start=3490
  _CTLFILTERINFO._serialized_end=3665
  _BACKTRACKFILTERPARAMS._serialized_start=3667
  _BACKTRACKFILTERPARAMS._serialized_end=3728
  _BACKTRACKFILTERRESULT._serialized_start=3730
  _BACKTRACKFILTERRESULT._serialized_end=3852
  _BACKTRACKFILTERINFO._serialized_start=3855
  _BACKTRACKFILTERINFO._serialized_end=3984
  _CLOSEDGRAPHFILTERPARAMS._serialized_start=3987
  _CLOSEDGRAPHFILTERPARAMS._serialized_end=4169
  _CLOSEDGRAPHFILTERRESULT._serialized_start=4172
  _CLOSEDGRAPHFILTERRESULT._serialized_end=4383
  _CLOSEDGRAPHFILTERINFO._serialized_start=4386
  _CLOSEDGRAPHFILTERINFO._serialized_end=4521
  _FILTERRESULTS._serialized_start=4524
  _FILTERRESULTS._serialized_end=4893
  _TMRECORD._serialized_start=4896
  _TMRECORD._serialized_end=5076
# @@protoc_insertion_point(module_scope)
