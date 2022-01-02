#  Copyright (c) 2019-2022 ThatRedKite and contributors

import discord
from discord.ext import commands, tasks
from discord.ext.commands.errors import CommandInvokeError
from thatkitebot.backend.util import errormsg
from thatkitebot.backend import cache
from thatkitebot.cogs import welcomecog
import aioredis
import time


class ListenerCog(commands.Cog):
    def __init__(self, bot):
        self.dirname = bot.dirname
        self.redis_cache: aioredis.Redis = bot.redis_cache
        self.redis_welcomes: aioredis.Redis = bot.redis_welcomes
        self.repost_redis: aioredis.Redis = bot.redis_repost
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
        await cache.add_message_to_cache(self.redis_cache, message)
        if self.bot.command_prefix not in message.content and message.author.id != self.bot.user.id:
            await welcomecog.update_count(self.redis_welcomes, message)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        key = f"{hex(payload.guild_id)}:{hex(payload.channel_id)}:{hex(payload.cached_message.author.id)}:{hex(payload.message_id)}"
        if await self.redis_cache.exists(key):
            await self.redis_cache.delete(key)

        # delete the associated repost if it exists
        if len(rkeys := [rkey async for rkey in self.repost_redis.scan_iter(match=f"{payload.message_id}:*")]) > 0:
            await self.repost_redis.delete(rkeys[0])

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        key = f"{hex(payload.guild_id)}:{hex(payload.channel_id)}:{hex(payload.cached_message.author.id)}:{hex(payload.message_id)}"
        if await self.redis_cache.exists(key):
            await cache.add_message_to_cache(self.redis_cache, payload.cached_message)

    @commands.Cog.listener()
    async def on_member_join(self, joinedmember):
        welcomechannel = joinedmember.guild.system_channel.id
        lastjoined = joinedmember.joined_at
        unixtime = time.mktime(lastjoined.timetuple())
        guild = joinedmember.guild.id
        key = f"latest_join:{guild}"
        datadict = dict(
            latest_join=int(unixtime),
            user_id=int(joinedmember.id),
            join_channel=int(welcomechannel)
        )
        await self.redis_welcomes.hmset(key, datadict)
        await joinedmember.guild.system_channel.send("welcome")


def setup(bot):
    bot.add_cog(ListenerCog(bot))
