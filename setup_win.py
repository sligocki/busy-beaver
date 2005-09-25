#!/usr/bin/env python

from distutils.core import setup, Extension

module1 = Extension('busyBeaverC',
                    sources=['busyBeaverC.c'])

setup(name='busyBeaverC',
      version='1.0',
      description='C speedups to busyBeaver',
      ext_modules=[module1])
