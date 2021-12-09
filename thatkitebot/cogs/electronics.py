# ------------------------------------------------------------------------------
#  MIT License
#
#  Copyright (c) 2019-2021 ThatRedKite
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
#  documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
#  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
#  and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all copies or substantial portions of
#  the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
#  THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
#  TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
# ------------------------------------------------------------------------------
import math
from math import log10, sqrt
import matplotlib.pyplot as plt
from io import BytesIO
import discord
import discord.commands as scmd
from discord.ext import commands
import si_prefix
from random import randint
from random import uniform
from thatkitebot.backend import util


class InputDifferenceError(Exception):
    pass


class InputOutOfRangeError(Exception):
    pass


class TooFewArgsError(Exception):
    pass


class ImpossibleValueError(Exception):
    pass


def convert_e24(input):
    e24_list = [
        1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0,
        3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1,
    ]
    mantissa = input
    power = 0
    while mantissa >= 10:
        power += 1
        mantissa = mantissa / 10
    nearest = min(e24_list, key=lambda x: abs(x - mantissa))
    return nearest * 10 ** power


def draw_divider(indict):
    vin = indict["vin"]
    r1 = indict["r1"]
    r2 = indict["r2"]
    vout = indict["vout"]
    return f"""
    ```
     Vin = {vin}V
     ▲
     │
    ┌┴┐
    │ │ R1 = {r1}Ω
    │ │
    └┬┘
     ├───► Vout = {vout}V
    ┌┴┐
    │ │ R2 = {r2}Ω
    │ │
    └┬┘
     │
    ─┴─
    GND
    ```
    """
    

def parse_input(s):
    s = s.replace("=", " ").split(" ")
    s_dict = dict(zip(s[::2], s[1::2]))
    for key in s_dict.keys():
        old = s_dict[key]
        new = old.replace("v", "").replace("V", "").replace("u", "µ")
        s_dict.update({key: new})
    return s_dict


def slash_preprocessor(a: str):
    return a.replace("v", "").replace("V", "").replace("u", "µ").replace("F", "").strip() if a else None


def calculate_divider(mode, b):
    match mode:
        case "r1":
            r2 = si_prefix.si_parse(b["r2"])
            vin = si_prefix.si_parse(b["vin"])
            vout = si_prefix.si_parse(b["vout"])

            b.update({
                "r1": si_prefix.si_format(r2 * (vin - vout) / vout),
                "r2": si_prefix.si_format(r2),
                "vin": si_prefix.si_format(vin),
                "vout": si_prefix.si_format(vout),
            }
            )

        case "r2":
            r1 = si_prefix.si_parse(b["r1"])
            vin = si_prefix.si_parse(b["vin"])
            vout = si_prefix.si_parse(b["vout"])
            b.update({
                "r1": si_prefix.si_format(r1),
                "r2": si_prefix.si_format(vout * r1 / (vin - vout)),
                "vin": si_prefix.si_format(vin),
                "vout": si_prefix.si_format(vout),
            }
            )

        case "vout":
            r1 = si_prefix.si_parse(b["r1"])
            r2 = si_prefix.si_parse(b["r2"])
            vin = si_prefix.si_parse(b["vin"])
            b.update({
                "r1": si_prefix.si_format(r1),
                "r2": si_prefix.si_format(r2),
                "vin": si_prefix.si_format(vin),
                "vout": si_prefix.si_format(vin * r2 / (r1 + r2)),
            }
            )

        case _:
            raise ValueError("Invalid mode, please use r1, r2 or vout as mode")
    return b


