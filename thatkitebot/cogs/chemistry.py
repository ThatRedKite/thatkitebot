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
            mass_analyzed = molmass.analyze(formula.upper())
            avg, mono, nom, mean = re.findall(masspattern, mass_analyzed)
            embed = discord.Embed(
                title=f"Molar mass for {formula.upper()} (in g/mol)",
                description=f"Average mass: `{avg}`\nMonoisotopic mass: `{mono}`\nNominal mass: `{nom}`\nMean mass: `{mean}`")
            embed.color = util.EmbedColors.lime_green
            await ctx.send(embed=embed)
        except ValueError:
            await util.errormsg(ctx, "This does not appear to be a valid Chemical. Please check your input.")


def setup(bot):
    bot.add_cog(ChemCog(bot))
