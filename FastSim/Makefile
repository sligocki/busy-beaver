CFLAGS = -g -O2
CXXFLAGS = -g -O2
LDFLAGS = -g -O2
LIBS = -lgmpxx -lgmp -lm

exe1 = Quick_Sim
src1 = Quick_Sim.cpp                 \
       TTable.cpp                    \
       Tape.cpp                      \
       Simple_Turing_Machine.cpp     \
       Block_Finder.cpp              \
       Macro_Turing_Machine.cpp      \
       Backsymbol_Turing_Machine.cpp \
       Chain_Simulator.cpp           \
       Proof_System.cpp              \
       General_Chain_Simulator.cpp   \
       Exception.cpp                 \
       Expression.cpp	
obj1 = Quick_Sim.o                   \
       TTable.o                      \
       Tape.o                        \
       Simple_Turing_Machine.o       \
       Block_Finder.o                \
       Macro_Turing_Machine.o        \
       Backsymbol_Turing_Machine.o   \
       Chain_Simulator.o             \
       Proof_System.o                \
       General_Chain_Simulator.o     \
       Exception.o                   \
       Expression.o

all: $(exe1)

$(exe1): $(obj1)
	$(CXX) $(LDFLAGS) -o $(exe1) $(obj1) $(LIBS)

depend:
	makedepend $(CXXFLAGS) $(src1)

