#  Copyright (c) 2019-2022 ThatRedKite and contributors
import discord
from discord.ext import commands


class SudoCommands(commands.Cog, name="administrative commands"):
    """
    This cog contains commands that are used to manage the bot. These commands are only available to the bot owner.
    """
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.is_owner()
    @commands.command(aliases=["reload", "reboot", "r"])
    async def restart(self, ctx):
        """Reloads all cogs"""
        # this will currently break all image commands
        extensions = list(self.bot.extensions.keys())
        for extension in extensions:
                try:
                    self.bot.reload_extension(extension)
                    print(f"Reloaded {extension}")
                except Exception as exc:
                    raise exc
        await ctx.send(f"All cogs reloaded.")
        print("\n")

    @commands.is_owner()
    @commands.command()
    async def debug(self, ctx):
        """produces more verbose error messages"""
        self.bot.debug_mode = not self.bot.debug_mode
        await ctx.message.delete()

    @discord.guild_only()
    @commands.is_owner()
    @discord.slash_command()
    async def echo(
            self,
            ctx: discord.ApplicationContext,
            message: discord.Option(discord.SlashCommandOptionType.string, required=True),
    ):
        """pretend to be the bot"""
        if not ctx.author.id == self.bot.owner_id:
            return
        await ctx.send(message)


def setup(bot):
    bot.add_cog(SudoCommands(bot))
