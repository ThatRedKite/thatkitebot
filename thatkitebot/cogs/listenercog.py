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
import logging

import discord
from datetime import datetime

from redis.exceptions import ConnectionError
from redis import asyncio as aioredis
from discord.ext import commands, tasks

import thatkitebot
from thatkitebot.base.util import errormsg
from thatkitebot.tkb_redis.cache import RedisCacheAsync, CacheInvalidMessageException, NoDataException
from thatkitebot.tkb_redis.settings import RedisFlags as flags
from thatkitebot.base.exceptions import *
#endregion

class ListenerCog(commands.Cog):
    """
    The perfect place to put random listeners in.
    """
    def __init__(self, bot):
        self.bot: thatkitebot.ThatKiteBot = bot
        self.redis: aioredis.Redis = bot.redis
        self.redis_cache: aioredis.Redis = bot.redis_cache
        self.redis_welcomes: aioredis.Redis = bot.redis_welcomes
        self.repost_redis: aioredis.Redis = bot.redis_repost

        self.logger: logging.Logger = bot.logger
        self.cache: RedisCacheAsync = bot.r_cache

    # global error handlers
    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        match type(error):
            case commands.CommandOnCooldown:
                await errormsg(ctx, f"Sorry, but this command is on cooldown! Please wait {round(error.retry_after, 1)} seconds.")
            case commands.CommandInvokeError:
                if self.bot.debug_mode:
                    await errormsg(ctx, repr(error))
                    
                if not isinstance(error, (NotEnoughMessagesException, StarboardDisabledException)):
                    self.bot.logger.error("Error during command: %s", error, exc_info=True)
            case discord.errors.CheckFailure:
                await errormsg(ctx, "A check has failed! This command might be disabled on the server or you lack permission")
            case commands.MissingPermissions:
                await errormsg(ctx, "Sorry, but you don't have the permissions to do this")

        if self.bot.debug_mode:
            raise error
            
    
    @commands.Cog.listener()
    async def on_application_command_error(self, ctx: commands.Context, error):
        match type(error):
            case commands.CommandOnCooldown:
                await errormsg(ctx, f"Sorry, but this command is on cooldown! Please wait {round(error.retry_after, 1)} seconds.")
            case commands.CommandInvokeError:
                if self.bot.debug_mode:
                    await errormsg(ctx, repr(error))
                raise error
            case discord.errors.CheckFailure:
                await errormsg(ctx, "A check has failed! This command might be disabled on the server or you lack permission")
            case commands.MissingPermissions:
                await errormsg(ctx, "Sorry, but you don't have the permissions to do this")

    @tasks.loop(hours=1.0)
    async def hourly_reset(self) -> None:
        self.bot.command_invokes_hour = 0
        self.bot.events_hour = 0

    @tasks.loop(minutes=1)
    async def database_ping(self) -> None:
        try:
            await self.redis.ping()
            await self.redis_cache.ping()
            # update last online time as well
            await self.redis.set("last", int(datetime.now().timestamp()))

        except ConnectionError as exc:
            self.logger.critical(f"REDIS: Lost connection to at least one redis instance!! Message: {repr(exc)}")
    
    # execs the cache pipeline every 60 seconds
    @tasks.loop(seconds=60)
    async def cache_update(self) -> None:
        # commit pending writes
        async with self.bot.cache_lock:
                await self.cache.exec()

    @commands.Cog.listener()
    async def on_connect(self) -> None:
        await self.bot.sync_commands()

    @commands.Cog.listener()
    async def on_ready(self) -> None:

        self.logger.info(f"{self.bot.user.name} is now ready")
        await self.bot.change_presence(
            activity=discord.Activity(name="suffering", type=5),
            status=discord.Status.online,
        )

    @commands.Cog.listener()
    async def on_command_completion(self, ctx) -> None:
        self.bot.command_invokes_hour += 1
        self.bot.command_invokes_total += 1
        self.bot.events_hour += 1
        self.bot.events_total += 1

    @commands.Cog.listener()
    async def on_slash_command_error(self, ctx, ex) -> None:
        raise ex

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        self.bot.events_hour += 1
        self.bot.events_total += 1

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent) -> None:
        self.bot.events_hour += 1
        self.bot.events_total += 1
        # async with self.bot.cache_lock:
        #     await self.cache.update_message_raw(payload)

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, payload: discord.RawBulkMessageDeleteEvent) -> None:
        self.bot.events_hour += 1
        self.bot.events_total += 1
       #await self.bot.r_cache.mass_expire_messages(payload)


    @commands.Cog.listener()
    async def on_member_update(self, _, after: discord.Member) -> None:
        self.bot.events_hour += 1
        self.bot.events_total += 1
        # await self.bot.add_user(after._user)
        pass
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        self.bot.events_hour += 1
        self.bot.events_total += 1

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent) -> None:
        self.bot.events_hour += 1
        self.bot.events_total += 1
        #await self.bot.delete_message_raw(payload)
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        self.bot.events_hour += 1
        self.bot.events_total += 1

        self.logger.info(f"Joined guild {guild.name} with {guild.member_count} users.")

        if not await self.redis.exists(f"flags:{guild.id}"):
            # initialize standard settings when joining a Guild if they don't exist
            pipe = self.redis.pipeline()
            await flags.set_guild_flag(pipe, guild.id, flags.FlagEnum.IMAGE, True)
            await flags.set_guild_flag(pipe, guild.id, flags.FlagEnum.CACHING, True)
            await flags.set_guild_flag(pipe, guild.id, flags.FlagEnum.UWU, True)

        # try to send a message informing about settings
        try:
            await guild.system_channel.send(
                (
                    "Thanks for inviting me! "
                    "Note that most of the advanced features (Moderation, Repost Detection, etc.) "
                    "are disabled by default and need to be enabled if you want to use them. "
                    "Use `/settings` to see what settings are available. "
                )
            )
        
        except TypeError:
            return
        
        except discord.Forbidden:
            return


def setup(bot) -> None:
    bot.add_cog(ListenerCog(bot))

