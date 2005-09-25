#!/usr/bin/env python

from distutils.core import setup, Extension

module1 = Extension('busyBeaverC',
                    sources=['busyBeaverC.c'],
                    extra_compile_args=['-pedantic-errors','-Wno-long-long'])

setup(name='busyBeaverC',
      version='1.0',
      description='C speedups to busyBeaver',
      ext_modules=[module1])
