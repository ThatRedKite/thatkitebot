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

from backend import util
import discord
import asyncio
from discord.ext import commands
import subprocess


class SudoCommands(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.dirname = bot.dirname

    @commands.is_owner()
    @commands.command()
    async def kill(self, ctx):
        await self.bot.change_presence(status=discord.Status.offline)
        # clear the temp file folder
        util.clear_temp_folder(self.dirname)
        # close the aiohttp session
        await self.bot.aiohttp_session.close()
        # close the discord session
        await self.bot.close()

    @commands.is_owner()
    @commands.command()
    async def restart(self, ctx):
        extensions = list(self.bot.extensions.keys())
        for extension in extensions:
            try:
                self.bot.reload_extension(extension)
            except Exception as exc:
                raise exc

    @commands.is_owner()
    @commands.command()
    async def debug(self, ctx, state: str):
        self.bot.debugmode = util.bool_parse(state.lower())
        await ctx.message.delete()

    @commands.is_owner()
    @commands.command()
    async def echo(self, ctx, *, message: str):
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
