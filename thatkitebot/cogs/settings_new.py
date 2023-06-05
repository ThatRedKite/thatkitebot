import asyncio
from redis import asyncio as aioredis
import discord

from discord.ext import commands, bridge

import thatkitebot
from thatkitebot.base.util import PermissonChecks as pc
from thatkitebot.tkb_redis.settings import RedisFlags
from thatkitebot.base import util


class SettingsCogV2(commands.Cog, name="Settings"):
    def __init__(self, bot):
        print("ass")
        self.bot: discord.Client = bot
        self.redis: aioredis.Redis = self.bot.redis

    settings = discord.SlashCommandGroup("settings", "Bot Settings", default_member_permissions=discord.Permissions(manage_guild=True))

    @settings.command(name="images")
    @discord.default_permissions(manage_guild=True)
    async def enable_images(self, ctx: discord.ApplicationContext):
        """
        Toggle image commands. Can be used by everyone with "manage_guild" permissions.
        """
        result = await RedisFlags.toggle_guild_flag(self.redis, ctx.guild.id, RedisFlags.IMAGE)
        if result:
            await ctx.send(f"Image commands have been enabled")
        else:
            await ctx.send(f"Image commands have been disabled")

    @settings.command(name="nsfw")
    @discord.default_permissions(manage_guild=True)
    async def enable_nsfw(self, ctx):
        """
        Toggle NSFW commands. Can be used by everyone with "manage_guild" permissions.
        (NSFW Commands will still require an NSFW channel to work)
        """
        result = await RedisFlags.toggle_guild_flag(self.redis, ctx.guild.id, RedisFlags.NSFW)
        if result:
            await ctx.send(f"NSFW commands have been enabled")
        else:
            await ctx.send(f"NSFW commands have been disabled")

    @settings.command(name="repost")
    @discord.default_permissions(manage_guild=True)
    async def enable_repost(self, ctx):
        """
        Toggle Repost Commands. Can be used by everyone with "manage_guild" permissions.
        (NSFW Commands will still require an NSFW channel to work)
        """
        result = await RedisFlags.toggle_guild_flag(self.redis, ctx.guild.id, RedisFlags.REPOST)
        if result:
            await ctx.send(f"NSFW commands have been enabled")
        else:
            await ctx.send(f"NSFW commands have been disabled")

    @settings.command()
    @discord.default_permissions(manage_guild=True)
    async def enable_music(self, ctx):
        """
        Toggle music commands in the current server, requires the `Manage Server` permission.
        (Warning: Music functionality is still highly experimental)
        """
        result = await RedisFlags.toggle_guild_flag(self.redis, ctx.guild.id, RedisFlags.MUSIC)
        if result:
            embed = discord.Embed(title="Music commands are now enabled.", description="**WARNING: HIGHLY EXPERIMENTAL**")
            await ctx.send(embed)
        else:
            await ctx.send(f"NSFW commands have been disabled")

    @settings.command(name="uwu")
    @discord.default_permissions(manage_guild=True)
    async def enable_uwu(self, ctx):
        """
        Toggle UwU Commands. Can be used by everyone with "manage_guild" permissions.
        (NSFW Commands will still require an NSFW channel to work)
        """
        result = await RedisFlags.toggle_guild_flag(self.redis, ctx.guild.id, RedisFlags.UWU)
        if result:
            await ctx.send(f"UwU commands have been enabled")
        else:
            await ctx.send(f"UwU commands have been disabled")

    @settings.command(name="welcome_leaderboard")
    @discord.default_permissions(manage_guild=True)
    async def enable_welcome_leaderboard(self, ctx):
        """
        Toggle the welcome leaderboard. Can be used by everyone with "manage_guild" permissions.
        (NSFW Commands will still require an NSFW channel to work)
        """
        result = await RedisFlags.toggle_guild_flag(self.redis, ctx.guild.id, RedisFlags.WELCOME)
        if result:
            await ctx.send(f"Welcome leaderboard has been enabled")
        else:
            await ctx.send(f"Welcome leaderboard has been disabled")

    @settings.command(name="welcome_message")
    @discord.default_permissions(manage_guild=True)
    async def enable_welcome_leaderboard(self, ctx):
        """
        Toggle the welcome message. Can be used by everyone with "manage_guild" permissions.r
        (NSFW Commands will still require an NSFW channel to work)
        """
        result = await RedisFlags.toggle_guild_flag(self.redis, ctx.guild.id, RedisFlags.WELCOME_MESSAGE)
        if result:
            await ctx.send(f"Welcome messages have been enabled")
        else:
            await ctx.send(f"Welcome messages have been disabled")


def setup(bot):
    bot.add_cog(SettingsCogV2(bot))
