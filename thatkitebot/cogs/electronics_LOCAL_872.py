#  Copyright (c) 2019-2022 ThatRedKite and contributors

import math
from math import log10, sqrt
from sre_constants import SUCCESS
import matplotlib.pyplot as plt
from io import BytesIO
import discord
import discord.commands as scmd
from discord.ext import commands
import si_prefix
from random import randint

from thatkitebot.backend import util
from thatkitebot.backend import pcb_mod

class InputDifferenceError(Exception):
    pass


class InputOutOfRangeError(Exception):
    pass


class TooFewArgsError(Exception):
    pass


class ImpossibleValueError(Exception):
    pass


def parse_input(s):
    s = s.replace("=", " ").split(" ")
    s_dict = dict(zip(s[::2], s[1::2]))
    for key in s_dict.keys():
        old = s_dict[key]
        new = old.replace("v", "").replace("V", "").replace("u", "µ").replace("Ω", "")
        s_dict.update({key: new})
    return s_dict


def slash_preprocessor(a: str):
    return a.replace("v", "").replace("V", "").replace("u", "µ").replace("F", "").strip() if a else None


class conversion:
    def __init__(self, d: dict):
        self.mm = si_prefix.si_parse(d.get("mm")) if d.get("mm") else None
        self.mil = si_prefix.si_parse(d.get("mil")) if d.get("mil") else None
        self.oz = si_prefix.si_parse(d.get("oz")) if d.get("oz") else None
        self.mode = "length"
        
    def calculate(self):
        if self.mm is not None and self.mil is None and self.oz is None:
            self.mil = round(pcb_mod.mm2mil(self.mm), 3)
            self.mode = "mil"
        elif self.mm is None and self.mil is not None and self.oz is None:
            self.mm = round(pcb_mod.mil2mm(self.mil), 3)
            self.mode = "mm"
        elif self.mm is None and self.mil is None and self.oz is not None:
            self.mil = round(pcb_mod.weight2mil(self.oz), 3)
            self.mm = round(pcb_mod.mil2mm(self.mil) * 1000, 1)
            self.mode = "oz"
        else:
            raise TooFewArgsError()
        
    def gen_embed(self):
        try:
            self.calculate()
        except TooFewArgsError:
            self.mode = None
                            
        embed = discord.Embed(title="PCB Unit Conversions")    
        match self.mode:
            case None:    
                embed.add_field(
                    name="How to use this?",
                    value=f"""With this command you can convert between millimeters and mils for PCB applications
                    And it can give you the copper height in both mils and micrometers
                    
                    Example: `conv mm=20` to convert 20 mm to mils
                    
                    Example: `conv mil=20` to convert 20 mils to mm
                    
                    Example: `conv oz=2` to get the height of 2oz/ft² copper on a PCB
                    
                    This accepts any SI prefixes, but does not support endings with "mm" or "mil" 
                    """,
                    inline=True)
                return embed
            case "mm":
                embed.add_field(name="Result:",
                    value=f"{self.mil}mil(s) = __{self.mm}mm__")
            case "mil":
                embed.add_field(name="Result:",
                    value=f"{self.mm}mm = __{self.mil}mil(s)__")
            case "oz":
                embed.add_field(name="Result:",
                    value=f"{self.oz}oz/ft² = __{self.mil}mil(s)__ or __{self.mm}μm__")
                
        if embed:
            return embed


