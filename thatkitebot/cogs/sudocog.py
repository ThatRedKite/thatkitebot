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

import gc

from thatkitebot.backend import util
import discord
from discord.ext import commands
import subprocess


class SudoCommands(commands.Cog, name="administrative commands"):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.dirname = bot.dirname

    @commands.is_owner()
    @commands.command()
    async def kill(self, ctx):
        """Kills the bot :("""
        await self.bot.change_presence(status=discord.Status.offline)
        # clear the temp file folder
        util.clear_temp_folder(self.dirname)
        # close the aiohttp session
        await self.bot.aiohttp_session.close()
        # close the redis connection
        self.redis.close()
        # close the discord session
        await self.bot.close()

    @commands.is_owner()
    @commands.command(aliases=["reload", "reboot", "r"])
    async def restart(self, ctx):
        """Reloads all cogs"""
        extensions = list(self.bot.extensions.keys())
        for extension in extensions:
            if not extension == "thatkitebot.cogs.electroslash":
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
        self.bot.debugmode = not self.bot.debugmode
        await ctx.message.delete()

    @commands.is_owner()
    @commands.command()
    async def echo(self, ctx, *, message: str):
        """pretend to be the bot"""
        await ctx.message.delete()
        await ctx.send(message)

    @commands.is_owner()
    @commands.command(aliases=["pull"])
    async def update(self, ctx):
        """Pull new git changes"""
        process = subprocess.Popen(["git", "pull"], stdout=subprocess.PIPE)
        out, error = process.communicate()
        if out:
            text = out.decode()
            if text == "Already up to date.\n":
                await ctx.send(f"Nothing to pull")
            else:
                await ctx.send(f"Pull successful, restart the bot for the update to take effect.")
        if error:
            await util.errormsg(ctx=ctx, msg="Could not pull")


def setup(bot):
    bot.add_cog(SudoCommands(bot))
