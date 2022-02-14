CFLAGS = -ansi

all: build-all protobuf test-all

build-all:
	/bin/rm -rf build *.so
	./setup.py build
	ln -s build/lib.*/*.so .

protobuf:
	protoc -I=. --python_out=. ./io.proto

test: test-all
test-all:
	./test_Algebraic_Expression.py
	./test_Backtracking_Filter.py
	./test_Enumerate.py
	./test_Lin_Recur.py
	./test_Macro_Proof_System.py
	./test_Macro_Simulator.py
	./test_Turing_Machine.py
