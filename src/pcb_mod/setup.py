from distutils.core import setup, Extension

module_pcb = Extension("pcb_mod", sources = ["pcb_calc.c"])

setup(name = "PCB_Calc",
      version = "1.0",
      description = "C library for calculating PCB related topics",
      ext_modules = [module_pcb])