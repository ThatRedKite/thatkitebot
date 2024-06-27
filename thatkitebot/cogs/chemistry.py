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
import re

import discord
import molmass
from discord.ext import commands

from thatkitebot.base import util
#endregion

#region Cog
class ChemCog(commands.Cog, name="Chemistry commands"):
    """
    This cog contains commands for chemistry.
    """
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.id = "chem"
        self.can_be_disabled = True

    @commands.command(name="molar_mass", aliases=["mm"])
    async def molar_mass(self, ctx, *, formula):
        """
        Calculates the molar mass of a chemical formula.
        """
        try:
            mass_analyzed = molmass.analyze(formula)

            nominal = re.findall(r"Nominal mass: ([0-9.]*)", mass_analyzed)[0]
            average = re.findall(r"Average mass: ([0-9.]*)", mass_analyzed)[0]
            monoisotopic = re.findall(r"Monoisotopic mass: ([0-9.]*)", mass_analyzed)[0]
            mostabundant = re.findall(r"Most abundant mass: ([0-9.]*)", mass_analyzed)[0]

            num = re.findall("Number of atoms: ([0-9]*)", mass_analyzed)[0]

            embed = discord.Embed(
                title=f"Molar mass for {formula} (in g/mol)",
                description=(
                    f"Number of Atoms: {num}\n"
                    f"Nominal mass: {nominal}\n"
                    f"Average Mass: {average}\n"
                    f"Monoisotopic mass: {monoisotopic}\n"
                    f"Most abundant mass: {mostabundant}\n"
                )
            )
            embed.color = util.EmbedColors.lime_green
            await ctx.send(embed=embed)
        except IndexError or ValueError:
            await util.errormsg(ctx, "This does not appear to be a valid Chemical. Please check your input.")
#endregion

def setup(bot):
    bot.add_cog(ChemCog(bot))
