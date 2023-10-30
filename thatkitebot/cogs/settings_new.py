#  Copyright (c) 2019-2023 ThatRedKite and contributors

import enum
import re

import discord
from redis import asyncio as aioredis

from discord.ext import commands
from thatkitebot.tkb_redis.settings import RedisFlags
from thatkitebot.base.util import PermissonChecks as pc
from thatkitebot.base.util import set_up_guild_logger


class SettingsCogV2(commands.Cog, name="Settings"):
    def __init__(self, bot):
        self.bot: discord.Client = bot
        self.redis: aioredis.Redis = self.bot.redis

    settings = discord.SlashCommandGroup(
        "settings",
        "Bot Settings",
        checks=[pc.can_change_settings]
    )

    @settings.command(name="images")
    async def enable_images(self, ctx, enable: discord.Option(bool, name="enable", description="Whether to enable or disable the setting", required=True)):
        """
        Toggle image commands. Can be used by everyone with "manage_guild" permissions.
        """
        await ctx.defer()
        logger = set_up_guild_logger(ctx.guild.id)

        await RedisFlags.set_guild_flag(self.redis, ctx.guild.id, RedisFlags.IMAGE, value=enable)
        status = "enabled" if enable else "disabled"
        logger.info(f"IMAGES: User {ctx.author.name} {status} image processing in {ctx.guild.name}")
        await ctx.followup.send(f"Image processing features are now **{status}**")

    @settings.command(name="nsfw")
    async def enable_nsfw(self, ctx, enable: discord.Option(bool, name="enable", description="Whether to enable or disable the setting", required=True)):
        """
        Toggle NSFW commands. Can be used by everyone with "manage_guild" permissions.
        """
        await ctx.defer()
        logger = set_up_guild_logger(ctx.guild.id)

        await RedisFlags.set_guild_flag(self.redis, ctx.guild.id, RedisFlags.NSFW, value=enable)
        status = "enabled" if enable else "disabled"
        logger.info(f"NSFW: User {ctx.author.name} {status} NSFW commands in {ctx.guild.name}")
        await ctx.followup.send(f"NSFW features are now **{status}**. Remember that they will only work in NSFW-Channels")


    @settings.command(name="repost")
    async def enable_repost(self, ctx, enable: discord.Option(bool, name="enable", description="Whether to enable or disable the setting", required=True)):
        """
        Toggle Repost Commands. Can be used by everyone with "manage_guild" permissions.
        """
        await ctx.defer()
        logger = set_up_guild_logger(ctx.guild.id)

        await RedisFlags.set_guild_flag(self.redis, ctx.guild.id, RedisFlags.REPOST, value=enable)
        status = "enabled" if enable else "disabled"
        logger.info(f"REPOST: User {ctx.author.name} {status} repost-detection in {ctx.guild.name}")
        await ctx.followup.send(f"Repost detection is now **{status}**")


    @settings.command(name="uwu")
    async def enable_uwu(self, ctx, enable: discord.Option(bool, name="enable", description="Whether to enable or disable the setting", required=True)):
        """
        Toggle UwU Commands. Can be used by everyone with "manage_guild" permissions.
        """
        await ctx.defer()
        logger = set_up_guild_logger(ctx.guild.id)

        await RedisFlags.set_guild_flag(self.redis, ctx.guild.id, RedisFlags.UWU, value=enable)
        status = "enabled" if enable else "disabled"
        logger.info(f"UWU: User {ctx.author.name} {status} uwu in {ctx.guild.name}")
        await ctx.followup.send(f"UwU features are now **{status}**")

    @settings.command(name="detrack")
    async def enable_detrack(self, ctx, enable: discord.Option(bool, name="enable", description="Whether to enable or disable the setting", required=True)):
        """
        Toggle de-tracking commands. Can be used by everyone with "manage_guild" permissions.
        """
        await ctx.defer()
        logger = set_up_guild_logger(ctx.guild.id)

        await RedisFlags.set_guild_flag(self.redis, ctx.guild.id, RedisFlags.DETRACK, value=enable)
        status = "enabled" if enable else "disabled"
        logger.info(f"DETRACK: User {ctx.author.name} {status} detracking in {ctx.guild.name}")
        await ctx.followup.send(f"Detracking is now **{status}**")

    @settings.command(name="welcome_leaderboard")
    async def enable_welcome_leaderboard(self, ctx, enable: discord.Option(bool, name="enable", description="Whether to enable or disable the setting", required=True)):
        """
        Toggle the welcome leaderboard. Can be used by everyone with "manage_guild" permissions.
        """
        await ctx.defer()
        logger = set_up_guild_logger(ctx.guild.id)

        await RedisFlags.set_guild_flag(self.redis, ctx.guild.id, RedisFlags.WELCOME, value=enable)
        status = "enabled" if enable else "disabled"
        logger.info(f"WELCOME: User {ctx.author.name} {status} welcome-messages in {ctx.guild.name}")
        await ctx.followup.send(f"Welcome leaderboard is now **{status}**")

    @settings.command(name="welcome_message")
    async def enable_welcome_message(self, ctx, enable: discord.Option(bool, name="enable", description="Whether to enable or disable the setting", required=True)):
        """
        Toggle the welcome message. Can be used by everyone with "manage_guild" permissions.
        """
        await ctx.defer()
        logger = set_up_guild_logger(ctx.guild.id)

        await RedisFlags.set_guild_flag(self.redis, ctx.guild.id, RedisFlags.WELCOME_MESSAGE, value=enable)
        status = "enabled" if enable else "disabled"
        logger.info(f"WELCOME: User {ctx.author.name} {status} welcome-messages in {ctx.guild.name}")
        await ctx.followup.send(f"Welcome messages are now **{status}**")


    @settings.command(name="moderation")
    async def enable_moderation(self, ctx, enable: discord.Option(bool, name="enable", description="Whether to enable or disable the setting", required=True)):
        """
        Toggle all Moderation features. Can be used by everyone with "manage_guild" permissions.
        """
        await ctx.defer()
        logger = set_up_guild_logger(ctx.guild.id)

        await RedisFlags.set_guild_flag(self.redis, ctx.guild.id, RedisFlags.MODERATION, value=enable)
        status = "enabled" if enable else "disabled"
        logger.info(f"WELCOME: User {ctx.author.name} {status} welcome-messages in {ctx.guild.name}")
        await ctx.followup.send(f"Moderation features are now **{status}**")

    @settings.command(name="add_mod", description="Add a moderator role. Mod commands will be available to this role.")
    async def _add_mod(self, ctx: discord.ApplicationContext, role: discord.Role):
        """
        Allows mod perms to add a moderator role. Anyone with this role will be able to access mod features of the bot.
        """

        ctx.defer()
        logger = set_up_guild_logger(ctx.guild.id)
        key = f"mod_roles:{ctx.guild.id}"
        if not await self.redis.sismember(key, str(role.id)):
            await self.redis.sadd(key, role.id)
            await ctx.respond(f"{role.name} is now a moderator role")
            logger.info(f"MODERATION: User {ctx.author.name} set {role.name} as a moderation role in {ctx.guild.name}")
        else:
            try:
                await self.redis.srem(key, str(role.id))
            except aioredis.ResponseError:
                await ctx.respond(f"{role.name} is not a moderator role")
                return
            logger.info(f"MODERATION: User {ctx.author.name} removed {role.name} as a moderation role in {ctx.guild.name}")
            await ctx.respond(f"{role.name} is no longer a moderator role")


    @commands.is_owner()
    @commands.dm_only()
    @commands.command()
    async def convert_settings_global(self, ctx):
        """
        Convert from the old setting system to the new flag-based system. Mandatory when migrating to 4.0!
        """
        class Settings(enum.Enum):
            UWU = RedisFlags.UWU
            NSFW = RedisFlags.NSFW
            IMAGE = RedisFlags.IMAGE
            REPOST = RedisFlags.REPOST
            WELCOME = RedisFlags.WELCOME

        # set the defaults
        pipe = self.redis.pipeline()
        count = 0
        for guild in self.bot.guilds:
            try:
                print(f"Converting settings for guild \x1b[0;32m'{guild.name}' \x1b[0;33m({guild.id}) \x1b[0;37m")
                for key in await self.redis.hgetall(str(guild.id)):
                    setting = await self.redis.hget(str(guild.id), key)
                    bool_repr = setting == "TRUE" # turn the boolean string into an actual boolean
                    pos = Settings[key].value  # get the bitfield offset from the enum 

                    await RedisFlags.set_guild_flag(pipe, guild.id, pos, bool_repr)  # set the flag

                await pipe.delete(str(guild.id))  # delete the old settings, to free up some RAM
                self.logger.info(f"SETTINGS: Converted the settings for guild {guild.name} ({count}/{len(self.bot.guilds)})")
                count += 0
            except Exception:
                continue

        await pipe.execute()
        print("success!")
        await ctx.send(f"Successfully updated the config for {count} out of {len(self.bot.guilds)} guilds")
    

    @commands.is_owner()
    @commands.dm_only()
    @commands.command()
    async def settings_cleanup(self, ctx: commands.Context):
        old_setting = re.compile(r"^(\d+)$")
        pipe = self.redis.pipeline()

        guild_ids = [int(guild.id) for guild in self.bot.guilds]

        # clean up named settings
        async for key in self.redis.scan_iter("*:*"):
            try:
                id = int(key.split(":")[-1])
            except ValueError:
                id = int(key.split(":")[-2])
            finally:
                if id not in guild_ids:
                    # bot not member of the guild it has settings for
                    await pipe.delete(key)
                else:
                    continue
        
        # clean up old guild settings
        async for key in self.redis.scan_iter("*"):
            if id := old_setting.match(key):
                id = int(id[0])
                if id not in guild_ids:
                    await pipe.delete(key)
            else:
                continue     

        self.bot.logger.info(f"SETTINGS: Cleaned up {len(pipe.command_stack)} settings.")      
        await pipe.execute()
            


def setup(bot):
    bot.add_cog(SettingsCogV2(bot))
