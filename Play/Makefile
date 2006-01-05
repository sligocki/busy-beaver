CFLAGS = -ansi

all:
	/bin/rm -rf build *.so
	./setup.py build
	ln -s build/lib.*/*.so .
