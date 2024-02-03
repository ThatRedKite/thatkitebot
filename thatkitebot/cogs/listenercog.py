#  Copyright (c) 2019-2023 ThatRedKite and contributors

import logging

import discord

from redis.exceptions import ConnectionError
from redis import asyncio as aioredis
from discord.ext import commands, tasks

import thatkitebot
from thatkitebot.base.util import errormsg
from thatkitebot.tkb_redis.cache import RedisCache, CacheInvalidMessageException, NoDataException
from thatkitebot.tkb_redis.settings import RedisFlags as flags
from thatkitebot.base.exceptions import *


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
        self.cache: RedisCache = bot.r_cache

        self.database_ping.start()
        self.cache_update.start()

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
    async def hourly_reset(self):
        self.bot.command_invokes_hour = 0
        self.bot.events_hour = 0

    @tasks.loop(minutes=1)
    async def database_ping(self):
        try:
            await self.redis.ping()
            await self.redis_cache.ping()
        except ConnectionError as exc:
            self.logger.critical(f"REDIS: Lost connection to at least one redis instance!! Message: {repr(exc)}")

    @tasks.loop(seconds=10)
    async def cache_update(self):
        if len(self.cache.pipeline.command_stack) > 0:
            await self.cache.exec()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"\n{self.bot.user.name} is up and ready.")

        print("Starting task loops…\n")
        self.hourly_reset.start()

        await self.bot.change_presence(
            activity=discord.Activity(name="a battle against russia", type=5),
            status=discord.Status.online,
        )

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        self.bot.command_invokes_hour += 1
        self.bot.command_invokes_total += 1
        self.bot.events_hour += 1
        self.bot.events_total += 1

    @commands.Cog.listener()
    async def on_slash_command_error(self, ctx, ex):
        raise ex

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        self.bot.events_hour += 1
        self.bot.events_total += 1
        if not message.guild:
            return

        try:
            await self.cache.add_message(message)
            
        except CacheInvalidMessageException:
            if self.bot.debug_mode:
                self.logger.debug("CACHE: Could not add message to cache, reason: Invalid Message")

        except NoDataException:
            if self.bot.debug_mode:
                self.logger.debug("CACHE: Could not add message to cache, reason: No Data")


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        self.bot.events_hour += 1
        self.bot.events_total += 1

        try:
            key, data = await self.cache.get_message(
                message_id=payload.message_id,
                guild_id=payload.guild_id,
                author_id=payload.user_id,
                channel_id=payload.channel_id
            )
        except CacheInvalidMessageException:
            return
        
        except NoDataException:
            self.logger.error(f"Failed to add message {payload.message_id} to cache")
        
        # update the reactions
        data["reactions"].append((payload.emoji.id, payload.member.id))

        # update the message
        await self.cache.update_message(
            author_id=payload.user_id,
            data_new=data,
            key=key
        )
    
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        self.bot.events_hour += 1
        self.bot.events_total += 1

        self.logger.info(f"Joined guild {guild.name} with {guild.member_count} users.")

        if not await self.redis.exists(f"flags:{guild.id}"):
            # initialize standard settings when joining a Guild if they don't exist
            pipe = self.redis.pipeline()
            await flags.set_guild_flag(pipe, guild.id, flags.IMAGE, True)
            await flags.set_guild_flag(pipe, guild.id, flags.CACHING, True)
            await flags.set_guild_flag(pipe, guild.id, flags.UWU, True)

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


def setup(bot):
    bot.add_cog(ListenerCog(bot))

