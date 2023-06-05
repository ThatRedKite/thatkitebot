#  Copyright (c) 2019-2022 ThatRedKite and contributors

import enum

import asyncio
import discord

from redis import asyncio as aioredis
from discord.ext import commands, bridge

from thatkitebot.base.util import PermissonChecks as pc
from thatkitebot.base.util import Parsing

from thatkitebot.tkb_redis.settings import RedisFlags


# TODO: make this not suck ass

class SettingsCog(commands.Cog, name="legacy settings"):
    """
    Settings Cog. Allows the bot owner or admins to change settings for their server. All settings are stored in Redis
    and only apply to the server the command was used in. Global settings are not a thing (yet).
    """
    def __init__(self, bot):
        self.bot: discord.Client = bot
        self.redis: aioredis.Redis = self.bot.redis
        self.possible_settings = ["NSFW", "IMAGE", "REPOST", "WELCOME", "UWU"]

    @commands.group(name="setting", aliases=["settings", "set"], hidden=True)
    @commands.check(pc.can_change_settings)
    async def settings(self, ctx):
        """
        This is a command group used to change some bot settings.
        You have to be an Administrator or the bot owner to change use this command group.
        You should use one of the following subcommands: add, list, help.
        """
        if not ctx.subcommand_passed:
            await self._help(ctx)

    @settings.command(name="add", aliases=["update"], hidden=True)
    @commands.cooldown(3, 10, commands.BucketType.user)
    async def _add(self, ctx: commands.Context, name: str, arg):
        """
        This command changes the value of a setting.
        """
        channel = ctx.channel
        author = ctx.message.author
        yes_choices = ["y", "yes", "ja", "j"]

        def check(m):
            if m.channel == channel and m.author is author:
                return m.content.lower() in yes_choices

        if not Parsing.preprocessor(name) in self.possible_settings:
            await util.errormsg(
                ctx,
                f"This seems to be an invalid setting! Execute {ctx.prefix}settings help to see all availible settings")
            return
        await ctx.send(f"Add the setting `{Parsing.preprocessor(name)}` with the value `{preprocessor(arg)}` to the settings? (y/n)")
        msg = await self.bot.wait_for("message", timeout=10, check=check)
        if msg.content in yes_choices:
            await self.redis.hset(ctx.guild.id, preprocessor(name), preprocessor(arg))
            await ctx.send("Okay, done.", delete_after=5.0)
        else:
            await ctx.send("Cancelled.", delete_after=5.0)

    #@settings.command(name="add_mod", hidden=True)
    @bridge.bridge_command(name="add_mod", description="Add a moderator role. Mod commands will be available to this role.")
    async def _add_mod(self, ctx: commands.Context, role: discord.Role):
        """
        Allows mod perms to add a moderator role. Anyone with this role will be able to access mod features of KiteBot. 
        """
        if not ctx.channel.permissions_for(ctx.author).administrator:
            await ctx.respond("You do not have permission to do this.")
            return
        
        key = f"mod_roles:{ctx.guild.id}"   # I wanted to call them snowflakes :troll: but that would result in bad readability
        if not await self.redis.sismember(key, role.id):
            await self.redis.sadd(key, role.id)
            await ctx.respond(f"{role.name} is now a moderator role")
        else:
            try:
                await self.redis.srem(key, role.id)
            except aioredis.ResponseError:
                await ctx.respond(f"{role.name} is not a moderator role")
                return
            await ctx.respond(f"{role.name} is no longer a moderator role")

    @settings.command(name="list", aliases=["ls"])
    async def _list(self, ctx):
        """
        Lists all the settings for the current guild.
        """
        settings = await self.redis.hgetall(ctx.guild.id)
        embed = discord.Embed(title=f"settings for **guild {str(ctx.guild)}**")
        for setting in settings:
            embed.add_field(name=setting, value=settings.get(setting))
        await ctx.send(embed=embed, delete_after=10.0)

    @settings.command(name="help")
    async def _help(self, ctx):
        """
        This command lists all availible settings and their possible values.
        """
        e = discord.Embed(title="Possible bot settings")
        e.add_field(
            name="NSFW",
            value="""
            Enable or disable NSFW commands for the server (does not affect blacklisted servers)\n
            Possible values: `TRUE`, `FALSE`\n
            Standard value: `FALSE`
            """
        )
        e.add_field(
            name="IMAGE",
            value="""
             Enable or disable image manipulation commands for the server.\n
             Possible values: `TRUE`, `FALSE`\n
             Standard value: `TRUE`
             """
        )
        e.add_field(
            name="REPOST",
            value="""
             Enable or disable repost detection for the server.\n
             Possible values: `TRUE`, `FALSE`\n
             Standard value: `TRUE`
             """
        )
        e.add_field(
            name="WELCOME",
            value="""
             Enable or disable welcome leaderboards for the server.\n
             Possible values: `TRUE`, `FALSE`\n
             Standard value: `TRUE`
             """
        )
        e.add_field(
            name="UWU",
            value="""
            Enable or disable the uwuify function for the server.\n
            Possible values: `TRUE`, `FALSE`\n
            Standard value: `TRUE`
            """
        )
        await ctx.send(embed=e, delete_after=10)
        await asyncio.sleep(10)
        await ctx.message.delete()

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        # this initializes the settings for the guild the bot joins
        init_dict = {
            "NSFW": "FALSE",
            "IMAGE": "TRUE",
            "REPOST": "FALSE",
            "WELCOME": "FALSE",
            "UWU": "TRUE"
        }
        # check if there already are settings for the guild present
        if not await self.redis.hexists(guild.id, "IMAGE"):
            # set the settings that were defined in init_dict
            await self.redis.hmset(guild.id, init_dict)

    @commands.is_owner()
    @commands.command()
    async def convert_settings(self, ctx):
        """
        convert from the old setting system to the new flag-based system
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
            for key in await self.redis.hgetall(guild.id):
                setting = await self.redis.hget(guild.id, key)
                bool_repr = setting == "TRUE"
                pos = Settings[key].value
                await RedisFlags.set_guild_flag(pipe, ctx.guild.id, pos, bool_repr)
            print(await RedisFlags.get_guild_flags(self.redis, guild.id, *range(0, 7)))

        await pipe.execute()
        print("success!")


def setup(bot):
    bot.add_cog(SettingsCog(bot))
