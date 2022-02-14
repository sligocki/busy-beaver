#! /usr/bin/env python3

from distutils.core import setup, Extension

module1 = Extension('Turing_Machine_Sim',
                    sources=['Turing_Machine_Sim.c','Turing_Machine.c'],
                    extra_compile_args=['-Wno-long-long'])

setup(name='Turing_Machine_Sim',
      version='1.0',
      description='C speedups to Turing machine simulation',
      ext_modules=[module1])

module2 = Extension('Turing_Machine_Count',
                    sources=['Turing_Machine_Count.c','Turing_Machine.c'],
                    extra_compile_args=['-Wno-long-long'])

setup(name='Turing_Machine_Count',
      version='1.0',
      description='Turing machine simulation to get tape size as a function of steps',
      ext_modules=[module2])

module3 = Extension('Dual_Machine',
                    sources=['Dual_Machine.c','Turing_Machine.c'],
                    extra_compile_args=['-Wno-long-long'])

setup(name='Dual_Machine',
      version='1.0',
      description='Run one TM at two different speeds',
      ext_modules=[module3])

module4 = Extension('Macro_Machine',
                    sources=['Macro_Machine.c','Turing_Machine.c'],
                    extra_compile_args=['-Wno-long-long'])

setup(name='Macro_Machine',
      version='1.0',
      description='Run one TM using macro steps',
      ext_modules=[module4])

#module5 = Extension('Tree_Identify',
#                    sources=['Tree_Identify.c','Turing_Machine.c'],
#                    extra_compile_args=['-Wno-long-long'])
#
#setup(name='Tree_Identify',
#      version='1.0',
#      description='Identify a possible infinite tree',
#      ext_modules=[module5])

module6 = Extension('signalPlus',
                    sources=['signalPlusModule.c'],
                    extra_compile_args=['-Wno-long-long'])

setup(name='signalPlus',
      version='1.0',
      description='Signal module plus ualarm',
      ext_modules=[module6])

module7 = Extension('Turing_Machine_Recur',
                    sources=['Turing_Machine_Recur.c','Turing_Machine.c'],
                    extra_compile_args=['-Wno-long-long'])

setup(name='Turing_Machine_Recur',
      version='1.0',
      description='C speedups to Turing machine simulation',
      ext_modules=[module7])

module8 = Extension('Turing_Machine_Recur_2_4_054',
                    sources=['Turing_Machine_Recur_2_4_054.c','Turing_Machine.c'],
                    extra_compile_args=['-Wno-long-long'])

setup(name='Turing_Machine_Recur_2_4_054',
      version='1.0',
      description='C speedups to Turing machine simulation',
      ext_modules=[module8])

