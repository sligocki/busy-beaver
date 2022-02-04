CFLAGS = -ansi

all: build-all test-all

build-all:
	/bin/rm -rf build *.so
	./setup.py build
	ln -s build/lib.*/*.so .

test: test-all
test-all:
	./test_Backtracking_Filter.py
	./test_Enumerate.py
	./test_Macro_Proof_System.py
	./test_Macro_Simulator.py
	./test_Turing_Machine.py
