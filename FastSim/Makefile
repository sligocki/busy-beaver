CFLAGS = -g -O2
CXXFLAGS = -g -O2
LDFLAGS = -g -O2
LIBS = -lm

exe1 = Quick_Sim
obj1 = Quick_Sim.o   TTable.o   Turing_Machine.o   Simple_Turing_Machine.o   \
       Block_Finder.o
src1 = Quick_Sim.cpp TTable.cpp Turing_Machine.cpp Simple_Turing_Machine.cpp \
       Block_Finder.cpp
hdr1 =               TTable.h   Turing_Machine.h   Simple_Turing_Machine.h   \
       Block_Finder.h

$(exe1): $(obj1)
	$(CXX) $(LDFLAGS) -o $(exe1) $(obj1) $(LIBS)

$(obj1): $(hdr1)

tar:
	tar jcf code.tar.bz2 Makefile $(src1) $(hdr1) Python/*.py Python/*.tm
# DO NOT DELETE

Quick_Sim.o: TTable.h Turing_Machine.h Simple_Turing_Machine.h Block_Finder.h
TTable.o: TTable.h