class PCB_calc:
    def __init__(self, d: dict, internal = False, limit = False):
        self.current = si_prefix.si_parse(d.get("i")) if d.get("i") else None
        self.width = si_prefix.si_parse(d.get("w")) if d.get("w") else None
        self.thicc = si_prefix.si_parse(d.get("t")) if d.get("t") else None
        self.temp = si_prefix.si_parse(d.get("temp")) if d.get("temp") else None
        self.internal = internal
        self.limit = limit
        self.mode = None

    def calculate(self):
        if self.limit:
            self.mode = "limit"
        if self.temp is not None and (self.temp < 10 or self.temp > 100):
            raise ImpossibleValueError("Get real")
        if self.thicc is not None and (self.thicc < 0.5 or self.thicc > 3):
            raise ImpossibleValueError("Get real")
        
        if self.current is not None and self.width is None:
            if self.current <= 0 or self.current > 35:
                raise ImpossibleValueError("Get real")
            self.width = round(pcb_mod.width(self.current, int(0 if self.temp is None else self.temp), int(0 if self.thicc is None else self.thicc), self.internal), 3)
            self.mode = "succ"
        elif self.current is None and self.width is not None:
            if self.width < 0 or self.width > 400:
                raise ImpossibleValueError("Get real")
            self.current = round(pcb_mod.current(int(0 if self.temp is None else self.temp), self.width, int(0 if self.thicc is None else self.thicc), self.internal), 3)
            self.mode = "succ"
        elif not self.limit:
            raise ImpossibleValueError("Get real")
        
        if self.thicc is None:
            if self.internal:
                self.thicc = 0.5
            else:
                self.thicc = 1  
        
        if self.temp is None:
            self.temp = 10
                                                  
    def draw(self):
        if self.mode != "succ":
            return f"""
        ```
        
Width = {self.width}mils
  <---->
   ┌──┐   
───┴──┴───

Copper weight = {self.thicc}oz/ft²
Max Current = {self.current}A
ΔTemperature = {self.temp}°C
Internal layer? {self.internal}
        ```
        """
        else:
            return """
        ```
        
Width = {self.width}mils
  <---->
   ┌──┐   
───┴──┴───
        ```
        """
        
    def randomize(self):
        self.current = randint(1,10)
        self.temp = randint(1, 100)
        self.thicc = 1
        self.temp = 10
        
    def gen_embed(self):
        try:
            self.calculate()
        except TooFewArgsError:
            self.randomize()
            self.calculate()
            self.mode = None

        embed = discord.Embed(title="PCB Trace Calculator")
        
        if self.mode != "limit":
            embed.add_field(name="Drawing", value=self.draw(), inline=False)

        match self.mode:
            case None:
                embed.add_field(
                    name="How to use this?",
                    value=f"""With this command you can calculate either how wide your PCB traces have to be,
                    or how much current they can handle. This is done with the IPC-2221 formulas.
                    
                    Example: `pcbtrace i=2 temp=10` 
                    this will calculate how wide an outside trace has to be to carry 2A without heating more than 10°C
                    
                    Example: `pcbtrace w=10 temp=10`
                    this will calculate how much current a 10 mils trace can carry without heating more than 10°C
                    
                    You can also specify the copper weight in oz/ft² with the `t=2` variable.
                    however if you do not specify the copper weight the bot will use JLCPCBs standard values
                    To calculate for internal traces, add `internal` to the end of the command.
                    To check the command limits, type `pcbtrace limit`
                    """,
                    inline=True)
                embed.set_footer(text="Note: the above values are randomly generated")
            case "limit":
                embed.add_field(
                    name="IPC2221 Formula limits",
                    value=f"""This command is using the IPC2221 standard as the source for PCB related formulas.
                    Because of that, it has been hardcoded to only accept inputs within the range the formula was made for.
                    
                    These limits are:```
Width: 0 to 400mils
Copper weight: 0.5 to 3oz/ft²
Max Current: 0 to 35A
ΔTemperature: 10 to 100°C```
                    Note, exactly 0A is not an acceptable input.
                    Because who really needs a trace that cant carry any current? <:schmuck:900445607888551947>
                    """,
                    inline=True)
            case "succ":                        
                embed.add_field(
                    name="Values",
                    value=f"Width = {self.width}mils\nCopper weight = {self.thicc}oz/ft²\nMax Current = {self.current}A\nΔTemperature = {self.temp}°C\nInternal layer? {self.internal}\n")

        if embed:
            return embed


