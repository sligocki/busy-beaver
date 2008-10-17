CFLAGS = -g -O2
CXXFLAGS = -g -O2
LDFLAGS = -g -O2
LIBS = -lm

exe1 = Quick_Sim
src1 = Quick_Sim.cpp TTable.cpp Turing_Machine.cpp Simple_Turing_Machine.cpp \
       Block_Finder.cpp
obj1 = Quick_Sim.o   TTable.o   Turing_Machine.o   Simple_Turing_Machine.o   \
       Block_Finder.o  

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

Quick_Sim.o: TTable.h Turing_Machine.h Simple_Turing_Machine.h Block_Finder.h
