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
from discord.ext import commands, tasks
from discord.ext.commands.errors import CommandInvokeError
from thatkitebot.backend.util import errormsg
from thatkitebot.backend import cache
import aioredis
import json


class ListenerCog(commands.Cog):
    def __init__(self, bot):
        self.dirname = bot.dirname
        self.redis: aioredis.Redis = bot.redis_cache
        self.bot: discord.Client = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: CommandInvokeError):
        match type(error):
            case commands.CommandOnCooldown:
                await errormsg(ctx, f"Sorry, but this command is on cooldown! Please wait {int(error.retry_after)} seconds.")
            case commands.CommandInvokeError:
                if self.bot.debugmode:
                    await errormsg(ctx, repr(error))
                    raise error
                else:
                    raise error
            case commands.CheckFailure:
                await errormsg(ctx, "A check has failed! This command might be disabled on the server or you lack permission")
            case commands.MissingPermissions:
                await errormsg(ctx, "Sorry, but you don't have the permissions to do this")
            case commands.NotOwner:
                await errormsg(ctx, "Only the bot owner (ThatRedKite) can do this! Contact him if needed.")

    @tasks.loop(hours=1.0)
    async def reset_invoke_counter(self):
        self.bot.command_invokes_hour = 0

    @commands.Cog.listener()
    async def on_ready(self):
        print("\nbot successfully started!")
        self.reset_invoke_counter.start()
        await self.bot.change_presence(
            activity=discord.Activity(name="a battle against itself", type=5),
            status=discord.Status.online,
        )

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        self.bot.command_invokes_hour += 1
        self.bot.command_invokes_total += 1

    @commands.Cog.listener()
    async def on_slash_command_error(self, ctx, ex):
        raise ex

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        await cache.add_message_to_cache(self.redis, message)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        key = f"{payload.guild_id}:{payload.channel_id}:{payload.cached_message.author.id}:{payload.message_id}"
        if await self.redis.exists(key):
            await self.redis.delete(key)

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        key = f"{payload.guild_id}:{payload.channel_id}:{payload.cached_message.author.id}:{payload.message_id}"
        if await self.redis.exists(key):
            await cache.add_message_to_cache(self.redis, payload.cached_message)


def setup(bot):
    bot.add_cog(ListenerCog(bot))
