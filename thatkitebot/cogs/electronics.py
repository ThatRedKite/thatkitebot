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
import discord
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

def convert_E24(input):
    E24_list = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0,	2.2, 2.4, 2.7, 3.0, 3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]
    buff = input
    power = 0
    while(buff>10):
        power += 1
        buff = buff/10
    nearest = 0
    neatest_diff = 100
    for n in E24_list:
        if(abs(n - buff) < neatest_diff):
            nearest = n
            neatest_diff = abs(n - buff)
    return(nearest * 10 ** power)


def columnize(indict):
    """turns a dictionary of strings into columns"""


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


def draw_lm317(indict):
    vin = indict["vin"]
    r1 = indict["r1"]
    r2 = indict["r2"]
    vout = indict["vout"]

    return f"""
    ```
    \n
Vin = {vin}V                         
     ┌──────────┐     Vout = {vout}V    
>────┤IN     OUT├────┬──> 
     │   ADJ    │   ┌┴┐
     └────┬─────┘   │ │ R1 = {r1}Ω
          │         └┬┘
          ├──────────┘
         ┌┴┐
         │ │ R2 = {r2}Ω
         └┬┘
          │
         ─┴─
         GND
    ```
    """


def draw_lm317_cc(indict):
    vin = indict["vin"]
    r1 = indict["r1"]
    iout = indict["iout"]

    return f"""
    ```
    \n
Vin = {vin}V                         
     ┌──────────┐         
>────┤IN     OUT├────┐ 
     │   ADJ    │   ┌┴┐
     └────┬─────┘   │ │ R1 = {r1}Ω
          │         └┬┘
          └──────────┴──>
                      Iout = {iout}A
    ```
    """


def parse_input(s):
    s = s.lower()
    s = s.replace("=", " ").split(" ")
    s_dict = dict(zip(s[::2], s[1::2]))
    for key in s_dict.keys():
        old = s_dict[key]
        new = old.replace("v", "").replace("V", "").replace("u", "µ")
        s_dict.update({key:new})
    return s_dict


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


def calculate_lm317(b):
    if "iout" in b:
        return(calculate_lm317_cc(b))
    try:
        vin = si_prefix.si_parse(b["vin"])
        if not 3.0 <= vin <= 40.0:
            raise InputOutOfRangeError("Voltage out of Range")
        if vin < 0:
            raise ImpossibleValueError("Negative voltage")
        specificVin = True
    except:
        specificVin = False
    try:
        vout = si_prefix.si_parse(b["vout"])
    except:
        vout = None
    try:
        r1 = si_prefix.si_parse(b["r1"])
    except:
        r1 = 240
    try:
        r2 = si_prefix.si_parse(b["r2"])
    except:
        r2 = None

    if vout is None and r2 is None:
        raise TooFewArgsError("Too few arguments")    
    if vout is None:
        vout = 1.25 * (1 + (r2/r1))
    if r2 is None:
        r2 = ((vout / 1.25) - 1) * r1
    if not specificVin:
        vin = round(vout + 3, 1)
        
    if vin - vout > 40 or vin - vout < 3:
        raise InputDifferenceError("In-Out difference out of Range") # Input-to-output differential voltage out of range
    if not specificVin:
        vin = str(vin) + "V to 40.0"
    if vout < 0 or r1 < 0 or r2 < 0:
        raise ImpossibleValueError("Negative voltage")
    return dict(r1=r1, r2=round(r2,1), vin=vin, vout=si_prefix.si_format(vout), E24_r1=si_prefix.si_format(convert_E24(r1)), E24_r2=si_prefix.si_format(convert_E24(r2)))


def calculate_lm317_cc(b):
    r1 = 0
    iout = 0
    if "iout" in b:
        iout = si_prefix.si_parse(b["iout"])
        if iout < 0:
            raise ImpossibleValueError("Get real")
        elif iout > 1.5:
            raise InputOutOfRangeError("Your LM317 will explode")
        r1=1.25/iout
    elif "r1" in b:
        r1 = si_prefix.si_parse(b["r1"])
        iout = 1.25/r1
        if iout < 0:
            raise ImpossibleValueError("Get real")
        elif iout > 1.5:
            raise InputOutOfRangeError("Your LM317 will explode")
    else:
        raise TooFewArgsError()
    vin = "4.25V to 40.0"   
    return dict(r1=si_prefix.si_format(r1), iout=si_prefix.si_format(iout), E24_r1=si_prefix.si_format(convert_E24(r1)), vin=vin)


