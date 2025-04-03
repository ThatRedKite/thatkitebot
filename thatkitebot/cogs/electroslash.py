#region License
"""
MIT License

Copyright (c) 2019-present The Kitebot Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
#endregion

#region Imports
from random import uniform

import discord
from discord.ext.commands import Cog

from thatkitebot.base.util import Parsing as p
from thatkitebot.base.util import errormsg
from thatkitebot.calculators.electronics.rc_filter import RCFilter
from thatkitebot.calculators import electronics as el
from thatkitebot.calculators.electronics.exceptions import *
#endregion

#region Cog
class ElectroSlashCog(Cog, name="Electronics slash commands"):
    """
    A cog for slash commands related to electronics.
    """
    def __init__(self, bot):
        self.bot = bot

    @discord.command(name="rc")
    async def _rc(
            self,
            ctx: discord.ApplicationContext,
            c1: discord.Option(str, "Value for C1:", required=False, default=None), #type:ignore
            r1: discord.Option(str, "Value for R1", required=False, default=None),#type:ignore
            fcut: discord.Option(str, "cutoff frequency:", required=False, default=None),#type:ignore
            draw_plot: discord.Option(bool, "Display plot", required=False, default=False)#type:ignore
    ) -> None:
        """
        Calculate different aspects of an RC filter.
        Run the command for more details.
        """
        if not c1 and not r1 and not fcut:
            args_parsed = {
                "fcut": str(uniform(0.1, 10 ** 5)),
                "r1": str(uniform(100, 100000))
            }

            rc = RCFilter(d=args_parsed, plot=False)
            await ctx.respond(embed=rc.gen_embed())
            return

        args_parsed = dict(
            c1=p.slash_command_arguments_parser(c1),
            r1=p.slash_command_arguments_parser(r1),
            fcut=p.slash_command_arguments_parser(fcut)
        )

        try:
            if draw_plot:
                rc = el.RCFilter(d=args_parsed, plot=True)
                await ctx.respond(embed=rc.gen_embed(), file=rc.gen_file())

            else:
                rc = el.RCFilter(d=args_parsed, plot=False)
                await ctx.respond(embed=rc.gen_embed())

        except TooFewArgsError:
            a = await errormsg(ctx, "Not enough arguments to compute anything.", embed_only=True)
            await ctx.respond(embed=a)
            return

    @discord.command(name="divider")
    async def _divider(
            self,
            ctx: discord.ApplicationContext,
            r1: discord.Option(str, "Value for R1", required=False, default=None),#type:ignore
            r2: discord.Option(str, "Value for R2", required=False, default=None),#type:ignore
            vin: discord.Option(str, "Input voltage", required=False, default=None),#type:ignore
            vout: discord.Option(str, "Output Voltage", required=False, default=False)#type:ignore
    ) -> None:
        """
        Calculate values of an unloaded voltage divider. Run the command for more details.
        Thank you dimin for the idea and the "art"
        """
        args_parsed = dict(
            r1=p.slash_command_arguments_parser(r1),
            r2=p.slash_command_arguments_parser(r2),
            vin=p.slash_command_arguments_parser(vin),
            vout=p.slash_command_arguments_parser(vout)
        )
        div = el.VoltageDivider(d=args_parsed)
        await ctx.respond(embed=div.gen_embed())

    @discord.command(name="lm317")
    async def lm317(
            self,
            ctx: discord.ApplicationContext,
            r1: discord.Option(str, "Value for R1:", required=False, default=None),#type:ignore
            r2: discord.Option(str, "Value for R2:", required=False, default=None),#type:ignore
            vin: discord.Option(str, "Input Voltage", required=False, default=None),#type:ignore
            vout: discord.Option(str, "Output Voltage", required=False, default=None),#type:ignore
            iout: discord.Option(str, "Output Current", required=False, default=None)#type:ignore
    ) -> None:
        """
        Calculate resistor values for an LM317 in CV and CC mode. Run the command for more details.
        """
        await ctx.defer()
        args_parsed = dict(
            r1=p.slash_command_arguments_parser(r1),
            r2=p.slash_command_arguments_parser(r2),
            vin=p.slash_command_arguments_parser(vin),
            vout=p.slash_command_arguments_parser(vout),
            iout=p.slash_command_arguments_parser(iout)
        )

        try:
            lm = el.LM317(d=args_parsed)
            await ctx.followup.send(embed=lm.gen_embed())

        except InputOutOfRangeError:
            await errormsg(ctx, "Input voltage out of range. Please use values that won't fry the LM317.")
            return

        except InputDifferenceError:
            await errormsg(ctx, "Difference between input and output voltage is outside of datasheet recommended values.")
            return

        except TooFewArgsError:
            await errormsg(ctx, "Not enough arguments to compute anything.")
            return

        except ImpossibleValueError:
            await errormsg(ctx, "Get real. <:troll:910540961958989934>")
            return
#endregion

def setup(bot) -> None:
    bot.add_cog(ElectroSlashCog(bot))
