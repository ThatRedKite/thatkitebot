
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
            mass_pattern = re.compile(r"mass: (\S+)\n")
            mass_analyzed = molmass.analyze(formula)
            avg, mono, nom, mean = re.findall(mass_pattern, mass_analyzed)
            embed = discord.Embed(
                title=f"Molar mass for {formula} (in g/mol)",
                description=f"Average mass: `{avg}`\nMonoisotopic mass: `{mono}`\nNominal mass: `{nom}`\nMean mass: `{mean}`")
            embed.color = util.EmbedColors.lime_green
            await ctx.send(embed=embed)
        except ValueError:
            await util.errormsg(ctx, "This does not appear to be a valid Chemical. Please check your input.")


def setup(bot):
    bot.add_cog(ChemCog(bot))