class ElectroCog(commands.Cog, name="Electronics commands"):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

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
            embed.set_footer(text="Note: the underlined res is the output of the calculator (i.e the missing value)")
            await ctx.send(embed=embed)

        elif args_parsed.get("r2") and args_parsed.get("vin") and args_parsed.get("vout") and not args_parsed.get("r1"):
            res = calculate_divider("r1", args_parsed)
            embed = discord.Embed(title="Unloaded voltage divider calculation")
            embed.add_field(name="Image", value=draw_divider(res), inline=False)
            embed.add_field(
                name="Values",
                value=f"R1 = __{res['r1']}__Ω\nR2 = {res['r2']}Ω\nVin = {res['vin']}V\nVout = {res['vout']}V"
            )
            embed.set_footer(text="Note: the underlined res is the output of the calculator (i.e the missing value)")
            await ctx.send(embed=embed)

        elif args_parsed.get("r1") and args_parsed.get("r2") and args_parsed.get("vin") and not args_parsed.get("vout"):
            res = calculate_divider("vout", args_parsed)
            embed = discord.Embed(title="Unloaded voltage divider calculation")
            embed.add_field(name="Image", value=draw_divider(res), inline=False)
            embed.add_field(
                name="Values",
                value=f"R1 = {res['r1']}Ω\nR2 = {res['r2']}Ω\nVin = {res['vin']}V\nVout = __{res['vout']}V__")
            embed.set_footer(text="Note: the underlined res is the output of the calculator (i.e the missing value)")
            await ctx.send(embed=embed)

        elif args_parsed.get("r1") and args_parsed.get("r2") and args_parsed.get("vin") and args_parsed.get("vout"):
            await util.errormsg(ctx, "There is nothing to calculate. Please enter exactly 3 values")

    @commands.command(name="cap_energy", aliases=["joule", "energy", "ce", "charge"])
    async def capacitor_energy(self, ctx, *, args = None):
        """
        Calculate the capacitor energy and charge in joules and coulomb using voltage and capacitance.
        """
        if not args:
            embed = discord.Embed(title="Capacitor energy calculation")
            embed.add_field(
            name="How to use this?",
                value=f"""With this command you can calculate capacitor energy and charge.
                Example: `{self.bot.command_prefix}cap_energy v=10v c=47u`to find energy and charge.
                This accepts any SI-prefix (e.g. k, m, M, µ, etc.). 
                Writing the "V" after the voltages is optional.
                You can also use `{self.bot.command_prefix}joule`, `{self.bot.command_prefix}energy`, `{self.bot.command_prefix}ce` and `{self.bot.command_prefix}charge`.
                """,
                inline=True)
                # TODO
                # Add something to automatically grab the aliases and command name
            await ctx.send(embed=embed)
        else:
            args_parsed = parse_input(args)
            c = si_prefix.si_parse(args_parsed["c"])
            v = si_prefix.si_parse(args_parsed["v"])
            e = si_prefix.si_format((0.5 * c) * (v**2))
            q = si_prefix.si_format(c * v)
            embed = discord.Embed(title="Capacitor charge calculator")
            embed.add_field(name="Energy", value=f"{e}J")
            embed.add_field(name="Charge", value=f"{q}C")
            await ctx.send(embed=embed)
        
    @commands.command(name="lm317", aliases=["317cv", "cv317", "LM317", "lm317cv"])
    async def lm317(self, ctx, *, args = None):
        """
        Calculate resistor values for an LM317 in CV mode for CC mode use `lm317cc`.
        """
        if not args:
            random_lm = {
                "vout": str(randint(1, 37))
            }
            embed = discord.Embed(title="LM317 Adjustable Regulator **CV**")
            embed.add_field(name="Image", value=draw_lm317(calculate_lm317(random_lm)), inline=False)
            embed.add_field(
            name="How to use this?",
                value=f"""With this command you can calculate required resistor values for an LM317 in CV mode.
                Example: `{self.bot.command_prefix}lm317 vout=10v r1=240` to find r2.
                This accepts any SI-prefix (e.g. k, m, M, µ, etc.). 
                Writing the "V" after the voltages is optional but don't try writing out the `Ω` in Ohms 
                as it just confuses the bot (don't use R either).
                You can also use `{self.bot.command_prefix}317cv`, `{self.bot.command_prefix}cv317` and `{self.bot.command_prefix}lm317cv`.
                For CC use `{self.bot.command_prefix}lm317cc`.
                """,
                inline=True)
                # TODO
                # Add something to automatically grab the aliases and command name
            await ctx.send(embed=embed)
        else:
            args_parsed = parse_input(args)
            try:
                res = calculate_lm317(args_parsed)
                if "iout" in res:
                    res = calculate_lm317_cc(args_parsed)
                    embed = discord.Embed()
                    embed.add_field(name="Image", value=draw_lm317_cc(res), inline=False)
                    embed.add_field(
                    name="Values",
                    value=f"R1 = __{res['r1']}Ω__\nVin = {res['vin']}V\nIout = {res['iout']}A")
                    embed.add_field(
                    name="Closest E24 resistor values",
                    value=f"R1 = __{res['r1']}Ω__")
                    await ctx.send(embed=embed)
                    return
                embed = discord.Embed()
                embed.add_field(name="Image", value=draw_lm317(res), inline=False)
                embed.add_field(
                    name="Values",
                    value=f"R1 = {res['r1']}Ω\nR2 = __{res['r2']}Ω__\nVin = {res['vin']}V\nVout = {res['vout']}V")
                embed.add_field(
                    name="Closest E24 resistor values",
                    value=f"R1 = {res['E24_r1']}Ω\nR2 = __{res['E24_r2']}Ω__")
                await ctx.send(embed=embed)
            except InputOutOfRangeError:
                await util.errormsg(ctx, "Input voltage out of range. Please use values that won't fry the LM317.")
                return
            except InputDifferenceError:
                await util.errormsg(ctx, "Difference between input and output voltage is outside of datasheet recommended values.")
                return
            except TooFewArgsError:
                await util.errormsg(ctx, "Not enough arguments to compute anything.")
                return
            except ImpossibleValueError:
                await util.errormsg(ctx, "Get real. <:troll:910540961958989934>")
                return

    @commands.command(name="lm317cc", aliases=["317cc", "cc317", "LM317cc"])
    async def lm317cc(self, ctx, *, args = None):
        """
        Calculate resistor values for an LM317 in CC mode for CV mode use `lm317cv`.
        """
        if not args:
            random_lm = {
                "iout": str(uniform(0.1, 1.5))
            }
            embed = discord.Embed(title="LM317 Adjustable Regulator **CC**")
            embed.add_field(name="Image", value=draw_lm317_cc(calculate_lm317_cc(random_lm)), inline=False)
            embed.add_field(
            name="How to use this?",
                value=f"""With this command you can calculate required resistor values for an LM317 in CC mode.
                Example: `{self.bot.command_prefix}lm317cc iout=1.3` to find r1.
                This accepts any SI-prefix (e.g. k, m, M, µ, etc.). 
                Writing the "V" after the voltages is optional but don't try writing out the `Ω` in Ohms 
                as it just confuses the bot (don't use R either).
                You can also use `{self.bot.command_prefix}317cc`, `{self.bot.command_prefix}cc317` and `{self.bot.command_prefix}lm317cc`.
                For CV use `{self.bot.command_prefix}lm317cv`.
                """,
                inline=True)
                # TODO
                # Add something to automatically grab the aliases and command name
            await ctx.send(embed=embed)
        else:
            args_parsed = parse_input(args)
            try:
                res = calculate_lm317_cc(args_parsed)
                embed = discord.Embed()
                embed.add_field(name="Image", value=draw_lm317_cc(res), inline=False)
                embed.add_field(
                    name="Values",
                    value=f"R1 = __{res['r1']}Ω__\nVin = {res['vin']}V\nIout = {res['iout']}A")
                embed.add_field(
                    name="Closest E24 resistor values",
                    value=f"R1 = __{res['r1']}Ω__")
                await ctx.send(embed=embed)
            except InputOutOfRangeError:
                await util.errormsg(ctx, "Input voltage out of range. Please use values that won't fry the LM317.")
                return
            except InputDifferenceError:
                await util.errormsg(ctx, "Difference between input and output voltage is outside of datasheet recommended values.")
                return
            except TooFewArgsError:
                await util.errormsg(ctx, "Not enough arguments to compute anything.")
                return
            except ImpossibleValueError:
                await util.errormsg(ctx, "Get real. <:troll:910540961958989934>")
                return


def setup(bot):
    bot.add_cog(ElectroCog(bot))
