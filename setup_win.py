#!/usr/bin/env python

from distutils.core import setup, Extension

module1 = Extension('Turing_Machine_Sim',
                    sources=['Turing_Machine_Sim.c'])

setup(name='Turing_Machine_Sim',
      version='1.0',
      description='C speedups to Turing machine simulation',
      ext_modules=[module1])

module2 = Extension('Dual_Machine',
                    sources=['Dual_Machine.c'])

setup(name='Dual_Machine',
      version='1.0',
      description='Run one TM at two different speeds',
      ext_modules=[module2])

module3 = Extension('Macro_Machine',
                    sources=['Macro_Machine.c'])

setup(name='Macro_Machine',
      version='1.0',
      description='Run one TM using macro steps',
      ext_modules=[module3])
