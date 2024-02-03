
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


class Offsets:
    EDIT_CHECKER = 0
    # more will follow


async def enable_check(ctx: discord.ApplicationContext):
    redis = ctx.bot.redis
    is_enabled = await settings.RedisFlags.get_guild_flag(redis, ctx.guild, flag_offset=settings.RedisFlags.FlagEnum.MODERATION.value)
    return is_enabled


class ModerationCommands(commands.Cog, name="Moderation Commands"):
    """
    This cog contains commands that are used to manage the bot. These commands are only available to the bot owner.
    """
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.redis: aioredis.Redis = bot.redis
        self.logger: logging.Logger = bot.logger

    edit_checker = discord.SlashCommandGroup(
        "edit_checker",
        "Edit Checking Commands",
        checks=[pc.mods_can_change_settings, enable_check]
    )

    moderation = discord.SlashCommandGroup(
        "moderation",
        "General Moderation Commands",
        checks=[pc.mods_can_change_settings, enable_check]
    )

    @moderation.command(name="send_logs", description="Sends the logs for this guild. Use with care.")
    async def send_logs(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        log_path = os.path.join("/var/log/thatkitebot/", f"{ctx.guild.id}.log")
        if not os.path.exists(log_path):
            await ctx.followup.send("No logs found.")
            return
        
        async with aiofiles.open(log_path, "rb") as log:
            file = discord.File(fp=io.BytesIO(await log.read()), filename=f"{ctx.guild.id}.txt")
            await ctx.followup.send(file=file)


    #
    # --- General Settings Commands ---
    #


    @edit_checker.command(name="enable", description="Enable or change settings for checking for old edits")
    async def edit_checker_enable(
            self,
            ctx: discord.ApplicationContext,
            check_time: discord.Option(
                str,
                description="Maximum age of messages that can be edited. Format like `1y 2w 3d 4h 5m 6s`",
                required=True
            ),

            behavior: discord.Option(
                str,
                description="If the selected option sends a warning, warn_channel is a required parameter.",
                choices=["Nothing", "Warn", "Delete", "Warn & Delete"],
                required=True
            ),

            warn_channel: discord.Option(
                discord.TextChannel,
                description="Channel to send a warning in. Required if selected behavior sends a warning.",
                required=False
            )

    ):
        behavior_int = 0
        time_diff = 0
        warn_channel_id = 0

        await ctx.defer()

        if not ctx.guild:
            await ctx.followup.send("Error! This command can only used in guilds. DMs won't work.")
            return

        # turn the behavior strings into ints for safekeeping and ensure user passed the correct parameters
        match behavior:
            case "Nothing":
                behavior_int = 0
            case "Warn":
                behavior_int = 1
                if not warn_channel:
                    await ctx.followup.send("Error! You need to specify a warning channel!")
                    return
            case "Delete":
                behavior_int = 2
            case "Warn & Delete":
                behavior_int = 3
                if not warn_channel:
                    await ctx.followup.send("Error! You need to specify a warning channel!")
                    return
            case _:
                self.logger.error("Somehow, no behavior was selected. This should not happen.")

        time_diff = parse_timestring(check_time)

        if time_diff <= 0:
            await ctx.followup.send("Please specify a valid time! Make sure you format it like that: `31d 5h`")
            return

        pipe = self.redis.pipeline()
        await settings.RedisFlags.set_guild_flag_custom(
            redis=pipe,
            gid=ctx.guild.id,
            name="moderation",
            flag_offset=Offsets.EDIT_CHECKER,
            value=True,
        )

        warn_channel_id = warn_channel.id

        key = f"edit_check:{ctx.guild.id}"
        mapping = {
            "age": time_diff,
            "behavior": behavior_int,
            "channel_id": warn_channel_id
        }

        logger = set_up_guild_logger(ctx.guild.id)
        logger.info(f"MODERATION: User {ctx.author.name} enabled edit-checking with behavior {behavior} in {ctx.guild.name}")

        await pipe.hset(key, mapping=mapping)
        await ctx.followup.send("Edit checking has been enabled!")
        await pipe.execute()


    @edit_checker.command(name="change_time", description="Change minimum age of messages that will be deleted.")
    async def _change_time(
            self,
            ctx: discord.ApplicationContext,
            check_time: discord.Option(
                str,
                "Maximum age of messages that can be edited. Format like `1y 2w 3d 4h 5m 6s`",
                required=True
            )
    ):
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
    async def _disable(self, ctx: discord.ApplicationContext):
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

    #
    # --- Channel Ignore Commands ---
    #

    @edit_checker.command(name="ignore_channel", description="Add channel to a list of channels in which edits will be ignored (e.g. rule channels)")
    async def _ignore_channel(
            self,
            ctx: discord.ApplicationContext,
            channel: discord.Option(discord.TextChannel, required=True, description="The channel to ignore")
    ):
        await ctx.defer()
        if not ctx.guild:
            await ctx.followup.send("Error! This command can only used in guilds. DMs won't work.")
            return
        
        logger = set_up_guild_logger(ctx.guild.id)
        logger.info(f"MODERATION: User {ctx.author.name} added {channel.name} to ignorelist in {ctx.guild.name}")
        await self.redis.sadd(f"edit_check_ignore_channels", channel.id)
        await ctx.followup.send(f"Successfully added <#{channel.id}> to the ignore list.")

    @edit_checker.command(name="unignore_channel", description="Remove channel from the list of channels in which edits will be ignored.")
    async def _unignore_channel(
            self,
            ctx: discord.ApplicationContext,
            channel: discord.Option(discord.TextChannel, required=True, description="The channel to un-ignore")
    ):
        await ctx.defer()
        if not ctx.guild:
            await ctx.followup.send("Error! This command can only be used in guilds. DMs won't work.")
            return
        
        logger = set_up_guild_logger(ctx.guild.id)
        logger.info(f"MODERATION: User {ctx.author.name} removed {channel.name} from ignorelist in {ctx.guild.name}")
        await self.redis.srem("edit_check_ignore_channels", channel.id)
        await ctx.followup.send(f"Successfully removed <#{channel.id}> from the ignore list.")

    #
    #  --- Role Ignore Commands
    #

    @edit_checker.command(name="ignore_role", description="Add role to a list of roles whose will be ignored (e.g. Moderators)")
    async def _ignore_role(
            self,
            ctx: discord.ApplicationContext,
            role: discord.Option(discord.Role, required=True, description="The role to ignore")
    ):
        await ctx.defer()
        if not ctx.guild:
            await ctx.followup.send("Error! This command can only used in guilds. DMs won't work.")
            return
        
        logger = set_up_guild_logger(ctx.guild.id)
        logger.info(f"MODERATION: User {ctx.author.name} added role {role.name} to ignorelist in {ctx.guild.name}")
        await self.redis.sadd(f"edit_check_ignore_roles", role.id)
        await ctx.followup.send(f"Successfully added {role.name} to the ignore list.")

    @edit_checker.command(name="unignore_role", description="Remove a role from the list of roles whose edits will be ignored.")
    async def _unignore_role(
            self,
            ctx: discord.ApplicationContext,
            role: discord.Option(discord.Role, required=True, description="The role to un-ignore")
    ):
        await ctx.defer()
        if not ctx.guild:
            await ctx.followup.send("Error! This command can only used in guilds. DMs won't work.")
            return
        
        logger = set_up_guild_logger(ctx.guild.id)
        logger.info(f"MODERATION: User {ctx.author.name} removed role {role.name} from ignorelist in {ctx.guild.name}")
        await self.redis.srem("edit_check_ignore_roles", role.id)
        await ctx.followup.send(f"Successfully removed {role.name} from the ignore list.")


    #
    #  --- Main Listener Function ---
    #


    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent):
        self.bot.events_hour += 1
        self.bot.events_total += 1
        # check if edit checking is enabled

        # ignore DMs
        if not payload.guild_id:
            return

        is_enabled = await settings.RedisFlags.get_guild_flag_custom(
            redis=self.redis,
            gid=payload.guild_id,
            name="moderation",
            flag_offset=Offsets.EDIT_CHECKER,
        )

        # return, if nothing is enabled
        if not is_enabled:
            return

        # check if the channel is in the ignore list
        if await self.redis.sismember("edit_check_ignore_channels", str(payload.channel_id)):
            return

        # check if the author has a role that permits all edits
        orig_channel = await self.bot.fetch_channel(payload.channel_id)
        message = await orig_channel.fetch_message(payload.message_id)

        role_checks = await self.redis.smismember("edit_check_ignore_roles", [role.id for role in message.author.roles])
        if any(role_checks):
            return

        # get the settings from the hash in order to figure out how to proceed from here
        check_settings = await self.redis.hgetall(f"edit_check:{payload.guild_id}")

        # return if that somehow didn't exist
        if not check_settings:
            return
        # check if message is too old
        if check_message_age(payload.message_id, int(check_settings["age"])):
            # message is too old, let's decide what to do with it
            match int(check_settings["behavior"]):
                case 0:
                    # do nothing
                    return

                case 1:
                    # send warning message in warning channel
                    # get the warning channel
                    warn_channel = await self.bot.fetch_channel(int(check_settings["channel_id"]))
                    warn_embed = mod_embeds.gen_edit_warning(payload)

                    await warn_channel.send(embed=warn_embed)
                    return

                case 2:
                    # delete

                    # get the message from the API
                    try:
                        await message.delete(reason="Automatic removal of old messages suddenly edited.")
                        logger = set_up_guild_logger(ctx.guild.id)
                        logger.info(f"MODERATION: Message {message.id} by {message.author} deleted by edit-checker.")
                        return
                    
                    except Exception:
                        logger = set_up_guild_logger(ctx.guild.id)
                        logger.warn(f"MODERATION: Edit-checker failed to delete {message.id} by {message.author}")
                        return

                case 3:
                    # warn and delete

                    # generate the warning embed
                    warn_channel = self.bot.get_channel(int(check_settings["channel_id"]))
                    warn_embed = mod_embeds.gen_edit_warning(payload)
                    warn_embed.title = f"Deleted old edited message by {message.author.name}#{message.author.discriminator}"

                    try:
                        await message.delete(reason="Automatic removal of old messages suddenly edited.")
                        self.logger.info(f"MODERATION: Message {message.id} by {message.author} deleted by edit-checker.")

                    except discord.Forbidden:
                        await warn_channel.send("Failed to to delete due to insufficient permissions:", embed=warn_embed)
                        self.logger.warn(f"MODERATION: Edit-checker failed to delete {message.id} by {message.author}")
                        return
            
                    await warn_channel.send(embed=warn_embed)


def setup(bot):
    bot.add_cog(ModerationCommands(bot))
