CFLAGS = -g -O2
CXXFLAGS = -g -O2
LDFLAGS = -g -O2
LIBS = -lm

exe1 = Quick_Sim
src1 = Quick_Sim.cpp                 \
       TTable.cpp                    \
       Simple_Turing_Machine.cpp     \
       Block_Finder.cpp              \
       Macro_Turing_Machine.cpp      \
       Backsymbol_Turing_Machine.cpp \
       Chain_Simulator.cpp           \
       Tape.cpp                      \
       Proof_System.cpp              \
       Exception.cpp
obj1 = Quick_Sim.o                   \
       TTable.o                      \
       Simple_Turing_Machine.o       \
       Block_Finder.o                \
       Macro_Turing_Machine.o        \
       Backsymbol_Turing_Machine.o   \
       Chain_Simulator.o             \
       Tape.o                        \
       Proof_System.o                \
       Exception.o

all: $(exe1)

$(exe1): $(obj1)
	$(CXX) $(LDFLAGS) -o $(exe1) $(obj1) $(LIBS)

depend:
	makedepend $(src1)

tar:
	tar jcf code.tar.bz2 Makefile $(src1) $(hdr1) Python/*.py Python/*.tm

clean:
	/bin/rm -f $(exe1) *.o

# DO NOT DELETE

Quick_Sim.o: Define.h Exception.h TTable.h Turing_Machine.h
Quick_Sim.o: Simple_Turing_Machine.h Block_Finder.h Macro_Turing_Machine.h
Quick_Sim.o: Backsymbol_Turing_Machine.h Chain_Simulator.h Tape.h
Quick_Sim.o: Proof_System.h
TTable.o: TTable.h Define.h Exception.h
Simple_Turing_Machine.o: Simple_Turing_Machine.h Define.h Exception.h
Simple_Turing_Machine.o: TTable.h Turing_Machine.h
Block_Finder.o: Block_Finder.h Define.h Exception.h Turing_Machine.h
Macro_Turing_Machine.o: Macro_Turing_Machine.h Define.h Exception.h TTable.h
Macro_Turing_Machine.o: Turing_Machine.h
Backsymbol_Turing_Machine.o: Backsymbol_Turing_Machine.h Define.h Exception.h
Backsymbol_Turing_Machine.o: TTable.h Turing_Machine.h
Chain_Simulator.o: Chain_Simulator.h Define.h Exception.h Turing_Machine.h
Chain_Simulator.o: Tape.h Proof_System.h
Tape.o: Tape.h Define.h Exception.h
Proof_System.o: Proof_System.h Define.h Exception.h Turing_Machine.h
Exception.o: Exception.h Define.h
