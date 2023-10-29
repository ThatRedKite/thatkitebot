#  Copyright (c) 2019-2023 ThatRedKite and contributors
import logging
from datetime import timedelta, datetime

import discord
from redis import asyncio as aioredis
from discord.ext import commands

from thatkitebot.base.util import PermissonChecks as pc
from thatkitebot.base.util import Parsing
from thatkitebot.base.util import parse_timestring, check_message_age, ids_from_link
from thatkitebot.tkb_redis.settings import RedisFlags as flags
from thatkitebot.embeds.starboard import generate_embed
from thatkitebot.base.exceptions import *
from thatkitebot.base.util import set_up_guild_logger

class Modes:
    GLOBAL_THRESHOLD = 1
    SINGLE_CHANNEL_THRESHOLD = 2


async def set_starboard(redis, channel_id, mode, threshold, emoji, guild_id, channel_list=None, video: bool = True, time_string: str = ""):
    redis: aioredis.Redis
    """
    Set the starboard settings for a guild
    """

    # parse the date string if supplied
    max_age = 0
    if time_string:
        max_age = parse_timestring(time_string)

    setdict = {
        "channel_id": channel_id,
        "mode": mode,
        "threshold": threshold,
        "star_emoji": emoji.strip(),
        "channels": ";".join(channel_list) if channel_list else "None",
        "video": int(video),
        "max_age": max_age,
    }
    await redis.hset(f"starboard_settings:{guild_id}", mapping=setdict)

    # set the disable-flag to 0
    await flags.set_guild_flag(redis=redis, gid=guild_id, flag_offset=flags.STARBOARD, value=False)


async def check_permissions(ctx, channel: discord.TextChannel):
    if not channel.permissions_for(ctx.me).send_messages:
        await ctx.followup.send("I don't have permission to send messages in that channel.")
        return False
    elif not channel.permissions_for(ctx.me).embed_links:
        await ctx.followup.send("I don't have permission to embed links in that channel.")
        return False
    elif not channel.permissions_for(ctx.me).manage_messages:
        await ctx.followup.send("I don't have permission to manage messages in that channel.")
        return False
    return True


async def check_if_already_posted(message: discord.Message, starboard_channel: discord.TextChannel, bot_id: int):
    """
    Check if the message has already been posted to the starboard
    """
    async for starmsg in starboard_channel.history().filter(lambda m: m.embeds and m.author.bot):
        if starmsg.author.id == bot_id:
            continue
        if message.jump_url in starmsg.embeds[0].description:
            starboard_message = starmsg  # the starboard message id
            return starboard_message
        else:
            continue
    return None


