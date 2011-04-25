CFLAGS = -ansi

all: build test

build:
	/bin/rm -rf build *.so
	./setup.py build
	ln -s build/lib.*/*.so .

test:
	./test_Macro_Proof_System.py
	./test_Macro_Simulator.py
	./test_Enumerate.py