class VoltageDivider:
    def __init__(self, d: dict):
        self.vin = si_prefix.si_parse(d.get("vin")) if d.get("vin") else None
        self.vout = si_prefix.si_parse(d.get("vout")) if d.get("vout") else None
        self.r1 = si_prefix.si_parse(d.get("r1")) if d.get("r1") else None
        self.r2 = si_prefix.si_parse(d.get("r2")) if d.get("r2") else None
        self.mode = None

    def calculate(self):
        if self.r1 and self.r2 and self.vin and not self.vout:
            self.vout = self.vin * self.r2 / (self.r1 + self.r2)
            self.mode = "succ"

        elif self.r2 and self.vin and self.vout and not self.r1:
            self.r1 = self.r2 * (self.vin - self.vout) / self.vout
            self.mode = "succ"

        elif self.r1 and self.vin and self.vout and not self.r2:
            self.r2 = self.vout * self.r1 / (self.vin - self.vout)
            self.mode = "succ"

        else:
            raise TooFewArgsError()

        self.format()

    def draw(self):
        if self.mode is None:
            return f"""
        ```
        
   Vin
    ▲
    │
   ┌┴┐
   │ │ R1
   └┬┘
    ├───○ Vout
   ┌┴┐
   │ │ R2
   └┬┘
    │
   ─┴─
   GND
   
Vin = {self.vin}V
Vout = {self.vout}V
R1 = {self.r1}Ω
R2 = {self.r2}Ω
        ```
        """
        else:
            return """
        ```
        
   Vin
    ▲
    │
   ┌┴┐
   │ │ R1
   └┬┘
    ├───○ Vout
   ┌┴┐
   │ │ R2
   └┬┘
    │
   ─┴─
   GND
        ```
        """

    def format(self):
        self.r1 = si_prefix.si_format(self.r1)
        self.r2 = si_prefix.si_format(self.r2)
        self.vout = si_prefix.si_format(self.vout)
        self.vin = si_prefix.si_format(self.vin)

    def randomize(self):
        self.r1 = randint(1,1000000)
        self.r2 = randint(1, 1000000)
        self.vin = randint(1, 100)

    def gen_embed(self):
        try:
            self.calculate()
        except TooFewArgsError:
            self.randomize()
            self.calculate()
            self.mode = None

        embed = discord.Embed(title="Unloaded voltage divider calculation")
        embed.add_field(name="Schematic", value=self.draw(), inline=False)
        match self.mode:
            case None:
                embed.add_field(
                    name="How to use this?",
                    value=f"""With this command you can calculate different values of an unloaded voltage divider.
                    Example: `divider vin=10v r2=3k vout=3v`to find the value of R1.
                    The bot will try to figure out what you are looking for based on the value you didn't enter.
                    You can do the same for every value except Vin.
                    This accepts any SI-prefix (e.g. k, m, M, µ, etc.). 
                    Writing the "V" after the voltages is optional but don't try writing out the `Ω` in Ohms 
                    as it just confuses the bot (don't use R either).
                    """,
                    inline=True)
                embed.set_footer(text="Note: the above voltage divider is randomly generated")
                return embed
            case "succ":
                embed.add_field(
                    name="Values",
                    value=f"R1 =  {self.r1}Ω\nR2 = {self.r2}Ω\nVin = {self.vin}V\nVout = {self.vout}V")
                embed.add_field(
                    name=f"Closest E{(12 if self.e is None or 0 else self.e)} resistor values",
                    value=f"R1 = {si_prefix.si_format(pcb_mod.e_resistor(self.r1, (12 if self.e is None or 0 else self.e)))}Ω\nR2 = {si_prefix.si_format(pcb_mod.e_resistor(self.r2, int(12 if self.e is None or 0 else self.e)))}Ω")

        if embed:
            return embed