class lm317:
    def __init__(self, d: dict):
        self.r1 = si_prefix.si_parse(d.get("r1")) if d.get("r1") else None
        self.r2 = si_prefix.si_parse(d.get("r2")) if d.get("r2") else None
        self.vout = si_prefix.si_parse(d.get("vout")) if d.get("vout") else None
        self.vin = si_prefix.si_parse(d.get("vin")) if d.get("vin") else None
        self.iout = si_prefix.si_parse(d.get("iout")) if d.get("iout") else None
    
    def calculate(self):
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
            \n
        Vin = {self.vin}V                         
            ┌──────────┐         
       >────┤IN     OUT├────┐ 
            │   ADJ    │   ┌┴┐
            └────┬─────┘   │ │ R1 = {si_prefix.si_format(self.r1)}Ω
                 │         └┬┘
                 └──────────┴──>
                            Iout = {self.iout}A
            ```
            """
        else:
            return f"""
            ```
            \n
        Vin = {self.vin}V                         
            ┌──────────┐     Vout = {self.vout}V    
       >────┤IN     OUT├────┬──> 
            │   ADJ    │   ┌┴┐
            └────┬─────┘   │ │ R1 = {si_prefix.si_format(self.r1)}Ω
                 │         └┬┘
                 ├──────────┘
                ┌┴┐
                │ │ R2 = {si_prefix.si_format(self.r2)}Ω
                └┬┘
                 │
                ─┴─
                GND
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
                    value=f"R1 = __{si_prefix.si_format(self.r1)}Ω__\nVin = {self.vin}V\nIout = {self.iout}A")
                embed.add_field(
                    name="Closest E24 resistor values",
                    value=f"R1 = __{si_prefix.si_format(convert_e24(self.r1))}__Ω\n")
                return embed
            embed.add_field(name="Schematic", value=self.draw(), inline=False)
            embed.add_field(
                name="Values",
                value=f"R1 = {si_prefix.si_format(self.r1)}Ω\nR2 = __{si_prefix.si_format(self.r2)}Ω__\nVin = {self.vin}V\nVout = {self.vout}V")
            embed.add_field(
                name="Closest E24 resistor values",
                value=f"R1 = {si_prefix.si_format(convert_e24(self.r1))}Ω\nR2 = __{si_prefix.si_format(convert_e24(self.r2))}Ω__")
            return embed


