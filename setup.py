#!/usr/bin/env python

from distutils.core import setup, Extension

module1 = Extension('busy_beaver_C',
                    sources=['busy_beaver_C.c'],
                    extra_compile_args=['-pedantic-errors','-Wno-long-long'])

setup(name='busy_beaver_C',
      version='1.0',
      description='C speedups to Turing machine simulation',
      ext_modules=[module1])

module2 = Extension('two_machine_C',
                    sources=['two_machine_C.c'],
                    extra_compile_args=['-pedantic-errors','-Wno-long-long'])

setup(name='two_machine_C',
      version='1.0',
      description='Run one TM at two different speeds',
      ext_modules=[module2])
