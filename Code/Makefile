CFLAGS = -ansi

protobuf:
	protoc -I=. --python_out=. --mypy_out=. ./io.proto

test: test-small test-large

test-small:
	./test_Algebraic_Expression.py
	./test_Direct_Simulator.py
	./test_Exp_Int.py
	./test_Math.py
	./test_Proof_System.py
	./test_TNF.py
	./test_Turing_Machine.py

test-large:
	./test_Enumerate.py
	./test_Lin_Recur.py
	./test_Macro_Simulator.py
