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
import logging
import asyncio

import discord
from redis import asyncio as aioredis
from discord.ext import commands

from thatkitebot.base.util import PermissonChecks as pc
from thatkitebot.base.util import Parsing
from thatkitebot.base.util import parse_timestring, check_message_age
from thatkitebot.tkb_redis.settings import RedisFlags as flags
from thatkitebot.embeds.starboard import generate_embed
from thatkitebot.base.exceptions import *
from thatkitebot.base.util import set_up_guild_logger
#endregion

#region Modes
class Modes:
    GLOBAL_THRESHOLD = 1
    SINGLE_CHANNEL_THRESHOLD = 2
#endregion

#region Functions
async def set_starboard(redis: aioredis.Connection, channel_id, mode, threshold, emoji, guild_id, channel_list=None, video: bool = True, time_string: str = "") -> bool:
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
    return await flags.set_guild_flag(redis=redis, gid=guild_id, flag_offset=flags.FlagEnum.STARBOARD,value=False) == flags.FlagEnum.STARBOARD.value

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
    async for starmsg in starboard_channel.history(limit=300):
        # ignore messages without embeds
        if not starmsg.embeds:
            continue

        # ignore messages that are not somehow from the channel
        if starmsg.channel is not starboard_channel:
            continue
        
        # ignore messages that weren't sent by the bot
        if starmsg.author.id != bot_id:
            continue
        try:
            # FIXME
            # ignore messages with empty embeds
            for embed in starmsg.embeds:
                print(len(embed))
            
            # make sure that the starred message is correct
            if message.jump_url in starmsg.embeds[0].description and starmsg.embeds[0].timestamp == message.created_at:
                return starmsg
            
        # continue if this dumb error ever occurs
        except TypeError:
            continue

    return None
#endregion

