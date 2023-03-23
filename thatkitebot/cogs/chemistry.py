
import discord
from discord.ext import commands
import molmass
import re
from thatkitebot.base import util


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


def setup(bot):
    bot.add_cog(ChemCog(bot))
