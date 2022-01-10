#  Copyright (c) 2019-2022 ThatRedKite and contributors

import discord
from discord.ext import commands
import molmass
import re
from thatkitebot.backend import util


class ChemCog(commands.Cog, name="Chemistry commands"):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.command(name="molar_mass", aliases=["mm"])
    async def molar_mass(self, ctx, *, formula):
        try:
            masspattern = re.compile("mass: (\S+)\n")
            mass_analyzed = molmass.analyze(formula)
            avg, mono, nom, mean = re.findall(masspattern, mass_analyzed)
            embed = discord.Embed(
                title=f"Molar mass for {formula} (in g/mol)",
                description=f"Average mass: `{avg}`\nMonoisotopic mass: `{mono}`\nNominal mass: `{nom}`\nMean mass: `{mean}`")
            embed.color = util.EmbedColors.lime_green
            await ctx.send(embed=embed)
        except ValueError:
            await util.errormsg(ctx, "This does not appear to be a valid Chemical. Please check your input.")


def setup(bot):
    bot.add_cog(ChemCog(bot))