class StarBoard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis: aioredis.Redis = bot.redis
        self.star_redis: aioredis.Redis = bot.redis_starboard
        self.logger: logging.Logger = bot.logger

    # read the starboard blacklist from redis
    async def get_blacklist(self, guild_id):
        key = f"starboard_blacklist:{guild_id}"
        return await self.redis.hgetall(key)

    starboard: discord.SlashCommandGroup = discord.SlashCommandGroup(
        name="starboard",
        description="starboard Commands",
        checks=[pc.can_change_settings, lambda ctx: ctx.guild is not None]
    )

    _blacklist: discord.SlashCommandGroup = discord.SlashCommandGroup(
        name="starboard_blacklist",
        description="Commands related to blacklisting blacklisted channels",
        checks=[pc.can_change_settings, lambda ctx: ctx.guild is not None],
    )

    _threshold: discord.SlashCommandGroup = discord.SlashCommandGroup(
        name="starboard_threshold",
        description="Commands related to (re)setting the emoji threshold(s)",
        checks=[pc.can_change_settings, lambda ctx: ctx.guild is not None],
    )

    @starboard.command(name="enable", description="Set the starboard settings for this guild. Overrides previous settings.", checks=[pc.can_change_settings])
    async def _starboard_enable(
            self,
            ctx: discord.ApplicationContext,
            threshold: discord.Option(int, description="Minimum amount of emojis", required=True, min_value=1, max_value=99),
            channel: discord.Option(discord.abc.GuildChannel, "The channel where starboard messages are sent", required=True),
            emoji: discord.Option(str, "The emoji to count", required=True),
            max_age: discord.Option(str, description="The maximum age of messages added to starboard. Format like `1y 2w 3d 4h 5m 6s`", required=False)
    ):
        await ctx.defer()

        if not await check_permissions(ctx, channel):
            return

        if not Parsing.check_emoji(emoji):
            await ctx.followup.send("Invalid Emoji!")
            return

        if max_age and parse_timestring(max_age) == 0:
            await ctx.followup.send("Invalid maximum age!")
            return

        await set_starboard(
            redis=self.redis,
            channel_id=channel.id,
            mode=Modes.GLOBAL_THRESHOLD,
            threshold=threshold,
            emoji=emoji,
            guild_id=ctx.guild.id,
            channel_list=[],
            time_string=max_age
        )

        self.logger.info(f"STARBOARD: User {ctx.author.name} activated starboard in {ctx.guild.name}")

        await ctx.followup.send(
            f"Starboard set to threshold mode for {channel.mention} with threshold {threshold} and emoji {emoji}."
        )


    @starboard.command(name="channel_specific_starboard", description="A starboard that will only listen in specific channels. Overrides previous settings.",checks=[pc.can_change_settings])
    async def _starboard_channel_specific(
            self,
            ctx: discord.ApplicationContext,
            threshold: discord.Option(int, description="Minimum amount of emojis", required=True, min_value=1, max_value=99),
            emoji: discord.Option(str, description="The emoji to count", required=True),
            starboard_channel: discord.Option(discord.abc.GuildChannel, description="The channel where starboard messages are sent", required=True),
            listen_channel: discord.Option(discord.abc.GuildChannel, description="The channel to listen in.", required=True),
            max_age: discord.Option(str, description="The maximum age of messages added to starboard. Format like `1y 2w 3d 4h 5m 6s`", required=False)
    ):
        await ctx.defer()

        if not await check_permissions(ctx, listen_channel):
            return

        if not Parsing.check_emoji(emoji):
            await ctx.followup.send("Invalid Emoji!")

        if max_age and parse_timestring(max_age) == 0:
            await ctx.followup.send("Invalid maximum age!")
            return

        await set_starboard(
            redis=self.redis,
            channel_id=starboard_channel.id,
            mode=Modes.SINGLE_CHANNEL_THRESHOLD,
            threshold=threshold,
            emoji=emoji,
            guild_id=ctx.guild.id,
            channel_list=[str(listen_channel.id)]
        )

        logger = set_up_guild_logger(ctx.guild.id)
        logger.info(f"STARBOARD: User {ctx.author.name} activated starboard in {ctx.guild.name}")

        await ctx.followup.send(
            f"Starboard in {starboard_channel.mention} will now listen in the channel {listen_channel} for the {emoji} emoji."
        )


    @_blacklist.command(name="add", description="Blacklists a channel from appearing on starboard")
    async def blacklist_add(
            self,
            ctx: discord.ApplicationContext,
            channel: discord.Option(discord.abc.GuildChannel, description="The channel you want to blacklist", required=True)
    ):
        await ctx.defer()

        if await flags.get_guild_flag(self.redis, ctx.guild.id, flags.STARBOARD):
            raise StarboardDisabledException
        
        logger = set_up_guild_logger(ctx.guild.id)
        logger.info(f"STARBOARD: User {ctx.author.name} blacklisted {channel.name} in {ctx.guild.name}")

        await self.redis.sadd(f"starboard_blacklist:{ctx.guild.id}", channel.id)
        await ctx.followup.send(f"Added {channel.mention} to the starboard blacklist.")


    @_blacklist.command(name="remove", description="Unblacklists a channel.")
    async def starboard_blacklist_remove(
            self,
            ctx: discord.ApplicationContext,
            channel: discord.Option(discord.abc.GuildChannel, description="The channel you want whitelist", required=True)
    ):
        await ctx.defer()

        if await flags.get_guild_flag(self.redis, ctx.guild.id, flags.STARBOARD):
            raise StarboardDisabledException
        
        try:
            await self.redis.srem(f"starboard_blacklist:{ctx.guild.id}", channel.id)

        except Exception:
            await ctx.followup.send("Failed to remove the channel from the blacklist, it is likely not blacklisted.")
            return
        
        logger = set_up_guild_logger(ctx.guild.id)
        logger.info(f"STARBOARD: User {ctx.author.name} un-blacklisted {channel.name} in {ctx.guild.name}")

        await ctx.followup.send(f"Removed {channel.mention} from the starboard blacklist.")


    @_threshold.command(name="set_global", description="Sets the global threshold, does not affect thresholds for individual channels.")
    async def _set_global(
            self,
            ctx: discord.ApplicationContext,
            threshold: discord.Option(
                int,
                name="threshold",
                description="The threshold you want to use",
                max_value=99,
                min_value=1,
                required=True
            )
    ):
        await ctx.defer()

        # check if the disable flag is set
        if await flags.get_guild_flag(self.redis, ctx.guild.id, flags.STARBOARD):
            raise StarboardDisabledException

        # check if starboard settings even exist
        if not await self.redis.exists(f"starboard_settings:{ctx.guild_id}"):
            await ctx.followup.send("Starboard settings could not be found, please make sure Starboard has been set up.")
            return

        
        logger = set_up_guild_logger(ctx.guild.id)
        logger.info(f"STARBOARD: User {ctx.author.name} set global threshold to {threshold} in {ctx.guild.name}")
        await self.redis.hset(f"starboard_settings:{ctx.guild.id}", "threshold", threshold)
        if await flags.get_guild_flag(self.redis, gid=ctx.guild.id, flag_offset=flags.STARBOARD):
            await ctx.followup.send("Starboard has been disabled. The threshold has been changed but starboard remains disabled")
            return

        else:
            await ctx.followup.send(f"Global starboard threshold has been set to **{threshold}**. Channels with custom thresholds stay unaffected by this.")
            return
        

    @_threshold.command(name="set_channel", description="Sets the threshold for a specific channel. Unaffected by the global threshold.")
    async def _set_channel(
            self,
            ctx: discord.ApplicationContext,
            threshold: discord.Option(
                int,
                name="threshold",
                description="The threshold you want to use",
                max_value=99,
                min_value=1
            ),
            channel: discord.Option(discord.TextChannel, description="The channel you want to change")
    ):
        await ctx.defer()

        # check if the disable flag is set
        if await flags.get_guild_flag(self.redis, ctx.guild.id, flags.STARBOARD):
            raise StarboardDisabledException

        # check if starboard settings even exist
        if not await self.redis.exists(f"starboard_settings:{ctx.guild_id}"):
            await ctx.followup.send("Starboard settings could not be found, please make sure Starboard has been set up.")
            return
        
        logger = set_up_guild_logger(ctx.guild.id)
        logger.info(f"STARBOARD: User {ctx.author.name} set the threshold for {channel.name} to {threshold} in {ctx.guild.name}")

        await self.redis.hset(f"starboard_thresholds", str(channel.id), threshold)
        await ctx.followup.send(f"The threshold for {channel.mention} has been set to **{threshold}**.")


    @starboard.command(name="disable", description="Disables all starboard functionality while keeping all settings", checks=[pc.can_change_settings])
    async def _disable(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        # set the disable-flag to 1

        logger = set_up_guild_logger(ctx.guild.id)
        logger.info(f"STARBOARD: User {ctx.author.name} disabled starboard in {ctx.guild.name}")

        await flags.set_guild_flag(redis=self.redis, gid=ctx.guild.id, flag_offset=flags.STARBOARD, value=True)
        await ctx.followup.send("Starboard functionality has been completely disabled (Existing settings will be kept)")


    @starboard.command(name="set_max_age", description="Set the maximum age for messages to be added to starboard")
    async def _set_max_age(self, ctx: discord.ApplicationContext, max_age: discord.Option(str, )):
        await ctx.defer()

        # check if the disable flag is set
        if await flags.get_guild_flag(self.redis, ctx.guild.id, flags.STARBOARD):
            raise StarboardDisabledException

        if max_age and parse_timestring(max_age) == 0:
            await ctx.followup.send("Invalid maximum age!")
            return

        await self.redis.hset(f"starboard_settings:{ctx.guild.id}", "max_age", parse_timestring(max_age))

        logger = set_up_guild_logger(ctx.guild.id)
        logger.info(f"STARBOARD: User {ctx.author.name} changed max_age to {max_age} in {ctx.guild.name}")

        await ctx.followup.send("Successfully updated the maximum age for new messages.")


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        self.bot.events_hour += 1
        self.bot.events_total += 1

        # check if starboard is enabled on this guild
        # this flag is 1 to disable and 0 to enable to preserve compatibility
        if await flags.get_guild_flag(redis=self.redis, gid=payload.guild_id, flag_offset=flags.STARBOARD):
            return

        channel: discord.TextChannel = await self.bot.fetch_channel(payload.channel_id)
        # check if the channel is blacklisted
        if await self.redis.sismember(f"starboard_blacklist:{channel.guild.id}", str(channel.id)):
            return

        if not await self.redis.exists(f"starboard_settings:{payload.guild_id}"):
            return

        # load the starboard settings
        try:
            starboard_settings = await self.redis.hgetall(f"starboard_settings:{payload.guild_id}")
            mode = int(starboard_settings["mode"])
            star_emoji = starboard_settings["star_emoji"]
            threshold = int(starboard_settings["threshold"])
            star_channel: discord.TextChannel = await self.bot.fetch_channel(starboard_settings["channel_id"])
            channels = starboard_settings["channels"].split(";")
            reaction_emoji = str(payload.emoji)

            # get optional settings
            video_is_enabled = bool(starboard_settings.get("video",  0))
            max_age = int(starboard_settings.get("max_age", 0))

        except KeyError:
            return

        # load the message into the internal cache
        message = await channel.fetch_message(payload.message_id)

        match mode:
            case Modes.GLOBAL_THRESHOLD | Modes.SINGLE_CHANNEL_THRESHOLD:
                # make sure nothing in the starboard channel is starred and put onto the starboard
                if star_channel == channel:
                    return

                if mode == Modes.SINGLE_CHANNEL_THRESHOLD and str(message.channel.id) not in channels:
                    return

                # check if the star emoji is the same as the starboard emoji
                if reaction_emoji == star_emoji:
                    # sort the reactions to get the reaction count for the star emoji
                    message.reactions.sort(key=lambda e: str(e) == str(payload.emoji), reverse=True)
                    count = message.reactions[0].count

                    # check for the correct threshold (global or channel-specific threshold)A
                    channel_threshold = await self.redis.hget("starboard_thresholds", str(message.channel.id)) or None
                    if channel_threshold is not None and not count >= int(channel_threshold):
                        return

                    elif channel_threshold is None and not count >= int(threshold):
                        return

                    # check the database if the message has already been posted to starboard
                    in_database = (await self.star_redis.get(str(message.id)) or False)
                    already_posted = True
                    starboard_message = None

                    # check starboard channel history if message was not found in the database
                    if not in_database:
                        _starboard_message = await check_if_already_posted(message, star_channel, self.bot.user.id)
                        if _starboard_message is not None:
                            starboard_message = _starboard_message

                            # add the message to the database
                            await self.star_redis.set(str(payload.message_id), _starboard_message.id)
                        else:
                            already_posted = False

                    # use the database to avoid searching the starboard channel
                    else:
                        # try fetching the original message with the id from the database
                        try:
                            starboard_message = await star_channel.fetch_message(in_database)
                            already_posted = True

                        except discord.NotFound:
                            self.logger.warn(f"Message with id {in_database} has gone missing from starboard.")
                            already_posted = False

                    if not already_posted:

                        # ignore messages older than allowed
                        if max_age != 0 and check_message_age(payload.message_id, max_age):
                            return
                        
                        embed, file = await generate_embed(message, count, star_emoji, aiohttp_session=self.bot.aiohttp_session, return_file=video_is_enabled)
                        new_message = None

                        if file:
                            new_message = await star_channel.send(embed=embed, file=file)

                        else:
                            new_message = await star_channel.send(embed=embed)

                        # add the new message to the database
                        await self.star_redis.set(str(message.id), new_message.id)
                        return

                    elif already_posted and isinstance(starboard_message, discord.Message):
                        # update the starboard message
                        embed, _ = await generate_embed(message, count, star_emoji)
                        await starboard_message.edit(embed=embed)

                    else:
                        return

                else:
                    return

            case _:
                return
            

    @commands.Cog.listener()
    async def on_application_command_error(self, ctx: discord.ApplicationContext, exception):
        if ctx and isinstance(exception.original, StarboardDisabledException):
                await ctx.followup.send("Starboard has been disabled. Please re-enable it to change settings.")
        else:
            return


def setup(bot):
    bot.add_cog(StarBoard(bot))