tar:
	tar jcf code.tar.bz2 Makefile $(src1) $(hdr1) Python/*.py Python/*.tm

clean:
	/bin/rm -f $(exe1) *.o

# DO NOT DELETE

Quick_Sim.o: Define.h /usr/include/boost/shared_ptr.hpp
Quick_Sim.o: /usr/include/boost/config.hpp /usr/include/boost/config/user.hpp
Quick_Sim.o: /usr/include/boost/config/select_compiler_config.hpp
Quick_Sim.o: /usr/include/boost/config/compiler/gcc.hpp
Quick_Sim.o: /usr/include/boost/config/select_stdlib_config.hpp
Quick_Sim.o: /usr/include/boost/config/select_platform_config.hpp
Quick_Sim.o: /usr/include/boost/config/suffix.hpp /usr/include/limits.h
Quick_Sim.o: /usr/include/features.h /usr/include/sys/cdefs.h
Quick_Sim.o: /usr/include/bits/wordsize.h /usr/include/gnu/stubs.h
Quick_Sim.o: /usr/include/gnu/stubs.h /usr/include/bits/posix1_lim.h
Quick_Sim.o: /usr/include/bits/local_lim.h /usr/include/linux/limits.h
Quick_Sim.o: /usr/include/bits/posix2_lim.h /usr/include/boost/assert.hpp
Quick_Sim.o: /usr/include/assert.h /usr/include/boost/checked_delete.hpp
Quick_Sim.o: /usr/include/boost/throw_exception.hpp
Quick_Sim.o: /usr/include/boost/config.hpp
Quick_Sim.o: /usr/include/boost/detail/shared_count.hpp
Quick_Sim.o: /usr/include/boost/detail/bad_weak_ptr.hpp
Quick_Sim.o: /usr/include/boost/detail/sp_counted_base.hpp
Quick_Sim.o: /usr/include/boost/detail/sp_counted_base_gcc_x86.hpp
Quick_Sim.o: /usr/include/boost/detail/sp_counted_impl.hpp
Quick_Sim.o: /usr/include/boost/detail/workaround.hpp /usr/include/gmpxx.h
Quick_Sim.o: /usr/include/gmp.h Exception.h TTable.h Turing_Machine.h
Quick_Sim.o: Simple_Turing_Machine.h Block_Finder.h Macro_Turing_Machine.h
Quick_Sim.o: Backsymbol_Turing_Machine.h Chain_Simulator.h Tape.h
Quick_Sim.o: TapeImplem.h Proof_System.h Expression.h
TTable.o: TTable.h Define.h /usr/include/boost/shared_ptr.hpp
TTable.o: /usr/include/boost/config.hpp /usr/include/boost/config/user.hpp
TTable.o: /usr/include/boost/config/select_compiler_config.hpp
TTable.o: /usr/include/boost/config/compiler/gcc.hpp
TTable.o: /usr/include/boost/config/select_stdlib_config.hpp
TTable.o: /usr/include/boost/config/select_platform_config.hpp
TTable.o: /usr/include/boost/config/suffix.hpp /usr/include/limits.h
TTable.o: /usr/include/features.h /usr/include/sys/cdefs.h
TTable.o: /usr/include/bits/wordsize.h /usr/include/gnu/stubs.h
TTable.o: /usr/include/gnu/stubs.h /usr/include/bits/posix1_lim.h
TTable.o: /usr/include/bits/local_lim.h /usr/include/linux/limits.h
TTable.o: /usr/include/bits/posix2_lim.h /usr/include/boost/assert.hpp
TTable.o: /usr/include/assert.h /usr/include/boost/checked_delete.hpp
TTable.o: /usr/include/boost/throw_exception.hpp
TTable.o: /usr/include/boost/config.hpp
TTable.o: /usr/include/boost/detail/shared_count.hpp
TTable.o: /usr/include/boost/detail/bad_weak_ptr.hpp
TTable.o: /usr/include/boost/detail/sp_counted_base.hpp
TTable.o: /usr/include/boost/detail/sp_counted_base_gcc_x86.hpp
TTable.o: /usr/include/boost/detail/sp_counted_impl.hpp
TTable.o: /usr/include/boost/detail/workaround.hpp /usr/include/gmpxx.h
TTable.o: /usr/include/gmp.h Exception.h
Tape.o: Tape.h Define.h /usr/include/boost/shared_ptr.hpp
Tape.o: /usr/include/boost/config.hpp /usr/include/boost/config/user.hpp
Tape.o: /usr/include/boost/config/select_compiler_config.hpp
Tape.o: /usr/include/boost/config/compiler/gcc.hpp
Tape.o: /usr/include/boost/config/select_stdlib_config.hpp
Tape.o: /usr/include/boost/config/select_platform_config.hpp
Tape.o: /usr/include/boost/config/suffix.hpp /usr/include/limits.h
Tape.o: /usr/include/features.h /usr/include/sys/cdefs.h
Tape.o: /usr/include/bits/wordsize.h /usr/include/gnu/stubs.h
Tape.o: /usr/include/gnu/stubs.h /usr/include/bits/posix1_lim.h
Tape.o: /usr/include/bits/local_lim.h /usr/include/linux/limits.h
Tape.o: /usr/include/bits/posix2_lim.h /usr/include/boost/assert.hpp
Tape.o: /usr/include/assert.h /usr/include/boost/checked_delete.hpp
Tape.o: /usr/include/boost/throw_exception.hpp /usr/include/boost/config.hpp
Tape.o: /usr/include/boost/detail/shared_count.hpp
Tape.o: /usr/include/boost/detail/bad_weak_ptr.hpp
Tape.o: /usr/include/boost/detail/sp_counted_base.hpp
Tape.o: /usr/include/boost/detail/sp_counted_base_gcc_x86.hpp
Tape.o: /usr/include/boost/detail/sp_counted_impl.hpp
Tape.o: /usr/include/boost/detail/workaround.hpp /usr/include/gmpxx.h
Tape.o: /usr/include/gmp.h Exception.h Turing_Machine.h TapeImplem.h
Simple_Turing_Machine.o: Simple_Turing_Machine.h Define.h
Simple_Turing_Machine.o: /usr/include/boost/shared_ptr.hpp
Simple_Turing_Machine.o: /usr/include/boost/config.hpp
Simple_Turing_Machine.o: /usr/include/boost/config/user.hpp
Simple_Turing_Machine.o: /usr/include/boost/config/select_compiler_config.hpp
Simple_Turing_Machine.o: /usr/include/boost/config/compiler/gcc.hpp
Simple_Turing_Machine.o: /usr/include/boost/config/select_stdlib_config.hpp
Simple_Turing_Machine.o: /usr/include/boost/config/select_platform_config.hpp
Simple_Turing_Machine.o: /usr/include/boost/config/suffix.hpp
Simple_Turing_Machine.o: /usr/include/limits.h /usr/include/features.h
Simple_Turing_Machine.o: /usr/include/sys/cdefs.h
Simple_Turing_Machine.o: /usr/include/bits/wordsize.h
Simple_Turing_Machine.o: /usr/include/gnu/stubs.h /usr/include/gnu/stubs.h
Simple_Turing_Machine.o: /usr/include/bits/posix1_lim.h
Simple_Turing_Machine.o: /usr/include/bits/local_lim.h
Simple_Turing_Machine.o: /usr/include/linux/limits.h
Simple_Turing_Machine.o: /usr/include/bits/posix2_lim.h
Simple_Turing_Machine.o: /usr/include/boost/assert.hpp /usr/include/assert.h
Simple_Turing_Machine.o: /usr/include/boost/checked_delete.hpp
Simple_Turing_Machine.o: /usr/include/boost/throw_exception.hpp
Simple_Turing_Machine.o: /usr/include/boost/config.hpp
Simple_Turing_Machine.o: /usr/include/boost/detail/shared_count.hpp
Simple_Turing_Machine.o: /usr/include/boost/detail/bad_weak_ptr.hpp
Simple_Turing_Machine.o: /usr/include/boost/detail/sp_counted_base.hpp
Simple_Turing_Machine.o: /usr/include/boost/detail/sp_counted_base_gcc_x86.hpp
Simple_Turing_Machine.o: /usr/include/boost/detail/sp_counted_impl.hpp
Simple_Turing_Machine.o: /usr/include/boost/detail/workaround.hpp
Simple_Turing_Machine.o: /usr/include/gmpxx.h /usr/include/gmp.h Exception.h
Simple_Turing_Machine.o: TTable.h Turing_Machine.h
Block_Finder.o: Block_Finder.h Define.h /usr/include/boost/shared_ptr.hpp
Block_Finder.o: /usr/include/boost/config.hpp
Block_Finder.o: /usr/include/boost/config/user.hpp
Block_Finder.o: /usr/include/boost/config/select_compiler_config.hpp
Block_Finder.o: /usr/include/boost/config/compiler/gcc.hpp
Block_Finder.o: /usr/include/boost/config/select_stdlib_config.hpp
Block_Finder.o: /usr/include/boost/config/select_platform_config.hpp
Block_Finder.o: /usr/include/boost/config/suffix.hpp /usr/include/limits.h
Block_Finder.o: /usr/include/features.h /usr/include/sys/cdefs.h
Block_Finder.o: /usr/include/bits/wordsize.h /usr/include/gnu/stubs.h
Block_Finder.o: /usr/include/gnu/stubs.h /usr/include/bits/posix1_lim.h
Block_Finder.o: /usr/include/bits/local_lim.h /usr/include/linux/limits.h
Block_Finder.o: /usr/include/bits/posix2_lim.h /usr/include/boost/assert.hpp
Block_Finder.o: /usr/include/assert.h /usr/include/boost/checked_delete.hpp
Block_Finder.o: /usr/include/boost/throw_exception.hpp
Block_Finder.o: /usr/include/boost/config.hpp
Block_Finder.o: /usr/include/boost/detail/shared_count.hpp
Block_Finder.o: /usr/include/boost/detail/bad_weak_ptr.hpp
Block_Finder.o: /usr/include/boost/detail/sp_counted_base.hpp
Block_Finder.o: /usr/include/boost/detail/sp_counted_base_gcc_x86.hpp
Block_Finder.o: /usr/include/boost/detail/sp_counted_impl.hpp
Block_Finder.o: /usr/include/boost/detail/workaround.hpp /usr/include/gmpxx.h
Block_Finder.o: /usr/include/gmp.h Exception.h Turing_Machine.h
Macro_Turing_Machine.o: Macro_Turing_Machine.h Define.h
Macro_Turing_Machine.o: /usr/include/boost/shared_ptr.hpp
Macro_Turing_Machine.o: /usr/include/boost/config.hpp
Macro_Turing_Machine.o: /usr/include/boost/config/user.hpp
Macro_Turing_Machine.o: /usr/include/boost/config/select_compiler_config.hpp
Macro_Turing_Machine.o: /usr/include/boost/config/compiler/gcc.hpp
Macro_Turing_Machine.o: /usr/include/boost/config/select_stdlib_config.hpp
Macro_Turing_Machine.o: /usr/include/boost/config/select_platform_config.hpp
Macro_Turing_Machine.o: /usr/include/boost/config/suffix.hpp
Macro_Turing_Machine.o: /usr/include/limits.h /usr/include/features.h
Macro_Turing_Machine.o: /usr/include/sys/cdefs.h /usr/include/bits/wordsize.h
Macro_Turing_Machine.o: /usr/include/gnu/stubs.h /usr/include/gnu/stubs.h
Macro_Turing_Machine.o: /usr/include/bits/posix1_lim.h
Macro_Turing_Machine.o: /usr/include/bits/local_lim.h
Macro_Turing_Machine.o: /usr/include/linux/limits.h
Macro_Turing_Machine.o: /usr/include/bits/posix2_lim.h
Macro_Turing_Machine.o: /usr/include/boost/assert.hpp /usr/include/assert.h
Macro_Turing_Machine.o: /usr/include/boost/checked_delete.hpp
Macro_Turing_Machine.o: /usr/include/boost/throw_exception.hpp
Macro_Turing_Machine.o: /usr/include/boost/config.hpp
Macro_Turing_Machine.o: /usr/include/boost/detail/shared_count.hpp
Macro_Turing_Machine.o: /usr/include/boost/detail/bad_weak_ptr.hpp
Macro_Turing_Machine.o: /usr/include/boost/detail/sp_counted_base.hpp
Macro_Turing_Machine.o: /usr/include/boost/detail/sp_counted_base_gcc_x86.hpp
Macro_Turing_Machine.o: /usr/include/boost/detail/sp_counted_impl.hpp
Macro_Turing_Machine.o: /usr/include/boost/detail/workaround.hpp
Macro_Turing_Machine.o: /usr/include/gmpxx.h /usr/include/gmp.h Exception.h
Macro_Turing_Machine.o: TTable.h Turing_Machine.h
Backsymbol_Turing_Machine.o: Backsymbol_Turing_Machine.h Define.h
Backsymbol_Turing_Machine.o: /usr/include/boost/shared_ptr.hpp
Backsymbol_Turing_Machine.o: /usr/include/boost/config.hpp
Backsymbol_Turing_Machine.o: /usr/include/boost/config/user.hpp
Backsymbol_Turing_Machine.o: /usr/include/boost/config/select_compiler_config.hpp
Backsymbol_Turing_Machine.o: /usr/include/boost/config/compiler/gcc.hpp
Backsymbol_Turing_Machine.o: /usr/include/boost/config/select_stdlib_config.hpp
Backsymbol_Turing_Machine.o: /usr/include/boost/config/select_platform_config.hpp
Backsymbol_Turing_Machine.o: /usr/include/boost/config/suffix.hpp
Backsymbol_Turing_Machine.o: /usr/include/limits.h /usr/include/features.h
Backsymbol_Turing_Machine.o: /usr/include/sys/cdefs.h
Backsymbol_Turing_Machine.o: /usr/include/bits/wordsize.h
Backsymbol_Turing_Machine.o: /usr/include/gnu/stubs.h
Backsymbol_Turing_Machine.o: /usr/include/gnu/stubs.h
Backsymbol_Turing_Machine.o: /usr/include/bits/posix1_lim.h
Backsymbol_Turing_Machine.o: /usr/include/bits/local_lim.h
Backsymbol_Turing_Machine.o: /usr/include/linux/limits.h
Backsymbol_Turing_Machine.o: /usr/include/bits/posix2_lim.h
Backsymbol_Turing_Machine.o: /usr/include/boost/assert.hpp
Backsymbol_Turing_Machine.o: /usr/include/assert.h
Backsymbol_Turing_Machine.o: /usr/include/boost/checked_delete.hpp
Backsymbol_Turing_Machine.o: /usr/include/boost/throw_exception.hpp
Backsymbol_Turing_Machine.o: /usr/include/boost/config.hpp
Backsymbol_Turing_Machine.o: /usr/include/boost/detail/shared_count.hpp
Backsymbol_Turing_Machine.o: /usr/include/boost/detail/bad_weak_ptr.hpp
Backsymbol_Turing_Machine.o: /usr/include/boost/detail/sp_counted_base.hpp
Backsymbol_Turing_Machine.o: /usr/include/boost/detail/sp_counted_base_gcc_x86.hpp
Backsymbol_Turing_Machine.o: /usr/include/boost/detail/sp_counted_impl.hpp
Backsymbol_Turing_Machine.o: /usr/include/boost/detail/workaround.hpp
Backsymbol_Turing_Machine.o: /usr/include/gmpxx.h /usr/include/gmp.h
Backsymbol_Turing_Machine.o: Exception.h TTable.h Turing_Machine.h
Chain_Simulator.o: Chain_Simulator.h Define.h
Chain_Simulator.o: /usr/include/boost/shared_ptr.hpp
Chain_Simulator.o: /usr/include/boost/config.hpp
Chain_Simulator.o: /usr/include/boost/config/user.hpp
Chain_Simulator.o: /usr/include/boost/config/select_compiler_config.hpp
Chain_Simulator.o: /usr/include/boost/config/compiler/gcc.hpp
Chain_Simulator.o: /usr/include/boost/config/select_stdlib_config.hpp
Chain_Simulator.o: /usr/include/boost/config/select_platform_config.hpp
Chain_Simulator.o: /usr/include/boost/config/suffix.hpp /usr/include/limits.h
Chain_Simulator.o: /usr/include/features.h /usr/include/sys/cdefs.h
Chain_Simulator.o: /usr/include/bits/wordsize.h /usr/include/gnu/stubs.h
Chain_Simulator.o: /usr/include/gnu/stubs.h /usr/include/bits/posix1_lim.h
Chain_Simulator.o: /usr/include/bits/local_lim.h /usr/include/linux/limits.h
Chain_Simulator.o: /usr/include/bits/posix2_lim.h
Chain_Simulator.o: /usr/include/boost/assert.hpp /usr/include/assert.h
Chain_Simulator.o: /usr/include/boost/checked_delete.hpp
Chain_Simulator.o: /usr/include/boost/throw_exception.hpp
Chain_Simulator.o: /usr/include/boost/config.hpp
Chain_Simulator.o: /usr/include/boost/detail/shared_count.hpp
Chain_Simulator.o: /usr/include/boost/detail/bad_weak_ptr.hpp
Chain_Simulator.o: /usr/include/boost/detail/sp_counted_base.hpp
Chain_Simulator.o: /usr/include/boost/detail/sp_counted_base_gcc_x86.hpp
Chain_Simulator.o: /usr/include/boost/detail/sp_counted_impl.hpp
Chain_Simulator.o: /usr/include/boost/detail/workaround.hpp
Chain_Simulator.o: /usr/include/gmpxx.h /usr/include/gmp.h Exception.h
Chain_Simulator.o: Turing_Machine.h Tape.h TapeImplem.h Proof_System.h
Chain_Simulator.o: Expression.h
Proof_System.o: Expression.h Define.h /usr/include/boost/shared_ptr.hpp
Proof_System.o: /usr/include/boost/config.hpp
Proof_System.o: /usr/include/boost/config/user.hpp
Proof_System.o: /usr/include/boost/config/select_compiler_config.hpp
Proof_System.o: /usr/include/boost/config/compiler/gcc.hpp
Proof_System.o: /usr/include/boost/config/select_stdlib_config.hpp
Proof_System.o: /usr/include/boost/config/select_platform_config.hpp
Proof_System.o: /usr/include/boost/config/suffix.hpp /usr/include/limits.h
Proof_System.o: /usr/include/features.h /usr/include/sys/cdefs.h
Proof_System.o: /usr/include/bits/wordsize.h /usr/include/gnu/stubs.h
Proof_System.o: /usr/include/gnu/stubs.h /usr/include/bits/posix1_lim.h
Proof_System.o: /usr/include/bits/local_lim.h /usr/include/linux/limits.h
Proof_System.o: /usr/include/bits/posix2_lim.h /usr/include/boost/assert.hpp
Proof_System.o: /usr/include/assert.h /usr/include/boost/checked_delete.hpp
Proof_System.o: /usr/include/boost/throw_exception.hpp
Proof_System.o: /usr/include/boost/config.hpp
Proof_System.o: /usr/include/boost/detail/shared_count.hpp
Proof_System.o: /usr/include/boost/detail/bad_weak_ptr.hpp
Proof_System.o: /usr/include/boost/detail/sp_counted_base.hpp
Proof_System.o: /usr/include/boost/detail/sp_counted_base_gcc_x86.hpp
Proof_System.o: /usr/include/boost/detail/sp_counted_impl.hpp
Proof_System.o: /usr/include/boost/detail/workaround.hpp /usr/include/gmpxx.h
Proof_System.o: /usr/include/gmp.h Exception.h General_Chain_Simulator.h
Proof_System.o: Turing_Machine.h Tape.h TapeImplem.h Proof_System.h
General_Chain_Simulator.o: General_Chain_Simulator.h Define.h
General_Chain_Simulator.o: /usr/include/boost/shared_ptr.hpp
General_Chain_Simulator.o: /usr/include/boost/config.hpp
General_Chain_Simulator.o: /usr/include/boost/config/user.hpp
General_Chain_Simulator.o: /usr/include/boost/config/select_compiler_config.hpp
General_Chain_Simulator.o: /usr/include/boost/config/compiler/gcc.hpp
General_Chain_Simulator.o: /usr/include/boost/config/select_stdlib_config.hpp
General_Chain_Simulator.o: /usr/include/boost/config/select_platform_config.hpp
General_Chain_Simulator.o: /usr/include/boost/config/suffix.hpp
General_Chain_Simulator.o: /usr/include/limits.h /usr/include/features.h
General_Chain_Simulator.o: /usr/include/sys/cdefs.h
General_Chain_Simulator.o: /usr/include/bits/wordsize.h
General_Chain_Simulator.o: /usr/include/gnu/stubs.h
General_Chain_Simulator.o: /usr/include/gnu/stubs.h
General_Chain_Simulator.o: /usr/include/bits/posix1_lim.h
General_Chain_Simulator.o: /usr/include/bits/local_lim.h
General_Chain_Simulator.o: /usr/include/linux/limits.h
General_Chain_Simulator.o: /usr/include/bits/posix2_lim.h
General_Chain_Simulator.o: /usr/include/boost/assert.hpp
General_Chain_Simulator.o: /usr/include/assert.h
General_Chain_Simulator.o: /usr/include/boost/checked_delete.hpp
General_Chain_Simulator.o: /usr/include/boost/throw_exception.hpp
General_Chain_Simulator.o: /usr/include/boost/config.hpp
General_Chain_Simulator.o: /usr/include/boost/detail/shared_count.hpp
General_Chain_Simulator.o: /usr/include/boost/detail/bad_weak_ptr.hpp
General_Chain_Simulator.o: /usr/include/boost/detail/sp_counted_base.hpp
General_Chain_Simulator.o: /usr/include/boost/detail/sp_counted_base_gcc_x86.hpp
General_Chain_Simulator.o: /usr/include/boost/detail/sp_counted_impl.hpp
General_Chain_Simulator.o: /usr/include/boost/detail/workaround.hpp
General_Chain_Simulator.o: /usr/include/gmpxx.h /usr/include/gmp.h
General_Chain_Simulator.o: Exception.h Turing_Machine.h Tape.h TapeImplem.h
General_Chain_Simulator.o: Expression.h
Exception.o: Exception.h Define.h /usr/include/boost/shared_ptr.hpp
Exception.o: /usr/include/boost/config.hpp /usr/include/boost/config/user.hpp
Exception.o: /usr/include/boost/config/select_compiler_config.hpp
Exception.o: /usr/include/boost/config/compiler/gcc.hpp
Exception.o: /usr/include/boost/config/select_stdlib_config.hpp
Exception.o: /usr/include/boost/config/select_platform_config.hpp
Exception.o: /usr/include/boost/config/suffix.hpp /usr/include/limits.h
Exception.o: /usr/include/features.h /usr/include/sys/cdefs.h
Exception.o: /usr/include/bits/wordsize.h /usr/include/gnu/stubs.h
Exception.o: /usr/include/gnu/stubs.h /usr/include/bits/posix1_lim.h
Exception.o: /usr/include/bits/local_lim.h /usr/include/linux/limits.h
Exception.o: /usr/include/bits/posix2_lim.h /usr/include/boost/assert.hpp
Exception.o: /usr/include/assert.h /usr/include/boost/checked_delete.hpp
Exception.o: /usr/include/boost/throw_exception.hpp
Exception.o: /usr/include/boost/config.hpp
Exception.o: /usr/include/boost/detail/shared_count.hpp
Exception.o: /usr/include/boost/detail/bad_weak_ptr.hpp
Exception.o: /usr/include/boost/detail/sp_counted_base.hpp
Exception.o: /usr/include/boost/detail/sp_counted_base_gcc_x86.hpp
Exception.o: /usr/include/boost/detail/sp_counted_impl.hpp
Exception.o: /usr/include/boost/detail/workaround.hpp /usr/include/gmpxx.h
Exception.o: /usr/include/gmp.h
Expression.o: Expression.h Define.h /usr/include/boost/shared_ptr.hpp
Expression.o: /usr/include/boost/config.hpp
Expression.o: /usr/include/boost/config/user.hpp
Expression.o: /usr/include/boost/config/select_compiler_config.hpp
Expression.o: /usr/include/boost/config/compiler/gcc.hpp
Expression.o: /usr/include/boost/config/select_stdlib_config.hpp
Expression.o: /usr/include/boost/config/select_platform_config.hpp
Expression.o: /usr/include/boost/config/suffix.hpp /usr/include/limits.h
Expression.o: /usr/include/features.h /usr/include/sys/cdefs.h
Expression.o: /usr/include/bits/wordsize.h /usr/include/gnu/stubs.h
Expression.o: /usr/include/gnu/stubs.h /usr/include/bits/posix1_lim.h
Expression.o: /usr/include/bits/local_lim.h /usr/include/linux/limits.h
Expression.o: /usr/include/bits/posix2_lim.h /usr/include/boost/assert.hpp
Expression.o: /usr/include/assert.h /usr/include/boost/checked_delete.hpp
Expression.o: /usr/include/boost/throw_exception.hpp
Expression.o: /usr/include/boost/config.hpp
Expression.o: /usr/include/boost/detail/shared_count.hpp
Expression.o: /usr/include/boost/detail/bad_weak_ptr.hpp
Expression.o: /usr/include/boost/detail/sp_counted_base.hpp
Expression.o: /usr/include/boost/detail/sp_counted_base_gcc_x86.hpp
Expression.o: /usr/include/boost/detail/sp_counted_impl.hpp
Expression.o: /usr/include/boost/detail/workaround.hpp /usr/include/gmpxx.h
Expression.o: /usr/include/gmp.h Exception.h
