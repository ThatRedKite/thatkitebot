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
import discord
from discord.ext import commands

from thatkitebot.base.util import PermissonChecks as pc
from thatkitebot.tkb_redis.settings import RedisFlags
#endregion

#region Cog
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
            message: discord.Option(discord.SlashCommandOptionType.string, required=True), # type: ignore
    ):
        """pretend to be the bot"""
        if not ctx.author.id == self.bot.owner_id:
            return
        #await ctx.send_response(message, ephemeral=True)
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

    @commands.is_owner()
    @commands.command(name="test", hidden=True)
    async def _test(self, ctx):
        # raise NotImplemented

        print(RedisFlags.FlagEnum.IMAGE)

#endregion
def setup(bot):
    bot.add_cog(SudoCommands(bot))
