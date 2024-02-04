#  Copyright (c) 2019-2023 ThatRedKite and contributors

from distutils.core import setup, Extension

module_pcb = Extension("pcb_mod", sources=["pcb_calc.c"])

setup(
    name="PCB_Calc",
    version="1.1",
    description="C library for calculating PCB and electronics related topics",
    ext_modules=[module_pcb]
)
