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
import os
import io
import logging

import discord
import aiofiles
from discord.ext import commands
from redis import asyncio as aioredis

from thatkitebot.base.util import PermissonChecks as pc
from thatkitebot.base.util import check_message_age, parse_timestring, set_up_guild_logger
from thatkitebot.embeds import moderation as mod_embeds
from thatkitebot.tkb_redis import settings
import thatkitebot.tkb_redis.util
from thatkitebot.types.message import Message
#endregion

class Offsets:
    EDIT_CHECKER = 0
    REMIX_DELETE = 1
    # more will follow

class Behavior:
    NOTHING = 0
    WARN = 1
    DELETE = 2
    WARN_AND_DELETE = 3

    DICT = {
        "Nothing": 0,
        "Warn": 1,
        "Delete": 2,
        "Warn & Delete": 3
    }
async def enable_check(ctx: discord.ApplicationContext) -> bool:
    redis = ctx.bot.redis
    is_enabled = await settings.RedisFlags.get_guild_flag(redis, ctx.guild, flag_offset=settings.RedisFlags.FlagEnum.MODERATION)
    return is_enabled

#region Cog
class ModerationCog(commands.Cog, name="Moderation Commands"):
    """
    This cog contains commands that are used to manage the bot. These commands are only available to the bot owner.
    """
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.redis: aioredis.Redis = bot.redis
        self.logger: logging.Logger = bot.logger
        self.edit_checker = self.EditChecker(bot, self.redis)
        self.remix_checker = self.RemixDelete(bot,self.redis)

    #region EditChecker class
    class EditChecker:
        def __init__(self, bot, redis: aioredis.Redis):
            self.bot = bot
            self.redis = redis

        async def _enabled_in_guild(self, guild_id: int) -> bool:
            return await settings.RedisFlags.get_guild_flag_custom(
                redis=self.redis,
                gid=guild_id,
                name="moderation",
                flag_offset=Offsets.EDIT_CHECKER,
            )
        
        async def get_guild_channel_blacklist(self, guild_id: discord):
            raise NotImplementedError
        
        async def is_channel_ignored(self, channel_id) -> bool:
            return await self.redis.sismember("edit_check_ignore_channels", str(channel_id))
        
        async def is_role_ignored(self, author: discord.Member):
            return any(await self.redis.smismember("edit_check_ignore_roles", [role.id for role in author.roles]))

        async def ignore_channel(self, channel_id) -> None:
            await self.redis.sadd("edit_check_ignore_channels", str(channel_id))

        async def unignore_channel(self, channel_id) -> None:
            await self.redis.srem("edit_check_ignore_channels", str(channel_id))
        
        async def ignore_role(self, role_id) -> None:
            await self.redis.sadd("edit_check_ignore_roles", str(role_id))

        async def unignore_role(self, role_id) -> None:
            await self.redis.srem("edit_check_ignore_roles", str(role_id))

        async def enable_in_guild(self, guild_id: int, enable: bool=True):
            await settings.RedisFlags.set_guild_flag_custom(self.redis, guild_id, "moderation", enable, Offsets.EDIT_CHECKER)

        async def process_payload(self, payload: discord.RawMessageUpdateEvent):
            if not payload.guild_id:
                return

            # check if the edit checker is disabled 
            if not await self._enabled_in_guild(payload.guild_id):
                return
            
            # check if the channel is in the ignore list
            if await self.redis.sismember("edit_check_ignore_channels", str(payload.channel_id)):
                return

            # check if the author has a role that permits all edits
            orig_channel = await self.bot.get_or_fetch_channel(payload.channel_id)
            message = await self.bot.get_or_fetch_message(payload.message_id, orig_channel.id)

            if await self.is_role_ignored(message.author):
                return

            # get the settings from the hash in order to figure out how to proceed from here
            check_settings = await self.redis.exists(f"edit_check:{payload.guild_id}")

            # make sure we have settings and then check message age
            if not check_settings or not check_message_age(payload.message_id, int(check_settings["age"])):
                return
            
            # message is too old, let's decide what to do with it
            match int(await self.redis.hget(f"edit_check:{payload.guild_id}", "behavior")):
                case Behavior.NOTHING:
                    return

                case Behavior.WARN:
                    # send warning message in warning channel
                    # get the warning channel
                    warn_channel = await self.bot.get_or_fetch_channel(int(await self.redis.hget(f"edit_check:{payload.guild_id}", "channel_id")))
                    warn_embed = mod_embeds.gen_edit_warning(payload)

                    await warn_channel.send(embed=warn_embed)
                    return

                case Behavior.DELETE:
                    # get the message from the API
                    try:
                        await message.delete(reason="Automatic removal of old messages suddenly edited.")
                        logger = set_up_guild_logger(payload.guild_id)
                        logger.info(f"MODERATION: Message {message.id} by {message.author} deleted by edit-checker.")
                        return
                    
                    except Exception:
                        logger = set_up_guild_logger(payload.guild_id)
                        logger.warning(f"MODERATION: Edit-checker failed to delete {message.id} by {message.author}")
                        return

                case Behavior.WARN_AND_DELETE:
                    # generate the warning embed
                    warn_channel = self.bot.get_or_fetch_channel(int(await self.redis.hget(f"edit_check:{payload.guild_id}", "channel_id")))
                    warn_embed = mod_embeds.gen_edit_warning(payload)
                    warn_embed.title = f"Deleted old edited message by {message.author.name}#{message.author.discriminator}"

                    try:
                        await message.delete(reason="Automatic removal of old messages suddenly edited.")
                        self.logger.info(f"MODERATION: Message {message.id} by {message.author} deleted by edit-checker.")

                    except discord.Forbidden:
                        await warn_channel.send("Failed to to delete due to insufficient permissions:", embed=warn_embed)
                        self.logger.warning(f"MODERATION: Edit-checker failed to delete {message.id} by {message.author}")
                        return
            
                    await warn_channel.send(embed=warn_embed)
            
    #endregion
        
    class RemixDelete:
        def __init__(self, bot, redis: aioredis.Redis):
            self.bot = bot
            self.redis = redis

        async def _enabled_in_guild(self, guild_id: int) -> bool:
            return await settings.RedisFlags.get_guild_flag_custom(self.redis, guild_id, "moderation", Offsets.REMIX_DELETE)
        
        async def enable_in_guild(self, guild_id: int, enable: bool=True):
            await settings.RedisFlags.set_guild_flag_custom(self.redis, guild_id, "moderation", enable, Offsets.REMIX_DELETE)

        async def process_message(self, message: Message):
            if message.is_remix and await self._enabled_in_guild(message.guild.id):
                await message.delete()

    #region Command groups
    edit_checker = discord.SlashCommandGroup(
        "edit_checker",
        "Edit Checking Commands",
        checks=[pc.mods_can_change_settings, enable_check, pc.in_guild],
        guild_ids=[759419755253465188]
    )

    remix_delete = discord.SlashCommandGroup(
        "remix_delete",
        "Edit Checking Commands",
        checks=[pc.mods_can_change_settings, enable_check, pc.in_guild],
        guild_ids=[759419755253465188]
    )

    moderation = discord.SlashCommandGroup(
        "moderation",
        "General Moderation Commands",
        checks=[pc.mods_can_change_settings, enable_check, pc.in_guild]
    )
    #endregion

    #region general commands
    @moderation.command(name="send_logs", description="Sends the logs for this guild. Use with care.")
    async def send_logs(self, ctx: discord.ApplicationContext) -> None:
        await ctx.defer()
        log_path = os.path.join("/var/log/thatkitebot/", f"{ctx.guild.id}.log")
        if not os.path.exists(log_path):
            await ctx.followup.send("No logs found.")
            return
        
        async with aiofiles.open(log_path, "rb") as log:
            file = discord.File(fp=io.BytesIO(await log.read()), filename=f"{ctx.guild.id}.txt")
            await ctx.followup.send(file=file)
    #endregion

    #region edit checker
    @edit_checker.command(name="enable", description="Enable or change settings for checking for old edits")
    async def edit_checker_enable(
            self,
            ctx: discord.ApplicationContext,
            check_time: discord.Option(
                str,
                description="Maximum age of messages that can be edited. Format like `1y 2w 3d 4h 5m 6s`",
                required=True
            ),#type:ignore

            behavior: discord.Option(
                str,
                description="If the selected option sends a warning, warn_channel is a required parameter.",
                choices=["Nothing", "Warn", "Delete", "Warn & Delete"],
                required=True
            ),#type:ignore

            warn_channel: discord.Option(
                discord.TextChannel,
                description="Channel to send a warning in. Required if selected behavior sends a warning.",
                required=False
            )#type:ignore

    ) -> None:
        behavior_int = 0
        time_diff = 0

        await ctx.defer()

        if not ctx.guild:
            await ctx.followup.send("Error! This command can only used in guilds. DMs won't work.")
            return

        # turn the behavior strings into ints for safekeeping and ensure user passed the correct parameters

        behavior_int = Behavior.DICT.get(behavior, 0)

        if behavior_int == Behavior.WARN or Behavior.WARN_AND_DELETE and not warn_channel:
            await ctx.followup.send("Error! You need to specify a warning channel!")
            return

        if (time_diff := parse_timestring(check_time)) <= 0:
            await ctx.followup.send("Please specify a valid time! Make sure you format it like that: `31d 5h`")
            return

        await self.set_embed_checker(ctx, behavior, warn_channel, behavior_int, time_diff)

        await ctx.followup.send("Edit checking has been enabled!")

    async def set_embed_checker(self, ctx, behavior, warn_channel, behavior_int, time_diff):
        pipe = self.redis.pipeline()
        await settings.RedisFlags.set_guild_flag_custom(
            redis=pipe,
            gid=ctx.guild.id,
            name="moderation",
            flag_offset=Offsets.EDIT_CHECKER,
            value=True,
        )

        logger = set_up_guild_logger(ctx.guild.id)
        logger.info(f"MODERATION: User {ctx.author.name} enabled edit-checking with behavior {behavior} in {ctx.guild.name}")

        mapping = {
            "age": time_diff,
            "behavior": behavior_int,
            "channel_id": int(warn_channel.id) 
        }
        await pipe.hset(f"edit_check:{ctx.guild.id}", mapping=mapping)
        await pipe.execute()
        
    @edit_checker.command(name="change_time", description="Change minimum age of messages that will be deleted.")
    async def _change_time(
            self,
            ctx: discord.ApplicationContext,
            check_time: discord.Option(
                str,
                "Maximum age of messages that can be edited. Format like `1y 2w 3d 4h 5m 6s`",
                required=True
            )#type:ignore
    ) -> None:
        
        time_diff = 0

        await ctx.defer()
        if not ctx.guild:
            await ctx.followup.send("Error! This command can only used in guilds. DMs won't work.")
            return

        time_diff = parse_timestring(check_time)

        if time_diff <= 0:
            await ctx.followup.send("Please specify a valid time! Make sure you format it like that: `31d 5h`")
            return

        key = f"edit_check:{ctx.guild.id}"

        if not await self.redis.exists(key):
            await ctx.followup.send("Error! Edit checking does not seem to be enabled. Please run /edit_checker enable.")
            return
        
        logger = set_up_guild_logger(ctx.guild.id)
        logger.info(f"MODERATION: User {ctx.author.name} changed edit-check age to {check_time} in {ctx.guild.name}")
        await self.redis.hset(key, "age", time_diff)
        await ctx.followup.send("Successfully changed the check time.")

    @edit_checker.command(name="disable", description="Disables edit checking.")
    async def _disable(self, ctx: discord.ApplicationContext) -> None:
        await ctx.defer()
        if not ctx.guild:
            await ctx.followup.send("Error! This command can only used in guilds. DMs won't work.")
            return

        await settings.RedisFlags.set_guild_flag_custom(
            redis=self.redis,
            gid=ctx.guild.id,
            name="moderation",
            flag_offset=Offsets.EDIT_CHECKER,
            value=False,
        )

        logger = set_up_guild_logger(ctx.guild.id)
        logger.info(f"MODERATION: User {ctx.author.name} disabled edit-checking in {ctx.guild.name}")
        await ctx.followup.send("Successfully disabled edit checking.")
    #endregion

    #region Ignore Commands
    
    #
    # --- Channel Ignore Commands ---
    #

    @edit_checker.command(name="ignore_channel", description="Add channel to a list of channels in which edits will be ignored (e.g. rule channels)")
    async def _ignore_channel(
            self,
            ctx: discord.ApplicationContext,
            channel: discord.Option(discord.TextChannel, required=True, description="The channel to ignore")#type:ignore
    ) -> None:
        await ctx.defer()
        logger = set_up_guild_logger(ctx.guild.id)
        logger.info(f"MODERATION: User {ctx.author.name} added {channel.name} to ignorelist in {ctx.guild.name}")
        await self.edit_checker.ignore_channel(channel.id)
        await ctx.followup.send(f"Successfully added <#{channel.id}> to the ignore list.")

    @edit_checker.command(name="unignore_channel", description="Remove channel from the list of channels in which edits will be ignored.")
    async def _unignore_channel(
            self,
            ctx: discord.ApplicationContext,
            channel: discord.Option(discord.TextChannel, required=True, description="The channel to un-ignore")#type:ignore
    ) -> None:
        await ctx.defer()
        logger = set_up_guild_logger(ctx.guild.id)
        logger.info(f"MODERATION: User {ctx.author.name} removed {channel.name} from ignorelist in {ctx.guild.name}")
        await self.edit_checker.unignore_channel(channel.id)
        await ctx.followup.send(f"Successfully removed <#{channel.id}> from the ignore list.")

    #
    #  --- Role Ignore Commands
    #

    @edit_checker.command(name="ignore_role", description="Add role to a list of roles whose will be ignored (e.g. Moderators)")
    async def _ignore_role(
            self,
            ctx: discord.ApplicationContext,
            role: discord.Option(discord.Role, required=True, description="The role to ignore")#type:ignore
    ) -> None:
        
        await ctx.defer()
        logger = set_up_guild_logger(ctx.guild.id)
        logger.info(f"MODERATION: User {ctx.author.name} added role {role.name} to ignorelist in {ctx.guild.name}")
        await self.redis.sadd(f"edit_check_ignore_roles", role.id)
        await ctx.followup.send(f"Successfully added {role.name} to the ignore list.")

    @edit_checker.command(name="unignore_role", description="Remove a role from the list of roles whose edits will be ignored.")
    async def _unignore_role(
            self,
            ctx: discord.ApplicationContext,
            role: discord.Option(discord.Role, required=True, description="The role to un-ignore")#type:ignore
    ) -> None:
        
        await ctx.defer()
        logger = set_up_guild_logger(ctx.guild.id)
        logger.info(f"MODERATION: User {ctx.author.name} removed role {role.name} from ignorelist in {ctx.guild.name}")
        await self.redis.srem("edit_check_ignore_roles", role.id)
        await ctx.followup.send(f"Successfully removed {role.name} from the ignore list.")
    #endregion

    @remix_delete.command(name="toggle", description="Toggles the automatic deletion of remixes")
    async def _toggle_remix_delete(self, ctx: discord.ApplicationContext, enable: discord.Option(bool, required=True)): #type: ignore
        await ctx.defer()

        await self.remix_checker.enable_in_guild(ctx.guild.id, enable=enable)
        
        logger = set_up_guild_logger(ctx.guild.id)
        logger.info(f"MODERATION: User {ctx.author.name} toggled remix deletion {ctx.guild.name}")

        await ctx.followup.send("Toggled remix autodelete")


    #region listeners
    #
    #  --- Main Listener Functions ---
    #
    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent) -> None:
        self.bot.events_hour += 1
        self.bot.events_total += 1
        # check if edit checking is enabled
        await self.edit_checker.process_payload(payload)
        # ignore DMs

    @commands.Cog.listener()
    async def on_message(self, message) -> None:
        self.bot.events_hour += 1
        self.bot.events_total += 1
        # check if edit checking is enabled
        await self.remix_checker.process_message(message)
        # ignore DMs

    #endregion

def setup(bot) -> None:
    bot.add_cog(ModerationCog(bot))
