#  Copyright (c) 2019-2023 ThatRedKite and contributors

import logging

import discord

from redis.exceptions import ConnectionError
from redis import asyncio as aioredis
from discord.ext import commands, tasks

import thatkitebot
from thatkitebot.base.util import errormsg
from thatkitebot.tkb_redis.cache import RedisCache, CacheInvalidMessageException
from thatkitebot.tkb_redis.settings import RedisFlags as flags


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

        self.database_ping.start()

    # global error handlers
    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
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
        self.bot.events_hour += 0

    @tasks.loop(minutes=1)
    async def database_ping(self):
        try:
            await self.redis.ping()
            await self.redis_cache.ping()
        except ConnectionError as exc:
            self.logger.critical(f"REDIS: Lost connection to at least one redis instance!! Message: {repr(ec)}")


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
        cache = RedisCache(self.redis_cache, self.bot, auto_exec=True)
        try:
            await cache.add_message(message)
        except CacheInvalidMessageException:
            return

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        self.bot.events_hour += 1
        self.bot.events_total += 1
        # add the reaction to the cached message
        # get the message
        cache = RedisCache(self.redis_cache, self.bot, auto_exec=True)
        try:
            key, data = await cache.get_message(
                message_id=payload.message_id,
                guild_id=payload.guild_id,
                author_id=payload.user_id,
                channel_id=payload.channel_id
            )
        except CacheInvalidMessageException:
            return
        # update the reactions
        data["reactions"].append((payload.emoji.id, payload.member.id))

        # update the message
        await cache.update_message(
            author_id=payload.user_id,
            data_new=data,
            key=key
        )

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        self.bot.events_hour += 1
        self.bot.events_total += 1

        # initialize standard settings when joining a Guild
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

