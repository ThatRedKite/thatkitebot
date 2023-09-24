#  Copyright (c) 2019-2023 ThatRedKite and contributors

import enum

import discord
from redis import asyncio as aioredis

from discord.ext import commands
from thatkitebot.tkb_redis.settings import RedisFlags
from thatkitebot.base.util import PermissonChecks as pc


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
        await RedisFlags.set_guild_flag(self.redis, ctx.guild.id, RedisFlags.IMAGE, value=enable)

        if enable:
            await ctx.send(f"Image commands have been enabled")
        else:
            await ctx.send(f"Image commands have been disabled")

    @settings.command(name="nsfw")
    async def enable_nsfw(self, ctx, enable: discord.Option(bool, name="enable", description="Whether to enable or disable the setting", required=True)):
        """
        Toggle NSFW commands. Can be used by everyone with "manage_guild" permissions.
        """
        await RedisFlags.set_guild_flag(self.redis, ctx.guild.id, RedisFlags.NSFW, value=enable)

        if enable:
            await ctx.send(f"NSFW commands have been enabled")
        else:
            await ctx.send(f"NSFW commands have been disabled")

    @settings.command(name="repost")
    async def enable_repost(self, ctx, enable: discord.Option(bool, name="enable", description="Whether to enable or disable the setting", required=True)):
        """
        Toggle Repost Commands. Can be used by everyone with "manage_guild" permissions.
        """
        await RedisFlags.set_guild_flag(self.redis, ctx.guild.id, RedisFlags.REPOST, value=enable)

        if enable:
            await ctx.send(f"Repost commands have been enabled")
        else:
            await ctx.send(f"Repost commands have been disabled")

    @settings.command(name="music")
    async def enable_music(self, ctx, enable: discord.Option(bool, name="enable", description="Whether to enable or disable the setting", required=True)):
        """
        Toggle music commands in the current server, requires the `Manage Server` permission.
        (Warning: Music functionality is still highly experimental and the cog has to be manually loaded first)
        """
        await RedisFlags.set_guild_flag(self.redis, ctx.guild.id, RedisFlags.MUSIC, value=enable)

        if enable:
            embed = discord.Embed(title="Music commands are now enabled.", description="**WARNING: HIGHLY EXPERIMENTAL**")
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"Music commands have been disabled")

    @settings.command(name="uwu")
    async def enable_uwu(self, ctx, enable: discord.Option(bool, name="enable", description="Whether to enable or disable the setting", required=True)):
        """
        Toggle UwU Commands. Can be used by everyone with "manage_guild" permissions.
        """
        await RedisFlags.set_guild_flag(self.redis, ctx.guild.id, RedisFlags.UWU, value=enable)

        if enable:
            await ctx.send(f"UwU commands have been enabled")
        else:
            await ctx.send(f"UwU commands have been disabled")

    @settings.command(name="detrack")
    async def enable_detrack(self, ctx, enable: discord.Option(bool, name="enable", description="Whether to enable or disable the setting", required=True)):
        """
        Toggle de-tracking commands. Can be used by everyone with "manage_guild" permissions.
        """
        await RedisFlags.set_guild_flag(self.redis, ctx.guild.id, RedisFlags.DETRACK, value=enable)

        if enable:
            await ctx.send(f"UwU commands have been enabled")
        else:
            await ctx.send(f"UwU commands have been disabled")

    @settings.command(name="welcome_leaderboard")
    async def enable_welcome_leaderboard(self, ctx, enable: discord.Option(bool, name="enable", description="Whether to enable or disable the setting", required=True)):
        """
        Toggle the welcome leaderboard. Can be used by everyone with "manage_guild" permissions.
        """
        await RedisFlags.set_guild_flag(self.redis, ctx.guild.id, RedisFlags.WELCOME, value=enable)

        if enable:
            await ctx.send(f"Welcome leaderboard has been enabled")
        else:
            await ctx.send(f"Welcome leaderboard has been disabled")

    @settings.command(name="welcome_message")
    async def enable_welcome_message(self, ctx, enable: discord.Option(bool, name="enable", description="Whether to enable or disable the setting", required=True)):
        """
        Toggle the welcome message. Can be used by everyone with "manage_guild" permissions.
        """
        await RedisFlags.set_guild_flag(self.redis, ctx.guild.id, RedisFlags.WELCOME_MESSAGE, value=enable)

        if enable:
            await ctx.send(f"Welcome messages have been enabled")
        else:
            await ctx.send(f"Welcome messages have been disabled")

    @settings.command(name="moderation")
    async def enable_moderation(self, ctx, enable: discord.Option(bool, name="enable", description="Whether to enable or disable the setting", required=True)):
        """
        Toggle all Moderation features. Can be used by everyone with "manage_guild" permissions.
        """

        await RedisFlags.set_guild_flag(self.redis, ctx.guild.id, RedisFlags.MODERATION, value=enable)

        if enable:
            await ctx.send(f"Moderation features have been enabled")
        else:
            await ctx.send(f"Moderation features have been disabled")

    @settings.command(name="add_mod", description="Add a moderator role. Mod commands will be available to this role.")
    async def _add_mod(self, ctx: discord.ApplicationContext, role: discord.Role):
        """
        Allows mod perms to add a moderator role. Anyone with this role will be able to access mod features of the bot.
        """
        ctx.defer()
        key = f"mod_roles:{ctx.guild.id}"
        if not await self.redis.sismember(key, str(role.id)):
            await self.redis.sadd(key, role.id)
            await ctx.respond(f"{role.name} is now a moderator role")
        else:
            try:
                await self.redis.srem(key, str(role.id))
            except aioredis.ResponseError:
                await ctx.respond(f"{role.name} is not a moderator role")
                return
            await ctx.respond(f"{role.name} is no longer a moderator role")

    @commands.is_owner()
    @commands.dm_only()
    @commands.command()
    async def convert_settings_global(self, ctx):
        """
        Convert from the old setting system to the new flag-based system
        """
        class Settings(enum.Enum):
            UWU = RedisFlags.UWU
            NSFW = RedisFlags.NSFW
            IMAGE = RedisFlags.IMAGE
            REPOST = RedisFlags.REPOST
            WELCOME = RedisFlags.WELCOME

        # set the defaults
        pipe = self.redis.pipeline()
        for guild in self.bot.guilds:
            print(f"Converting settings for guild \x1b[0;32m'{guild.name}' \x1b[0;33m({guild.id}) \x1b[0;37m")
            for key in await self.redis.hgetall(str(guild.id)):
                setting = await self.redis.hget(str(guild.id), key)
                bool_repr = setting == "TRUE"
                pos = Settings[key].value
                await RedisFlags.set_guild_flag(pipe, ctx.guild.id, pos, bool_repr)
            print(await RedisFlags.get_guild_flags(self.redis, guild.id, *range(0, 7)))

        await pipe.execute()
        print("success!")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        # this initializes the settings for the guild the bot joins

        # check if the bot already has settings for this guild
        settings = [bool(setting) for setting in await RedisFlags.get_guild_flags(self.redis, guild.id, *range(0, 7))]
        if any(settings):
            return  # we seem to already have settings

        # enable image commands
        await RedisFlags.set_guild_flag(self.redis, guild.id, RedisFlags.IMAGE, True)


def setup(bot):
    bot.add_cog(SettingsCogV2(bot))
