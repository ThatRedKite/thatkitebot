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
from thatkitebot.backend import util


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
    return dict(zip(s[::2], s[1::2]))


def calculate(mode, b):
    match mode:
        case "r1":
            r2 = si_prefix.si_parse(b["r2"].replace("u", "µ"))
            vin = si_prefix.si_parse(b["vin"].replace("v", "").replace("V", "")).replace("u", "µ")
            vout = si_prefix.si_parse(b["vout"].replace("v", "").replace("V", "").replace("u", "µ"))

            b.update({
                "r1": si_prefix.si_format(r2 * (vin - vout) / vout),
                "r2": si_prefix.si_format(r2),
                "vin": si_prefix.si_format(vin),
                "vout": si_prefix.si_format(vout),
                }
            )

        case "r2":
            r1 = si_prefix.si_parse(b["r1"].replace("u", "µ"))
            vin = si_prefix.si_parse(b["vin"].replace("v", "").replace("V", "").replace("u", "µ"))
            vout = si_prefix.si_parse(b["vout"].replace("v", "").replace("V", "").replace("u", "µ"))
            b.update({
                "r1": si_prefix.si_format(r1),
                "r2": si_prefix.si_format(vout * r1 / (vin - vout)),
                "vin": si_prefix.si_format(vin),
                "vout": si_prefix.si_format(vout),
                }
            )

        case "vout":
            r1 = si_prefix.si_parse(b["r1"].replace("u", "µ"))
            r2 = si_prefix.si_parse(b["r2"].replace("u", "µ"))
            vin = si_prefix.si_parse(b["vin"].replace("v", "").replace("V", "").replace("u", "µ"))
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


class ElectroCog(commands.Cog, name="Electronics commands"):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.group()
    async def divider(self, ctx, *, args=None):
        if not args:
            random_divider = {
                "r1": str(randint(1, 10000000)),
                "r2": str(randint(1, 10000000)),
                "vin": str(randint(1, 1000))
            }

            embed = discord.Embed(title="Unloaded voltage divider calculation")
            embed.add_field(name="Image", value=draw_divider(calculate("vout", random_divider)), inline=False)
            embed.add_field(
                name="How to use this?",
                value=f"""With this command you can calculate different values of an unloaded voltage divider.
                Run `{self.bot.command_prefix}divider r1 vin=10v r2=3k vout=3v`to find the value of R1.
                You can do the same for every value except Vin (why would you even want to do that?).
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
            result = calculate("r2", args_parsed)
            embed = discord.Embed(title="Unloaded voltage divider calculation")
            embed.add_field(name="Image", value=draw_divider(result), inline=False)
            embed.add_field(
                name="Values",
                value=f"""
                R1 =  {result['r1']}Ω
                R2 = __{result['r2']}Ω__
                Vin = {result["vin"]}V
                Vout = {result["vout"]}V
                """
            )
            embed.set_footer(text="Note: the underlined result is the output of the calculator (i.e the missing value)")
            await ctx.send(embed=embed)

        elif args_parsed.get("r2") and args_parsed.get("vin") and args_parsed.get("vout") and not args_parsed.get("r1"):
            result = calculate("r1", args_parsed)
            embed = discord.Embed(title="Unloaded voltage divider calculation")
            embed.add_field(name="Image", value=draw_divider(result), inline=False)
            embed.add_field(
                name="Values",
                value=f"""
                R1 =  {result['r1']}Ω
                R2 = __{result['r2']}Ω__
                Vin = {result["vin"]}V
                Vout = {result["vout"]}V
                """
            )
            embed.set_footer(text="Note: the underlined result is the output of the calculator (i.e the missing value)")
            await ctx.send(embed=embed)

        elif args_parsed.get("r1") and args_parsed.get("r2") and args_parsed.get("vin") and not args_parsed.get("vout"):
            result = calculate("vout", args_parsed)
            embed = discord.Embed(title="Unloaded voltage divider calculation")
            embed.add_field(name="Image", value=draw_divider(result), inline=False)
            embed.add_field(
                name="Values",
                value=f"""
                R1 =  {result['r1']}Ω
                R2 = __{result['r2']}Ω__
                Vin = {result["vin"]}V
                Vout = {result["vout"]}V
                """
            )
            embed.set_footer(text="Note: the underlined result is the output of the calculator (i.e the missing value)")
            await ctx.send(embed=embed)

        elif args_parsed.get("r1") and args_parsed.get("r2") and args_parsed.get("vin") and args_parsed.get("vout"):
            await util.errormsg(ctx, "There is nothing to calculate. Please enter exactly 3 values")

def setup(bot):
    bot.add_cog(ElectroCog(bot))
