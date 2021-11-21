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



def draw_lm317_cv(indict):
    vin = indict["vin"]
    r1 = indict["r1"]
    r2 = indict["r2"]
    vout = indict["vout"]

    return f"""
    ```
    \n                               
           ┌──────────┐           
     <─────┤IN     OUT├─────┬──────► Vout = {vout}V
           │    ADJ   │    ┌┴┐
           └────┬─────┘    │ │ R1 = {r1}Ω
                │          └┬┘
                ├───────────┘
               ┌┴┐
               │ │ R2 = {r2}Ω
               └┬┘
                │
               ─┴─
               GND
    ```
    """
    
    
    
def draw_lm317_cc(indict):
    iout = indict["iout"]
    r = indict["r"]
    
    return f"""
    ```
    \n
           ┌──────────┐           
     <─────┤IN     OUT├─────┐
           │    ADJ   │    ┌┴┐
           └────┬─────┘    │ │ R = {r}Ω
                │          └┬┘ W = {w}W
                └───────────┴──────► 
                      Iout = {iout}I
    ```
    """
    
    
    
def parse_input(s):
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
    
    
    
def calculate_lm317(mode, b):
    match mode:
        case "cv":
            vin = si_prefix.si_parse(b["vin"])
            if not 4.25 <= vin <= 40.0:
                raise ValueError("Voltage out of Range")
            r1 = 240 #recommended r1 value from datasheet
            r2 = si_prefix.si_parse(b["r2"])
            vout = si_prefix.si_format(1.25 * (1 + (r2/r1))
            return dict(r1=r1, r2=r2, vin=vin, vout=vout)
            
        case "cc":
            iout = si_prefix.si_parse(b["iout"])
            if not 0 <= iout <= 1.5:
                raise ValueError("Current cannot exceed max ratings!")
            r = si_prefix.si_format(1.25 / iout)
            w = si_prefix.si_format(iout*iout*r)
            iout = si_prefix.si_parse(b["iout"])
            return dict(r=r, w=w, iout=iout)
        
        case _:
            raise ValueError("Invalid mode, please provide r1 and vin or iout")
    

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
    async def capacitor_energy(self, ctx, *, args):
        args_parsed = parse_input(args)
        c = si_prefix.si_parse(args_parsed["c"])
        v = si_prefix.si_parse(args_parsed["v"])
        e = si_prefix.si_format((0.5 * c) * (v**2))
        q = si_prefix.si_format(c * v)
        embed = discord.Embed(title="Capacitor charge calculator")
        embed.add_field(name="Energy", value=f"{e}J")
        embed.add_field(name="Charge", value=f"{q}C")
        await ctx.send(embed=embed)

    @commands.command()
    async def lm317(self, ctx, *, args):
        if not args:
            #help command goes here
        else
            args_parsed = parse_input(args)
            
        if args_parsed.get("r"):
            try:
                res = calculate_lm317("cv", args_parsed)
                embed = discord.Embed()
                embed.add_field(name="Image", value=draw_lm317_cv(res), inline=False)
                embed.add_field(
                    name="Values",
                    value=f"R1 = {res['r1']}Ω\nR2 = __{res['r2']}Ω__\nVout = {res['vout']}V")
                await ctx.send(embed=embed)
            except ValueError:
            await util.errormsg(ctx, "Input voltage out of range. Please use values that won't fry the LM317.")
            return 
            
        elif args_parsed.get("iout"):
            try:
                res = calculate_lm317("cc", args_parsed)
                embed = discord.Embed()
                embed.add_field(name="Image", value=draw_lm317_cc(res), inline=False)
                embed.add_field(
                    name="Values",
                    value=f"R = {res['r']}Ω\nW = __{res['w']}Ω__\nIout = {res['iout']}A")
                await ctx.send(embed=embed)
            except ValueError:
            await util.errormsg(ctx, "Output current will fry the LM317!")
            return


def setup(bot):
    bot.add_cog(ElectroCog(bot))