class rcFilter:
    def __init__(self, d: dict, plot=False):
        self.r1 = si_prefix.si_parse(d.get("r1")) if d.get("r1") else None
        self.c1 = si_prefix.si_parse(d.get("c1")) if d.get("c1") else None
        self.fcut = si_prefix.si_parse(d.get("fcut")) if d.get("fcut") else None
        self.doPlot = plot
    def calculate(self):
        if not self.fcut and self.r1 is not None and self.c1 is not None:
            self.fcut = 1 / (2 * math.pi * self.r1 * self.c1)
        elif not self.r1 and self.fcut is not None and self.c1 is not None:
            self.r1 = 1 / (2 * math.pi * self.fcut * self.c1)
        elif not self.c1 and self.fcut is not None and self.r1 is not None:
            self.c1 = 1 / (2 * math.pi * self.fcut * self.r1)
        else:
            raise TooFewArgsError()
    
    def draw(self):
        return f"""
        ```
        \n   
        R1 = {si_prefix.si_format(self.r1)}Ω     Fcut = {si_prefix.si_format(self.fcut)}Hz
        ┌───────┐ 
   IN ──┤       ├─────┬── OUT
        └───────┘     │ C1 = {si_prefix.si_format(self.c1)}F
                   ───┴───                                      
                   ───┬───        
                      │   
     ─────────────────┴──────
                            
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
        embed = discord.Embed(title="RC filter")
        try:
            self.calculate()
            self.mode = 1
        except TooFewArgsError:
            self.randomize()
            self.calculate()
            self.mode = None
        embed.add_field(name="Schematic", value=self.draw(), inline=False)
        if not self.mode:
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
            if self.doPlot:
                embed.set_image(url="attachment://rc.png")
            return embed
        if embed:
            embed.add_field(
                    name="Values",
                    value=f"R1 = __{si_prefix.si_format(self.r1)}Ω__\nC1 = {si_prefix.si_format(self.c1)}F\nFcut = {si_prefix.si_format(self.fcut)}Hz")
            embed.add_field(
                    name="Closest E24 resistor value",
                    value=f"R1 = __{si_prefix.si_format(convert_e24(self.r1))}Ω__")
            if self.doPlot:
                embed.set_image(url="attachment://rc.png")
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

    @commands.command()
    async def divider(self, ctx, *, args=None):
        """
        Calculate values of an unloaded voltage divider. Run the command for more details.
        Thank you dimin for the idea and the "art"
        """
        if not args:
            random_divider = {
                "r1": str(randint(1, 10000000)),
                "r2": str(randint(1, 10000000)),
                "vin": str(randint(1, 1000))
            }

            embed = discord.Embed(title="Unloaded voltage divider calculation")
            embed.add_field(name="Image", value=draw_divider(calculate_divider("vout", random_divider)), inline=False)
            embed.add_field(
                name="How to use this?",
                value=f"""With this command you can calculate different values of an unloaded voltage divider.
                Example: `{self.bot.command_prefix}divider vin=10v r2=3k vout=3v`to find the value of R1.
                The bot will try to figure out what you are looking for based on the value you didn't enter.
                You can do the same for every value except Vin.
                This accepts any SI-prefix (e.g. k, m, M, µ, etc.). 
                Writing the "V" after the voltages is optional but don't try writing out the `Ω` in Ohms 
                as it just confuses the bot (don't use R either).
                """,
                inline=True)
            embed.set_footer(text="Note: the above voltage divider is randomly generated")
            await ctx.send(embed=embed)
        else:
            args_parsed = parse_input(args)

        if args_parsed.get("r1") and args_parsed.get("vin") and args_parsed.get("vout") and not args_parsed.get("r2"):
            res = calculate_divider("r2", args_parsed)
            embed = discord.Embed(title="Unloaded voltage divider calculation")
            embed.add_field(name="Image", value=draw_divider(res), inline=False)
            embed.add_field(
                name="Values",
                value=f"R1 =  {res['r1']}Ω\nR2 = __{res['r2']}Ω__\nVin = {res['vin']}V\nVout = {res['vout']}V")
            embed.set_footer(text="Note: the underlined value is the output of the calculator (i.e the missing value)")
            await ctx.send(embed=embed)

        elif args_parsed.get("r2") and args_parsed.get("vin") and args_parsed.get("vout") and not args_parsed.get("r1"):
            res = calculate_divider("r1", args_parsed)
            embed = discord.Embed(title="Unloaded voltage divider calculation")
            embed.add_field(name="Image", value=draw_divider(res), inline=False)
            embed.add_field(
                name="Values",
                value=f"R1 = __{res['r1']}__Ω\nR2 = {res['r2']}Ω\nVin = {res['vin']}V\nVout = {res['vout']}V"
            )
            embed.set_footer(text="Note: the underlined value is the output of the calculator (i.e the missing value)")
            await ctx.send(embed=embed)

        elif args_parsed.get("r1") and args_parsed.get("r2") and args_parsed.get("vin") and not args_parsed.get("vout"):
            res = calculate_divider("vout", args_parsed)
            embed = discord.Embed(title="Unloaded voltage divider calculation")
            embed.add_field(name="Image", value=draw_divider(res), inline=False)
            embed.add_field(
                name="Values",
                value=f"R1 = {res['r1']}Ω\nR2 = {res['r2']}Ω\nVin = {res['vin']}V\nVout = __{res['vout']}V__")
            embed.set_footer(text="Note: the underlined value is the output of the calculator (i.e the missing value)")
            await ctx.send(embed=embed)

        elif args_parsed.get("r1") and args_parsed.get("r2") and args_parsed.get("vin") and args_parsed.get("vout"):
            await util.errormsg(ctx, "There is nothing to calculate. Please enter exactly 3 values")

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
            lm = lm317(d=args_parsed)
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
                rc = rcFilter(d=args_parsed, plot=True)
                await ctx.send(embed=rc.gen_embed(), file=rc.gen_file())
            else:
                rc = rcFilter(d=args_parsed)
                await ctx.send(embed=rc.gen_embed())
        except TooFewArgsError:
            await util.errormsg(ctx, "Not enough arguments to compute anything.")
            return

    @scmd.slash_command(guild_ids=[759419755253465188], name="rc")
    async def _rc(
            self,
            ctx: discord.ApplicationContext,
            c1: scmd.Option(str, "Value for C1:", required=False, default=None),
            r1: scmd.Option(str, "Value for R1", required=False, default=None),
            fcut: scmd.Option(str, "cutoff frequency:", required=False, default=None),
            draw_plot: scmd.Option(bool, "Display plot", required=False, default=False)
    ):
        """
        Calculate different aspects of an RC filter.
        Run the command for more details.
        """
        if not c1 and not r1 and not fcut:
            random_rc = {
                "fcut": str(uniform(0.1, 10 ** 5)),
                "r1": str(uniform(100, 100000))
            }
            args_parsed = parse_input(random_rc)
            rc = rcFilter(d=args_parsed, plot=False)
            await ctx.respond(embed=rc.gen_embed())
            return

        args_parsed = dict(
            c1=slash_preprocessor(c1),
            r1=slash_preprocessor(r1),
            fcut=slash_preprocessor(fcut)
        )
        try:
            if draw_plot:
                rc = rcFilter(d=args_parsed, plot=True)
                await ctx.respond(embed=rc.gen_embed(), file=rc.gen_file())
            else:
                rc = rcFilter(d=args_parsed, plot=False)
                await ctx.respond(embed=rc.gen_embed())

        except TooFewArgsError:
            a = await util.errormsg(ctx, "Not enough arguments to compute anything.", embed_only=True)
            await ctx.respond(embed=a)
            return


def setup(bot):
    bot.add_cog(ElectroCog(bot))
