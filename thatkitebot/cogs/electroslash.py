#  Copyright (c) 2019-2024 ThatRedKite and contributors


from random import uniform

import discord
from discord.ext.commands import Cog

from thatkitebot.base.util import Parsing as p
from thatkitebot.base.util import errormsg
from thatkitebot.calculators.electronics.rc_filter import RCFilter
from thatkitebot.calculators import electronics as el
from thatkitebot.calculators.electronics.exceptions import *


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
            c1: discord.Option(str, "Value for C1:", required=False, default=None),
            r1: discord.Option(str, "Value for R1", required=False, default=None),
            fcut: discord.Option(str, "cutoff frequency:", required=False, default=None),
            draw_plot: discord.Option(bool, "Display plot", required=False, default=False)
    ):
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
            r1: discord.Option(str, "Value for R1", required=False, default=None),
            r2: discord.Option(str, "Value for R2", required=False, default=None),
            vin: discord.Option(str, "Input voltage", required=False, default=None),
            vout: discord.Option(str, "Output Voltage", required=False, default=False)
    ):
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
            r1: discord.Option(str, "Value for R1:", required=False, default=None),
            r2: discord.Option(str, "Value for R2:", required=False, default=None),
            vin: discord.Option(str, "Input Voltage", required=False, default=None),
            vout: discord.Option(str, "Output Voltage", required=False, default=None),
            iout: discord.Option(str, "Output Current", required=False, default=None)
    ):
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


def setup(bot):
    bot.add_cog(ElectroSlashCog(bot))
