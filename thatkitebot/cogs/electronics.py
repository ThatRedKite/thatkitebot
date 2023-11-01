#  Copyright (c) 2019-2022 ThatRedKite and contributors

import discord
from discord.ext import commands
import si_prefix

from thatkitebot.base.util import Parsing as p
from thatkitebot.base.util import errormsg
from thatkitebot.calculators.electronics.rc_filter import RCFilter
from thatkitebot.calculators.electronics.divider import VoltageDivider
from thatkitebot.calculators.electronics.lm317 import LM317
from thatkitebot.calculators.electronics.pcb_calc import PCBConversion, PCB_calc
from thatkitebot.calculators.electronics.exceptions import *


class ElectroCog(commands.Cog, name="Electronics commands"):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    def get_aliases(self, ctx):
        command = ctx.command
        if isinstance(ctx, discord.commands.ApplicationContext):
            prefix = "/"
        else:
            prefix = ctx.prefix
        alist = [f"`{prefix + command.name}`"] + [f'`{prefix + cmd}`' for cmd in command.aliases]
        return ", ".join(alist)

    @commands.command(name="conversion", aliases=["mm2mil", "mil2mm", "conv"])
    async def conversion(self, ctx, *, args=None):
        """
        Convert between mils and millimeters, or oz/ft² to mils and millimeters
        """
        try:
            conv = PCBConversion(d=p.parse_arguments_input(args))
        except:
            conv = PCBConversion(d={})
        await ctx.send(embed=conv.gen_embed())

    @commands.command(name="pcbcalculator", aliases=["pcbtrace", "trace", "pcb", "tracewidth", "tracecurrent"])
    async def pcbtrace(self, ctx, *, args=""):
        """
        Calculate the PCB trace width or the maximum current it can handle using the IPC2221 standard.
        """
        try:
            if args.endswith("internal"):
                pcb = PCB_calc(d=p.parse_arguments_input(args), internal=True)
                await ctx.send(embed=pcb.gen_embed())
            elif args.endswith("limit"):
                pcb = PCB_calc(d=p.parse_arguments_input(args), limit=True)
                await ctx.send(embed=pcb.gen_embed())
            else:
                pcb = PCB_calc(d=p.parse_arguments_input(args), internal=False, limit=False)
                await ctx.send(embed=pcb.gen_embed())
        except ImpossibleValueError:
            await errormsg(ctx, "Get real. <:troll:910540961958989934>")
            return

    @commands.command()
    async def divider(self, ctx, *, args=None):
        """
        Calculate values of an unloaded voltage divider. Run the command for more details.
        Thank you dimin for the idea and the "art"
        """
        try:
            div = VoltageDivider(d=p.parse_arguments_input(args))
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
            args_parsed = p.parse_arguments_input(args)
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
        args_parsed = p.parse_arguments_input(args)

        try:
            lm = LM317(d=args_parsed)
            await ctx.send(embed=lm.gen_embed())
        except InputOutOfRangeError:
            await errormsg(ctx, "Input voltage out of range. Please use values that won't fry the LM317.")
            return
        except InputDifferenceError:
            await errormsg(ctx,
                                "Difference between input and output voltage is outside of datasheet recommended values.")
            return
        except TooFewArgsError:
            await errormsg(ctx, "Not enough arguments to compute anything.")
            return
        except ImpossibleValueError:
            await errormsg(ctx, "Get real. <:troll:910540961958989934>")
            return

    @commands.command(name="rc", aliases=["rcfilter", "filter", "lowpass"])
    async def rc_filter(self, ctx, *, args=""):
        """
        Calculate different aspects of an RC filter. Run the command for more details.
        """
        args_parsed = p.parse_arguments_input(args)
        try:
            if args.endswith("plot"):
                rc = RCFilter(d=args_parsed, plot=True)
                await ctx.send(embed=rc.gen_embed(), file=rc.gen_file())
            else:
                rc = RCFilter(d=args_parsed)
                await ctx.send(embed=rc.gen_embed())
        except TooFewArgsError:
            await errormsg(ctx, "Not enough arguments to compute anything.")
            return
        except ImpossibleValueError:
            await errormsg(ctx, "Get real. <:troll:910540961958989934>")
            return


def setup(bot):
    bot.add_cog(ElectroCog(bot))