#region Cog
class StarBoard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis: aioredis.Redis = bot.redis
        self.star_redis: aioredis.Redis = bot.redis_starboard
        self.logger: logging.Logger = bot.logger

        self.starboard_lock = asyncio.Lock()

    # read the starboard blacklist from redis
    async def get_blacklist(self, guild_id):
        key = f"starboard_blacklist:{guild_id}"
        return await self.redis.hgetall(key)

    #region command groups
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

    #region enable commands
    @starboard.command(name="enable", description="Set the starboard settings for this guild. Overrides previous settings.", checks=[pc.can_change_settings])
    async def _starboard_enable(
            self,
            ctx: discord.ApplicationContext,
            threshold: discord.Option(int, description="Minimum amount of emojis", required=True, min_value=1, max_value=99), # type: ignore
            channel: discord.Option(discord.abc.GuildChannel, "The channel where starboard messages are sent", required=True), # type: ignore
            emoji: discord.Option(str, "The emoji to count", required=True), # type: ignore
            max_age: discord.Option(str, description="The maximum age of messages added to starboard. Format like `1y 2w 3d 4h 5m 6s`", required=False) # type: ignore
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
            threshold: discord.Option(int, description="Minimum amount of emojis", required=True, min_value=1, max_value=99), # type: ignore
            emoji: discord.Option(str, description="The emoji to count", required=True), # type: ignore
            starboard_channel: discord.Option(discord.abc.GuildChannel, description="The channel where starboard messages are sent", required=True), # type: ignore
            listen_channel: discord.Option(discord.abc.GuildChannel, description="The channel to listen in.", required=True), # type: ignore
            max_age: discord.Option(str, description="The maximum age of messages added to starboard. Format like `1y 2w 3d 4h 5m 6s`", required=False), # type: ignore
            enable_video: discord.Option(bool, description="Whether to enable or disable videos", required=False) # type: ignore
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
            channel_list=[str(listen_channel.id)],
            video=enable_video
        )

        logger = set_up_guild_logger(ctx.guild.id)
        logger.info(f"STARBOARD: User {ctx.author.name} activated starboard in {ctx.guild.name}")

        await ctx.followup.send(
            f"Starboard in {starboard_channel.mention} will now listen in the channel {listen_channel} for the {emoji} emoji."
        )
    #endregion

    #region blacklist commands
    @_blacklist.command(name="add", description="Blacklists a channel from appearing on starboard")
    async def blacklist_add(
            self,
            ctx: discord.ApplicationContext,
            channel: discord.Option(discord.abc.GuildChannel, description="The channel you want to blacklist", required=True) # type: ignore
    ):
        await ctx.defer()

        if await flags.get_guild_flag(self.redis, ctx.guild, flags.FlagEnum.STARBOARD):
            raise StarboardDisabledException
        
        logger = set_up_guild_logger(ctx.guild.id)
        logger.info(f"STARBOARD: User {ctx.author.name} blacklisted {channel.name} in {ctx.guild.name}")

        await self.redis.sadd(f"starboard_blacklist:{ctx.guild.id}", channel.id)
        await ctx.followup.send(f"Added {channel.mention} to the starboard blacklist.")


    @_blacklist.command(name="remove", description="Unblacklists a channel.")
    async def starboard_blacklist_remove(
            self,
            ctx: discord.ApplicationContext,
            channel: discord.Option(discord.abc.GuildChannel, description="The channel you want whitelist", required=True) # type: ignore
    ):
        await ctx.defer()

        if await flags.get_guild_flag(self.redis, ctx.guild, flags.FlagEnum.STARBOARD):
            raise StarboardDisabledException
        
        try:
            await self.redis.srem(f"starboard_blacklist:{ctx.guild.id}", channel.id)

        except Exception:
            await ctx.followup.send("Failed to remove the channel from the blacklist, it is likely not blacklisted.")
            return
        
        logger = set_up_guild_logger(ctx.guild.id)
        logger.info(f"STARBOARD: User {ctx.author.name} un-blacklisted {channel.name} in {ctx.guild.name}")
        await ctx.followup.send(f"Removed {channel.mention} from the starboard blacklist.")
    #endregion

    #region threshold commands
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
            ) # type: ignore
    ):
        await ctx.defer()

        # check if the disable flag is set
        if await flags.get_guild_flag(self.redis, ctx.guild, flags.FlagEnum.STARBOARD):
            raise StarboardDisabledException

        # check if starboard settings even exist
        if not await self.redis.exists(f"starboard_settings:{ctx.guild_id}"):
            await ctx.followup.send("Starboard settings could not be found, please make sure Starboard has been set up.")
            return

        
        logger = set_up_guild_logger(ctx.guild.id)
        logger.info(f"STARBOARD: User {ctx.author.name} set global threshold to {threshold} in {ctx.guild.name}")
        await self.redis.hset(f"starboard_settings:{ctx.guild.id}", "threshold", threshold)
        if await flags.get_guild_flag(self.redis, guild=ctx.guild, flag_offset=flags.FlagEnum.STARBOARD):
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
            ), # type: ignore
            channel: discord.Option(discord.TextChannel, description="The channel you want to change") # type: ignore
    ):
        await ctx.defer()

        # check if the disable flag is set
        if await flags.get_guild_flag(self.redis, ctx.guild, flags.FlagEnum.STARBOARD):
            raise StarboardDisabledException

        # check if starboard settings even exist
        if not await self.redis.exists(f"starboard_settings:{ctx.guild_id}"):
            await ctx.followup.send("Starboard settings could not be found, please make sure Starboard has been set up.")
            return
        
        logger = set_up_guild_logger(ctx.guild.id)
        logger.info(f"STARBOARD: User {ctx.author.name} set the threshold for {channel.name} to {threshold} in {ctx.guild.name}")

        await self.redis.hset(f"starboard_thresholds", str(channel.id), threshold)
        await ctx.followup.send(f"The threshold for {channel.mention} has been set to **{threshold}**.")

    #endregion
    
    #region settings
    @starboard.command(name="disable", description="Disables all starboard functionality while keeping all settings", checks=[pc.can_change_settings])
    async def _disable(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        # set the disable-flag to 1

        logger = set_up_guild_logger(ctx.guild.id)
        logger.info(f"STARBOARD: User {ctx.author.name} disabled starboard in {ctx.guild.name}")

        await flags.set_guild_flag(redis=self.redis, gid=ctx.guild.id, flag_offset=flags.FlagEnum.STARBOARD,value=True)
        await ctx.followup.send("Starboard functionality has been completely disabled (Existing settings will be kept)")


    @starboard.command(name="set_max_age", description="Set the maximum age for messages to be added to starboard")
    async def _set_max_age(
        self,
        ctx: discord.ApplicationContext,
        max_age: discord.Option(str, description="The maximum age of messages added to starboard. Format like `1y 2w 3d 4h 5m 6s`",required=False) # type: ignore
    ):
        await ctx.defer()

        # check if the disable flag is set
        if await flags.get_guild_flag(self.redis, ctx.guild, flags.FlagEnum.STARBOARD):
            raise StarboardDisabledException

        if max_age and parse_timestring(max_age) == 0:
            await ctx.followup.send("Invalid maximum age!")
            return

        await self.redis.hset(f"starboard_settings:{ctx.guild.id}", "max_age", parse_timestring(max_age))

        logger = set_up_guild_logger(ctx.guild.id)
        logger.info(f"STARBOARD: User {ctx.author.name} changed max_age to {max_age} in {ctx.guild.name}")

        await ctx.followup.send("Successfully updated the maximum age for new messages.")


    @starboard.command(name="video_enable", description="Enable or disable videos in starboard messages.")
    async def _video(self, ctx: discord.ApplicationContext, enable: discord.Option(bool, description="Whether to enable or disable videos", required=True)): # type: ignore
        await ctx.defer()

        if await flags.get_guild_flag(self.redis, ctx.guild, flags.FlagEnum.STARBOARD):
            raise StarboardDisabledException
        
        await self.redis.hset(f"starboard_settings:{ctx.guild.id}", "video", int(enable))
        
        logger = set_up_guild_logger(ctx.guild.id)
        status = "enabled" if enable else "disabled"
        logger.info(f"STARBOARD: User {ctx.author.name} {status} videos in starboard {ctx.guild.name}")
        await ctx.followup.send(f"Videos are now **{status}** in starboard messages.")
    #endregion    
    
    #region main listeners
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        self.bot.events_hour += 1
        self.bot.events_total += 1
        async with self.starboard_lock:
            # check if starboard is enabled on this guild
            # this flag is 1 to disable and 0 to enable to preserve compatibility
            
            # return if not in a guild
            if not payload.guild_id or payload.member.bot or payload.user_id == self.bot.user.id:
                return
            
            # check if starboad is disabled
            if await flags.get_guild_flag(redis=self.redis, guild=payload.guild_id, flag_offset=flags.FlagEnum.STARBOARD):
                return

            channel = await self.bot.fetch_channel(payload.channel_id)

            # check if the channel is blacklisted
            if await self.redis.sismember(f"starboard_blacklist:{channel.guild.id}", str(channel.id)):
                return
            
            # check if it is a thread belonging to a blacklisted channel
            if type(channel) is discord.Thread and await self.redis.sismember(f"starboard_blacklist:{channel.guild.id}", str(channel.parent_id)):
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
                video_is_enabled = bool(starboard_settings.get("video",  1))
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

                        # check for the correct threshold (global or channel-specific threshold)

                        # get the correct channelto account while accounting for threads
                        if type(message.channel) is discord.Thread:
                            # check if the thread has its own threshold set
                            channel_threshold = await self.redis.hget("starboard_thresholds", str(message.channel.id)) or None

                            # if no threshold for the thread has been set, use the parent's threshold
                            if channel_threshold is None:
                                channel_threshold = await self.redis.hget("starboard_thresholds", str(message.channel.parent_id)) or None


                        else:
                            channel_threshold = await self.redis.hget("starboard_thresholds", str(message.channel.id)) or None

                        if channel_threshold is not None and not count >= int(channel_threshold):
                            return

                        elif channel_threshold is None and not count >= int(threshold):
                            return

                        # check the database if the message has already been posted to starboard
                        in_database = (await self.star_redis.get(f"{payload.guild_id}:{message.id}") or False)
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
                            
                            embed, pfp_file, video_file = await generate_embed(message, count, star_emoji, aiohttp_session=self.bot.aiohttp_session, return_file=video_is_enabled)
                            new_message = None

                            if video_file:
                                new_message = await star_channel.send(embed=embed, files=[pfp_file, video_file])

                            else:
                                new_message = await star_channel.send(embed=embed, files=[pfp_file])

                            # add the new message to the database
                            await self.star_redis.set(f"{payload.guild_id}:{message.id}", new_message.id)
                            return

                        elif already_posted and isinstance(starboard_message, discord.Message):
                            # update the starboard message
                            embed, pfp_file, _ = await generate_embed(message, count, star_emoji, aiohttp_session=self.bot.aiohttp_session)
                            await starboard_message.edit(embed=embed, files=[pfp_file])

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
    #endregion

def setup(bot):
    bot.add_cog(StarBoard(bot))