class LM317:
    def __init__(self, d: dict):
        self.r1 = si_prefix.si_parse(d.get("r1")) if d.get("r1") else None
        self.r2 = si_prefix.si_parse(d.get("r2")) if d.get("r2") else None
        self.vout = si_prefix.si_parse(d.get("vout")) if d.get("vout") else None
        self.vin = si_prefix.si_parse(d.get("vin")) if d.get("vin") else None
        self.iout = si_prefix.si_parse(d.get("iout")) if d.get("iout") else None
        self.e = si_prefix.si_parse(d.get("e")) if d.get("e") else None
            
    def calculate(self):
        if self.e is not None and pcb_mod.check_series(int(self.e)) == 0:
            raise ImpossibleValueError("Get real")
        if self.iout is not None:
            if self.iout is not None:
                if self.iout < 0:
                    raise ImpossibleValueError("Get real")
                elif self.iout > 1.5:
                    raise InputOutOfRangeError("Your LM317 will explode")
                self.r1 = 1.25 / self.iout
            elif self.r1 is not None:
                self.iout = 1.25 / self.r1
                if self.iout < 0:
                    raise ImpossibleValueError("Get real")
                elif self.iout > 1.5:
                    raise InputOutOfRangeError("Your LM317 will explode")
            else:
                raise TooFewArgsError()
            self.vin = "4.25V to 40.0"
            return
        if self.vin is not None and type(self.vin) is not type(""):
            if not 3.0 <= self.vin <= 40.0:
                raise InputOutOfRangeError("Voltage out of Range")
            if self.vin < 0:
                raise ImpossibleValueError("Negative voltage")
            specificVin = True
        else:
            specificVin = False
        if self.r1 is None:
            self.r1 = 240
        if self.vout is None and self.r2 is None:
            raise TooFewArgsError("Too few arguments")
        if self.vout is None and self.r2 is not None:
            self.vout = 1.25 * (1 + (self.r2 / self.r1))
        if self.r2 is None:
            self.r2 = ((self.vout / 1.25) - 1) * self.r1
        if self.vout is not None and self.r2 is not None:
            self.r1 = self.r2 / ((self.vout / 1.25) - 1)
        if not specificVin:
            self.vin = round(self.vout + 3, 1)
        if self.vin - self.vout > 40 or self.vin - self.vout < 3:
            raise InputDifferenceError(
                "In-Out difference out of Range")  # Input-to-output differential voltage out of range
        if not specificVin:
            self.vin = str(self.vin) + "V to 40.0"
        if self.vout < 0 or self.r1 < 0 or self.r2 < 0:
            raise ImpossibleValueError("Negative voltage")
        
    def draw(self):
        if self.iout is not None:
            return f"""
            ```         
                        
Vin  ┌──────────┐         
○────┤IN     OUT├────┐ 
     │   ADJ    │   ┌┴┐
     └────┬─────┘   │ │ R1
          │         └┬┘
          └──────────┴──○
                     Iout
                            
R1 = {si_prefix.si_format(self.r1)}Ω
Vin = {self.vin}V
Iout = {self.iout}A
            ```
            """
        else:
            return f"""
            ```
            
Vin  ┌──────────┐    Vout
○────┤IN     OUT├────┬──○
     │   ADJ    │   ┌┴┐
     └────┬─────┘   │ │ R1
          │         └┬┘
          ├──────────┘
         ┌┴┐
         │ │ R2
         └┬┘
          │
         ─┴─
         GND
                
R1 = {si_prefix.si_format(self.r1)}Ω
R2 = {si_prefix.si_format(self.r2)}Ω
Vin = {self.vin}V
Vout = {self.vout}V
```
            """
            
    def gen_embed(self):
        try:
            self.calculate()
            self.args = True
        except TooFewArgsError:
            self.args = False
        if not self.args:
            self.vout = randint(1, 37)
            self.calculate()
            embed = discord.Embed(title="LM317 Adjustable Regulator **CV**")
            embed.add_field(name="Schematic", value=self.draw(), inline=False)
            embed.add_field(
                name="How to use this?",
                value=f"""With this command you can calculate required resistor values for an LM317 in CV mode (or CC if you provide an `iout`).
                Example: `lm317 vout=10v r1=240` to find r2.
                This accepts any SI-prefix (e.g. k, m, M, µ, etc.). 
                Writing the "V" after the voltages is optional but don't try writing out the `Ω` in Ohms 
                as it just confuses the bot (don't use R either).
                For CC use `lm317 iout=1`.
                """,
                inline=True)
            return embed
        else:
            self.calculate()
            embed = discord.Embed()
            if self.iout is not None:
                
                embed.add_field(name="Schematic", value=self.draw(), inline=False)
                embed.add_field(
                    name="Values",
                    value=f"R1 = {si_prefix.si_format(self.r1)}Ω\nVin = {self.vin}V\nIout = {self.iout}A")
                embed.add_field(
                    name=f"Closest E{(12 if self.e is None or 0 else self.e)} resistor values",
                    value=f"R1 = {si_prefix.si_format(pcb_mod.e_resistor(self.r1, int(12 if self.e is None or 0 else self.e)))}Ω\n")
                return embed
            embed.add_field(name="Schematic", value=self.draw(), inline=False)
            embed.add_field(
                name="Values",
                value=f"R1 = {si_prefix.si_format(self.r1)}Ω\nR2 = {si_prefix.si_format(self.r2)}Ω\nVin = {self.vin}V\nVout = {self.vout}V")
            embed.add_field(
                name=f"Closest E{(12 if self.e is None or 0 else self.e)} resistor values",
                value=f"R1 = {si_prefix.si_format(pcb_mod.e_resistor(self.r1, (12 if self.e is None or 0 else self.e)))}Ω\nR2 = {si_prefix.si_format(pcb_mod.e_resistor(self.r2, int(12 if self.e is None or 0 else self.e)))}Ω")
            return embed


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
        self.r1 = randint(1,1000000)
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
                        If you want the closest real value resistor you can get, you can specify the series with `e`
                        Example: `rc cut=20k c1=20n e=48` to find r1 and the closest E48 series resistor
                        
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


