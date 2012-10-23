#
# __init__.py
#
"""
Simulation code for Heiner Marxen's Macro Machine/Chain Tape representation.

Turing_Machine
    Contains the generic Turing machine representation and extension classes
    to support both block-symbol and back-symbol "macro machines".

Tape
    Contains the "chained tape" representation which separates the tape into
    left and right halves and stores the symbols in run-length encoding, so
    each tape element is a symbol and a number-of-repetitions. The TM head
    is considered to be pointed towards the left or right half-tape rather than
    sitting on one side or the other.
        For example, the halting tape of the champion 5x2 Busy Beaver is:
        000^Inf 101^1 001^1  Z>  001^4094 100^1 000^Inf

Simulator
    Simulates a Turing_Machine on a Tape. Applies both atomic TM steps (read
    symbol, write symbol, move, change state) and "chain steps" where, in
    certain cases, the simulation can jump across a whole block of symbols from
    the "chained tape" representation.
        For example: if  A> 1 -> 0 A>, then  A> 1^305 -> 0^305 A>
    If enabled with a Proof_System, the Simulator may also find and apply
    more complex rules.

Proof_System
    Records simulation configurations and tries to notice and prove rules.
        For example:
            000^Inf 111^(a + 1)  B>  001^(b + 4) 100^1 000^Inf
        Goes to:
            000^Inf 111^(a + 5)  B>  001^(b + 1) 100^1 000^Inf
        In (18a + 99) steps (for all integers a,b >= 0).

Block_Finder
    Heuristic for finding the best "block size" for simulating macro machines.
    It runs two passes, first finding the block size that compresses the tape
    best. Then running simulations at various multiples of that size and seeing
    which is the most effective.
"""
