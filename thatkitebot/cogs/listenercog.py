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
import asyncio
from discord.ext import commands, tasks
from discord.ext.commands.errors import CommandInvokeError
from thatkitebot.backend.util import colors
from thatkitebot.backend.util import errormsg
import gc


class ListenerCog(commands.Cog):
    def __init__(self, bot):
        self.dirname = bot.dirname
        self.bot: discord.Client = bot
        self.colors = colors()

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: CommandInvokeError):
        if isinstance(error, commands.CommandNotFound):
            await errormsg(ctx, f"unknown command | do `{ctx.prefix}help` in order to see what i can do")
        elif isinstance(error, commands.CommandOnCooldown):
            await errormsg(ctx, f"Sorry, but this command is on cooldown! Please wait {int(error.retry_after)} seconds.")
        elif isinstance(error, CommandInvokeError) and self.bot.debugmode:
            await errormsg(ctx, repr(error))
            raise error
        else:
            raise error

    @tasks.loop(hours=1.0)
    async def reset_invoke_counter(self):
        self.bot.command_invokes_hour = 0

    @commands.Cog.listener()
    async def on_ready(self):
        print("\nbot successfully started!")
        self.reset_invoke_counter.start()

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        self.bot.command_invokes_hour += 1
        self.bot.command_invokes_total += 1
        gc.collect()

    @commands.Cog.listener()
    async def on_slash_command_error(self, ctx, ex):
        raise ex


def setup(bot):
    bot.add_cog(ListenerCog(bot))
