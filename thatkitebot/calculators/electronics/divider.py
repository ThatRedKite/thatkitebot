from random import randint

import si_prefix
import discord

from .exceptions import *


class VoltageDivider:
    def __init__(self, d: dict):
        self.vin = si_prefix.si_parse(d.get("vin")) if d.get("vin") else None
        self.vout = si_prefix.si_parse(d.get("vout")) if d.get("vout") else None
        self.r1 = si_prefix.si_parse(d.get("r1")) if d.get("r1") else None
        self.r2 = si_prefix.si_parse(d.get("r2")) if d.get("r2") else None
        self.e = int(d.get("e")) if d.get("e") else 12
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
        self.r1 = randint(1, 1000000)
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
                """
                embed.add_field(
                    name=f"Closest E{self.e} resistor values",
                    value=f"R1 = {si_prefix.si_format(int(pcb_mod.e_resistor(self.r1, self.e)))}Ω\nR2 = {si_prefix.si_format(int(pcb_mod.e_resistor(self.r2, self.e)))}Ω")
                """

        if embed:
            return embed