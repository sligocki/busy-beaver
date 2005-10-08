#!/usr/bin/env python

from distutils.core import setup, Extension

module1 = Extension('busyBeaverC',
                    sources=['busyBeaverC.c'],
                    extra_compile_args=['-pedantic-errors','-Wno-long-long'])

setup(name='busyBeaverC',
      version='1.0',
      description='C speedups to Turing machine simulation',
      ext_modules=[module1])

module2 = Extension('twoMachineC',
                    sources=['twoMachineC.c'],
                    extra_compile_args=['-pedantic-errors','-Wno-long-long'])

setup(name='twoMachineC',
      version='1.0',
      description='Run one TM at two different speeds',
      ext_modules=[module2])
