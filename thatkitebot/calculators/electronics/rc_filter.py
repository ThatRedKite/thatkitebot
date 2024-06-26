#  Copyright (c) 2019-2024 ThatRedKite and contributors

import math

from io import BytesIO
from random import randint
from math import *

import discord
import si_prefix
import matplotlib.pyplot as plt


from . import pcb_mod
from .exceptions import *


class RCFilter:
    def __init__(self, d: dict, plot=False):
        self.r1 = si_prefix.si_parse(d.get("r1")) if d.get("r1") else None
        self.c1 = si_prefix.si_parse(d.get("c1")) if d.get("c1") else None
        self.fcut = si_prefix.si_parse(d.get("fcut")) if d.get("fcut") else None
        self.e = si_prefix.si_parse(d.get("e")) if d.get("e") else None
        self.doPlot = plot
        self.mode = None

    def calculate(self):
        if self.e is not None and pcb_mod.check_series(int(self.e)) == 0:
            raise ImpossibleValueError("Get real")
        # if any value is negative, raise an error
        if self.r1 and self.r1 < 0:
            raise ImpossibleValueError("Get real")
        if self.c1 and self.c1 < 0:
            raise ImpossibleValueError("Get real")
        if self.fcut and self.fcut < 0:
            raise ImpossibleValueError("Get real")
        # calculate the missing value
        if not self.fcut and self.r1 is not None and self.c1 is not None:
            self.fcut = 1 / (2 * math.pi * self.r1 * self.c1)
            self.mode = "fcut"
        elif not self.r1 and self.fcut is not None and self.c1 is not None:
            self.r1 = 1 / (2 * math.pi * self.fcut * self.c1)
            self.mode = "r1"
        elif not self.c1 and self.fcut is not None and self.r1 is not None:
            self.c1 = 1 / (2 * math.pi * self.fcut * self.r1)
            self.mode = "c1"
        else:
            raise TooFewArgsError()

    def draw(self):
        if self.mode is None:
            return f"""
        ```

IN  ┌───────┐          OUT
○───┤  R1   ├─────┬──────○ 
    └───────┘     │ 
               ───┴─── C1
               ───┬───
                  │   
                 ─┴─
                 GND

R1 = {si_prefix.si_format(self.r1)}Ω    
C1 = {si_prefix.si_format(self.c1)}F
Fcut = {si_prefix.si_format(self.fcut)}Hz           
        ```
        """
        else:
            return """
        ```

IN  ┌───────┐          OUT
○───┤  R1   ├─────┬──────○ 
    └───────┘     │ 
               ───┴─── C1
               ───┬───
                  │   
                 ─┴─
                 GND      
        ```
        """

    def randomize(self):
        self.r1 = randint(1, 1000000)
        self.c1 = randint(0, 1000000) / 10 ** 6

    def plot(self):
        fcut = self.fcut
        cap = self.c1
        res = self.r1
        fmin = fcut / 1000
        fmax = fcut * 1000
        freqlist = []
        gainlist = []
        f = fmin
        while f < fmax:
            freqlist.append(f)
            x = 1 / (2 * math.pi * f * cap)
            vout = 10 * (x / sqrt((res ** 2) + (x ** 2)))
            gain = 20 * log10(vout / 10)
            gainlist.append(gain)
            f = f * 1.1
        plt.vlines(x=fcut,
                   ymin=-60,
                   ymax=gainlist[freqlist.index(min(freqlist, key=lambda x: abs(x - fcut)))],
                   color="orange",
                   label="Cutoff frequency: {}Hz".format(si_prefix.si_format(self.fcut))
                   )
        plt.plot(freqlist, gainlist, color="b")
        plt.grid()
        plt.xlabel('Frequency in Hz')
        plt.ylabel('Gain in dB')
        plt.xscale('log')
        plt.ylim([min(gainlist), 10])
        plt.xlim([min(freqlist), max(freqlist)])
        plt.legend()
        fig = plt.gcf()
        imgdata = BytesIO()
        fig.savefig(imgdata, format='png')
        imgdata.seek(0)  # rewind the data
        plt.clf()
        return imgdata

    def gen_embed(self):
        try:
            self.calculate()
        except TooFewArgsError:
            self.randomize()
            self.calculate()
            self.mode = None

        embed = discord.Embed(title="RC filter")
        embed.add_field(name="Schematic", value=self.draw(), inline=False)
        match self.mode:
            case None:
                embed.add_field(
                    name="How to use this?",
                    value=f"""
                        With this command you can calculate required resistor or capacitor value for a specific RC filter.
                        Example: `rc fcut=1k r1=100` to find c1. You can add `plot` to the end of the command if you would like a bode plot.

                        This accepts any SI-prefix (e.g. k, m, M, µ, etc.). 
                        Don't try writing out the `Ω` in Ohms 
                        as it just confuses the bot (don't use R either).
                        You can also use `rcfilter`, `filter`, `lowpass`.
                        """,
                    inline=True)
                embed.set_footer(text="Note: the above RC filter is randomly generated")
            case "r1":
                embed.add_field(
                    name="Values",
                    value=f"R1 = {si_prefix.si_format(self.r1)}Ω\nC1 = {si_prefix.si_format(self.c1)}F\nFcut = {si_prefix.si_format(self.fcut)}Hz")
                embed.add_field(
                    name=f"Closest E{int(24 if self.e is None or 0 else self.e)} resistor value",
                    value=f"R1 = {si_prefix.si_format(pcb_mod.e_resistor(self.r1, int(24 if self.e is None or 0 else self.e)))}Ω")
            case "c1":
                embed.add_field(
                    name="Values",
                    value=f"R1 = {si_prefix.si_format(self.r1)}Ω\nC1 = {si_prefix.si_format(self.c1)}F\nFcut = {si_prefix.si_format(self.fcut)}Hz")
                embed.add_field(
                    name=f"Closest E{int(12 if self.e is None or 0 else self.e)} capacitor value",
                    value=f"C1 = {si_prefix.si_format(pcb_mod.e_resistor(self.r1, int(12 if self.e is None or 0 else self.e)))}F")
            case "fcut":
                embed.add_field(
                    name="Values",
                    value=f"R1 = {si_prefix.si_format(self.r1)}Ω\nC1 = {si_prefix.si_format(self.c1)}F\nFcut = {si_prefix.si_format(self.fcut)}Hz")

        if self.doPlot:
            embed.set_image(url="attachment://rc.png")

        if embed:
            return embed

    def gen_file(self):
        imgdata = self.plot()
        file = discord.File(BytesIO(imgdata.read()), filename="rc.png")
        return file