#  Copyright (c) 2019-2024 ThatRedKite and contributors

import enum
import re

from asyncio import sleep

import discord
from redis import asyncio as aioredis

from discord.ext import commands
from thatkitebot.tkb_redis.settings import RedisFlags
from thatkitebot.base.util import PermissonChecks as pc
from thatkitebot.base.util import EmbedColors as ec
from thatkitebot.base.util import set_up_guild_logger

OLD_SETTING = re.compile(r"^(\d+)$")

class SettingsCogV2(commands.Cog, name="Settings"):
    def __init__(self, bot):
        self.bot: discord.Client = bot
        self.redis: aioredis.Redis = self.bot.redis

    settings = discord.SlashCommandGroup(
        "settings",
        "Bot Settings",
        checks=[pc.can_change_settings]
    )

    async def gen_settings_embed(self, ctx: discord.ApplicationContext, name: str, enable: bool, flag_id: int, further_config=False) -> discord.Embed:
        # set up the logging by getting the correct logger for the guild
        logger = set_up_guild_logger(ctx.guild.id)

        # make sure that the flag_id is valid
        assert flag_id in [flag.value for flag in RedisFlags.FlagEnum]

        # set the corresponding value
        await RedisFlags.set_guild_flag(self.redis, ctx.guild, flag_id, value=enable)

        # turn the bool into a string
        status = "Enabled" if enable else "Disabled"

        # log it to the server log
        logger.info(f"{RedisFlags.FlagEnum(flag_id).name}: User {ctx.author.name} {status} {name} in {ctx.guild.name}")

        embed = discord.Embed(title="Success!", description=f"**{status}** {name}", color=ec.lime_green)

        # if requested, add the 
        if further_config:
            embed.set_footer(text="Note: This only enables the commands, further configuration will be required!")

        return embed
    

    @settings.command(name="images")
    async def enable_images(self, ctx, enable: discord.Option(bool, name="enable", description="Whether to enable or disable the setting", required=True)):#type:ignore
        """
        Toggle image commands. Can be used by everyone with "manage_guild" permissions.
        """
        # defer, so that it looks like we are doing something really cool and to make sure we can send a followup later
        await ctx.defer()
        # set the settings, log everything and generate an embed
        await ctx.respond(embed=await self.gen_settings_embed(ctx, "Image Commands", enable, RedisFlags.FlagEnum.IMAGE.value))


    @settings.command(name="nsfw")
    async def enable_nsfw(self, ctx, enable: discord.Option(bool, name="enable", description="Whether to enable or disable the setting", required=True)):#type:ignore
        """
        Toggle NSFW commands. Can be used by everyone with "manage_guild" permissions.
        """
        # defer, so that it looks like we are doing something really cool and to make sure we can send a followup later
        await ctx.defer()
        # set the settings, log everything and generate an embed
        await ctx.respond(embed=await self.gen_settings_embed(ctx, "NSFW Commands", enable, RedisFlags.FlagEnum.NSFW.value))


    @settings.command(name="repost")
    async def enable_repost(self, ctx: discord.ApplicationContext, enable: discord.Option(bool, name="enable", description="Whether to enable or disable the setting", required=True)):#type:ignore
        """
        Toggle Repost Commands. Can be used by everyone with "manage_guild" permissions.
        """
        # defer, so that it looks like we are doing something really cool and to make sure we can send a followup later
        await ctx.defer()
        # set the settings, log everything and generate an embed
        await ctx.respond(embed=await self.gen_settings_embed(ctx, "Repost-Detection", enable, RedisFlags.FlagEnum.REPOST.value, further_config=True))


    @settings.command(name="uwu")
    async def enable_uwu(self, ctx, enable: discord.Option(bool, name="enable", description="Whether to enable or disable the setting", required=True)):#type:ignore
        """
        Toggle UwU Commands. Can be used by everyone with "manage_guild" permissions.
        """
        # defer, so that it looks like we are doing something really cool and to make sure we can send a followup later
        await ctx.defer()
        # set the settings, log everything and generate an embed
        await ctx.respond(embed=await self.gen_settings_embed(ctx, "UwUification Commands", enable, RedisFlags.FlagEnum.UWU.value, further_config=True))


    @settings.command(name="detrack")
    async def enable_detrack(self, ctx: discord.ApplicationContext, enable: discord.Option(bool, name="enable", description="Whether to enable or disable the setting", required=True)):#type:ignore
        """
        Toggle de-tracking commands. Can be used by everyone with "manage_guild" permissions.
        """
        await ctx.defer()
        # set the settings, log everything and generate an embed
        await ctx.respond(embed=await self.gen_settings_embed(ctx, "Detracking", enable, RedisFlags.FlagEnum.DETRACK.value))


    @settings.command(name="welcome_leaderboard")
    async def enable_welcome_leaderboard(self, ctx, enable: discord.Option(bool, name="enable", description="Whether to enable or disable the setting", required=True)):#type:ignore
        """
        Toggle the welcome leaderboard. Can be used by everyone with "manage_guild" permissions.
        """
        # defer, so that it looks like we are doing something really cool and to make sure we can send a followup later
        await ctx.defer()
        # set the settings, log everything and generate an embed
        await ctx.respond(embed=await self.gen_settings_embed(ctx, "the Welcome-Leaderboard", enable, RedisFlags.FlagEnum.WELCOME.value))


    @settings.command(name="welcome_message")
    async def enable_welcome_message(self, ctx, enable: discord.Option(bool, name="enable", description="Whether to enable or disable the setting", required=True)):#type:ignore
        """
        Toggle the welcome message. Can be used by everyone with "manage_guild" permissions.
        """
        # defer, so that it looks like we are doing something really cool and to make sure we can send a followup later
        await ctx.defer()
        # set the settings, log everything and generate an embed
        await ctx.respond(embed=await self.gen_settings_embed(ctx, "welcome messages", enable, RedisFlags.FlagEnum.WELCOME_MESSAGE.value))


    @settings.command(name="moderation")
    async def enable_moderation(self, ctx, enable: discord.Option(bool, name="enable", description="Whether to enable or disable the setting", required=True)):#type:ignore
        """
        Toggle all Moderation features. Can be used by everyone with "manage_guild" permissions.
        """
        # defer, so that it looks like we are doing something really cool and to make sure we can send a followup later
        await ctx.defer()
        # set the settings, log everything and generate an embed
        await ctx.respond(embed=await self.gen_settings_embed(ctx, "Moderation Features", enable, RedisFlags.FlagEnum.MODERATION.value, further_config=True))


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
            if id := OLD_SETTING.match(key):
                id = int(id[0])
                if id not in guild_ids:
                    await pipe.delete(key)
            else:
                continue     

        self.bot.logger.info(f"SETTINGS: Cleaned up {len(pipe.command_stack)} settings.")      
        await pipe.execute()
            


def setup(bot):
    bot.add_cog(SettingsCogV2(bot))
