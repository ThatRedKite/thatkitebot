
from random import randint

import discord
import si_prefix

from .exceptions import *
from . import pcb_mod


class LM317:
    def __init__(self, d: dict):
        self.r1 = int(si_prefix.si_parse(d.get("r1"))) if d.get("r1") else 240
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

        # this really needs an overhaul lol

        if not self.vout and not self.r2:
            raise TooFewArgsError("Too few arguments")

        elif not self.vout and not self.r2:
            self.vout = 1.25 * (1 + (self.r2 / self.r1))

        elif not self.r2:
            self.r2 = ((self.vout / 1.25) - 1) * self.r1

        elif self.vout and self.r2:
            self.r1 = self.r2 / ((self.vout / 1.25) - 1)

        elif not specificVin:
            self.vin = round(self.vout + 3, 1)

        elif 3 > (self.vin - self.vout) > 40:
            raise InputDifferenceError("In-Out difference out of Range")
            # Input-to-output differential voltage out of range
        elif not specificVin:
            self.vin = str(self.vin) + "V to 40.0"

        elif self.vout < 0 or self.r1 < 0 or self.r2 < 0:
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