class ElectroCog(commands.Cog, name="Electronics commands"):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    def get_aliases(self, ctx):
        command = ctx.command
        if isinstance(ctx, scmd.ApplicationContext):
            prefix = "/"
        else:
            prefix = ctx.prefix
        alist = [f"`{prefix + command.name}`"] + [f'`{prefix + cmd}`' for cmd in command.aliases]
        return ", ".join(alist)
    
    @commands.command(name = "conversion", aliases = ["mm2mil", "mil2mm", "conv"])
    async def conversion(self, ctx, *, args = None):
        """
        Convert between mils and millimeters, or oz/ft² to mils and millimeters
        """
        try:
            conv = conversion(d = parse_input(args))
        except:
            conv = conversion(d={})
        await ctx.send(embed = conv.gen_embed())
        

    @commands.command(name = "pcbcalculator", aliases = ["pcbtrace", "trace", "pcb", "tracewidth", "tracecurrent"])
    async def pcbtrace(self, ctx, *, args = ""):
        """
        Calculate the PCB trace width or the maximum current it can handle using the IPC2221 standard.
        """
        try:
            if args.endswith("internal"):
                pcb = PCB_calc(d = parse_input(args), internal = True)
                await ctx.send(embed = pcb.gen_embed())
            elif args.endswith("limit"):
                pcb = PCB_calc(d = parse_input(args), limit = True)
                await ctx.send(embed = pcb.gen_embed())
            else:
                pcb = PCB_calc(d = {})
                await ctx.send(embed = pcb.gen_embed())
        except ImpossibleValueError:
            await util.errormsg(ctx, "Get real. <:troll:910540961958989934>")
            return
        

    @commands.command()
    async def divider(self, ctx, *, args=None):
        """
        Calculate values of an unloaded voltage divider. Run the command for more details.
        Thank you dimin for the idea and the "art"
        """
        try:
            div = VoltageDivider(d=parse_input(args))
        except:
            div = VoltageDivider(d={})
        await ctx.send(embed=div.gen_embed())

    @commands.command(name="cap_energy", aliases=["joule", "energy", "ce", "charge"])
    async def capacitor_energy(self, ctx, *, args=None):
        """
        Calculate the capacitor energy and charge in joules and coulomb using voltage and capacitance. Run the command for more details.
        """
        if not args:
            embed = discord.Embed(title="Capacitor energy calculation")
            embed.add_field(
                name="How to use this?",
                value=f"""With this command you can calculate capacitor energy and charge.
                Example: `{self.bot.command_prefix}cap_energy v=10v c=47u`to find energy and charge.
                This accepts any SI-prefix (e.g. k, m, M, µ, etc.). 
                Writing the "V" after the voltages is optional.
                You can also use {self.get_aliases(ctx)}.
                """,
                inline=True)
            await ctx.send(embed=embed)
        else:
            args_parsed = parse_input(args)
            c = si_prefix.si_parse(args_parsed["c"])
            v = si_prefix.si_parse(args_parsed["v"])
            e = si_prefix.si_format((0.5 * c) * (v ** 2))
            q = si_prefix.si_format(c * v)
            embed = discord.Embed(title="Capacitor charge calculator")
            embed.add_field(name="Energy", value=f"{e}J")
            embed.add_field(name="Charge", value=f"{q}C")
            await ctx.send(embed=embed)

    @commands.command(name="lm317", aliases=["317cv", "cv317", "LM317", "lm317cv"])
    async def lm317(self, ctx, *, args=""):
        """
        Calculate resistor values for an LM317 in CV and CC mode. Run the command for more details.
        """    
        args_parsed = parse_input(args)
        try:
            lm = LM317(d=args_parsed)
            await ctx.send(embed=lm.gen_embed())
        except InputOutOfRangeError:
            await util.errormsg(ctx, "Input voltage out of range. Please use values that won't fry the LM317.")
            return
        except InputDifferenceError:
            await util.errormsg(ctx,"Difference between input and output voltage is outside of datasheet recommended values.")
            return
        except TooFewArgsError:
            await util.errormsg(ctx, "Not enough arguments to compute anything.")
            return
        except ImpossibleValueError:
            await util.errormsg(ctx, "Get real. <:troll:910540961958989934>")
            return

    @commands.command(name="rc", aliases=["rcfilter", "filter", "lowpass"])
    async def rc_filter(self, ctx, *, args=""):
        """
        Calculate different aspects of an RC filter. Run the command for more details.
        """
        args_parsed = parse_input(args)
        try:
            if args.endswith("plot"):
                rc = RCFilter(d=args_parsed, plot=True)
                await ctx.send(embed=rc.gen_embed(), file=rc.gen_file())
            else:
                rc = RCFilter(d=args_parsed)
                await ctx.send(embed=rc.gen_embed())
        except TooFewArgsError:
            await util.errormsg(ctx, "Not enough arguments to compute anything.")
            return
        except ImpossibleValueError:
            await util.errormsg(ctx, "Get real. <:troll:910540961958989934>")
            return


def setup(bot):
    bot.add_cog(ElectroCog(bot))
