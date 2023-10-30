#  Copyright (c) 2019-2023 ThatRedKite and contributors

import discord
from discord.ext import commands

from thatkitebot.base.util import PermissonChecks as pc


class SudoCommands(commands.Cog, name="Bot Owner Commands"):
    """
    This cog contains commands that are used to manage the bot. These commands are only available to the bot owner.
    """
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.logger = bot.logger

    @commands.is_owner()
    @commands.command(aliases=["reload", "reboot", "r"])
    async def restart(self, ctx):
        """Reloads all cogs"""
        # this will currently break all image commands
        extensions = list(self.bot.extensions.keys())
        for extension in extensions:
                try:
                    self.bot.reload_extension(extension)
                except Exception as exc:
                    raise exc
                
        await ctx.send(f"All cogs reloaded.")
        self.logger.info(f"Reloaded {len(extensions)} Extensions")

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

    @commands.is_owner()
    @commands.command()
    async def list_servers(self, ctx):
        """
        Lists all the servers in the system console. Owner-only
        """
        for guild in self.bot.guilds:
            print(guild.name, f"({guild.id})")
            print(f"Owner: {guild.owner.name}\n")

    @commands.is_owner()
    @commands.command(name="sync_commands")
    async def _sync_commands(self, ctx):
        print("Synced all Commands!")
        await self.bot.sync_commands(method="bulk", force=True)


def setup(bot):
    bot.add_cog(SudoCommands(bot))
