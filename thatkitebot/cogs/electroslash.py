#  Copyright (c) 2019-2022 ThatRedKite and contributors

import discord
from discord.ext.commands import Cog
from thatkitebot.cogs import electronics as el
import discord.commands as scmd
from random import uniform
from thatkitebot.backend import util


class ElectroSlashCog(Cog, name="Electronics slash commands"):
    """
    A cog for slash commands related to electronics
    """
    def __init__(self, bot):
        self.bot = bot

    @scmd.slash_command(name="rc")
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
            args_parsed = el.parse_input(random_rc)
            rc = el.RCFilter(d=args_parsed, plot=False)
            await ctx.respond(embed=rc.gen_embed())
            return

        args_parsed = dict(
            c1=el.slash_preprocessor(c1),
            r1=el.slash_preprocessor(r1),
            fcut=el.slash_preprocessor(fcut)
        )
        try:
            if draw_plot:
                rc = el.RCFilter(d=args_parsed, plot=True)
                await ctx.respond(embed=rc.gen_embed(), file=rc.gen_file())
            else:
                rc = el.RCFilter(d=args_parsed, plot=False)
                await ctx.respond(embed=rc.gen_embed())

        except el.TooFewArgsError:
            a = await util.errormsg(ctx, "Not enough arguments to compute anything.", embed_only=True)
            await ctx.respond(embed=a)
            return

    @scmd.slash_command(name="divider")
    async def _divider(
            self,
            ctx: discord.ApplicationContext,
            r1: scmd.Option(str, "Value for R1", required=False, default=None),
            r2: scmd.Option(str, "Value for R2", required=False, default=None),
            vin: scmd.Option(str, "Input voltage", required=False, default=None),
            vout: scmd.Option(str, "Output Voltage", required=False, default=False)
    ):
        """
        Calculate values of an unloaded voltage divider. Run the command for more details.
        Thank you dimin for the idea and the "art"
        """
        args_parsed = dict(
            r1=el.slash_preprocessor(r1),
            r2=el.slash_preprocessor(r2),
            vin=el.slash_preprocessor(vin),
            vout=el.slash_preprocessor(vout)
        )
        div = el.VoltageDivider(d=args_parsed)
        await ctx.respond(embed=div.gen_embed())


def setup(bot):
    bot.add_cog(ElectroSlashCog(bot))
