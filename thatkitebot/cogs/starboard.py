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

from importlib import reload
from random import randint

import discord
from redis import asyncio as aioredis
from discord.ext import commands

import thatkitebot
from thatkitebot.base.util import PermissonChecks as pc
from thatkitebot.base.util import Parsing
from thatkitebot.base.util import parse_timestring, check_message_age
import thatkitebot.embeds.starboard
from thatkitebot.tkb_redis.settings import RedisFlags as flags
import thatkitebot.embeds.starboard
from thatkitebot.embeds.starboard import generate_embed
from thatkitebot.base.exceptions import *
from thatkitebot.base.util import set_up_guild_logger
from thatkitebot.cogs.bookmark import Bookmark

#endregion


#region Modes
class StarboardMode:
    GLOBAL_THRESHOLD: int = 1
    SINGLE_CHANNEL_THRESHOLD: int = 2
#endregion

class StarboardView(discord.ui.View):
    def __init__(self, redis: aioredis.Redis):
        self.redis = redis
        super().__init__(timeout=None)

    @discord.ui.button(label="Bookmark Post", style=discord.ButtonStyle.secondary, custom_id=f"starboard-bookmark-button", emoji="🔖")
    async def button(self, button: discord.Button, interaction: discord.Interaction):
        bm = Bookmark.from_message(self.redis, interaction.user.id, interaction.message, f"Starboard Message by {interaction.message.author.name}")
        await bm.save()
        del bm

        try:
            await interaction.respond(f"Added {interaction.message.jump_url} to your bookmarks", ephemeral=True)
        except:
            return
            

class StarboardSettings:
    def __init__(self, redis: aioredis.Redis, bot, guild_id: int):
        self.redis = redis
        self.bot = bot

        self.mode: int = StarboardMode.GLOBAL_THRESHOLD
        self.channel: discord.TextChannel = None
        self.guild_id = guild_id
        self.emoji: str = ""
        self.threshold: int = 0
        self.max_age: int = 0 
        self.channels: list = []
        self.video_enabled: bool = True
        self.ignore_threads: bool = False
    
    @classmethod
    async def from_redis(cls, redis:aioredis.Redis,bot, guild_id:int):
        if not await redis.exists(f"starboard_settings:{guild_id}"):
            raise KeyError("No Starboard settings found, starboard is likely uninitialized")
        
        data = await redis.hgetall(f"starboard_settings:{guild_id}")
        new = cls(redis, bot, guild_id)

        new.mode = int(data["mode"])
        new.emoji = data["star_emoji"]
        new.threshold = int(data["threshold"])
        new.channel = await bot.get_or_fetch_channel(data["channel_id"])
        new.channels = data["channels"].split(";")
        new.ignore_threads = data.get("threads", False)
        new.video_enabled = data.get("video", True)

        return new

    async def save(self):
        a ={
            "mode": int(self.mode),
            "channel_id": int(self.channel.id),
            "threshold": int(self.threshold),
            "star_emoji": self.emoji.strip(),
            "channels": ";".join(self.channels) if self.channels else None,
            "max_age": int(self.max_age),
            "video": int(self.video_enabled),
            "threads": int(self.ignore_threads),
        }
        await self.redis.hset(name=f"starboard_settings:{self.guild_id}", mapping=a)
    
    async def enable(self) -> bool:
         return await flags.set_guild_flag(redis=self.redis, gid=self.guild_id, flag_offset=flags.FlagEnum.STARBOARD,value=False) == flags.FlagEnum.STARBOARD.value


#region Functions


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
            
            # make sure that the starred message is correct
            if message.jump_url in starmsg.embeds[0].description and starmsg.embeds[0].timestamp == message.created_at:
                return starmsg
            
        # continue if this dumb error ever occurs
        except TypeError:
            continue

    return None
#endregion

#region Cog
class StarboardCog(commands.Cog):
    def __init__(self, bot):
        self.bot: thatkitebot.ThatKiteBot = bot
        self.redis: aioredis.Redis = bot.redis
        self.star_redis: aioredis.Redis = bot.redis_starboard
        self.bookmark_redis = bot.redis_bookmarks
        self.logger: logging.Logger = bot.logger

        self.starboard_lock = asyncio.Lock()
        self.bot.add_view(StarboardView(self.bookmark_redis))
        reload(thatkitebot.embeds.starboard)


    # read the starboard blacklist from redis

    async def check_permissions(self, ctx, channel: discord.TextChannel):
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
            threshold: discord.Option(int, "Minimum amount of emojis", required=True, min_value=1, max_value=99), # type: ignore
            channel: discord.Option(discord.abc.GuildChannel, "The channel where starboard messages are sent", required=True), # type: ignore
            emoji: discord.Option(str, "The emoji to count", required=True), # type: ignore
            max_age: discord.Option(str, "The maximum age of messages added to starboard. Format like `1y 2w 3d 4h 5m 6s`", required=False), # type: ignore
            enable_video: discord.Option(bool, description="Whether to enable or disable videos", required=False), # type: ignore
            ignore_threads: discord.Option(bool, "Ignore all messages in Threads", required=False) # type: ignore
    ):
        await ctx.defer()

        if not await self.check_permissions(ctx, channel):
            return

        if not Parsing.check_emoji(emoji):
            await ctx.followup.send("Invalid Emoji!")
            return

        if max_age and parse_timestring(max_age) == 0:
            await ctx.followup.send("Invalid maximum age!")
            return

        settings = StarboardSettings(self.redis, self.bot, ctx.guild_id)

        settings.mode = StarboardMode.GLOBAL_THRESHOLD
        settings.threshold = threshold
        settings.channel = channel
        settings.emoji = emoji
        settings.max_age = parse_timestring(max_age) or 0
        settings.video_enabled = enable_video
        settings.ignore_threads = ignore_threads

        await settings.save()

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
            enable_video: discord.Option(bool, description="Whether to enable or disable videos", required=False), # type: ignore
            ignore_threads: discord.Option(bool, "Ignore all messages in Threads", required=False) # type: ignore
    ):
        await ctx.defer()

        if not await self.check_permissions(ctx, listen_channel):
            return

        if not Parsing.check_emoji(emoji):
            await ctx.followup.send("Invalid Emoji!")

        if max_age and parse_timestring(max_age) == 0:
            await ctx.followup.send("Invalid maximum age!")
            return
        

        settings = StarboardSettings(self.redis, self.bot, ctx.guild_id)
        settings.mode = StarboardMode.SINGLE_CHANNEL_THRESHOLD
        settings.threshold = threshold
        settings.channel = starboard_channel
        settings.channels = [listen_channel]
        settings.video_enabled = enable_video
        settings.emoji = emoji
        settings.max_age = parse_timestring(max_age) or 0
        settings.ignore_threads = ignore_threads


        logger = set_up_guild_logger(ctx.guild_id)
        logger.info(f"STARBOARD: User {ctx.author.name} activated starboard in {ctx.guild.name}")

        await ctx.followup.send(
            f"Starboard in {starboard_channel.mention} will now listen in the channel {listen_channel} for the {emoji} emoji."
        )
    #endregion

    #region blacklist methods
    async def blacklist_toggle_channel(self, ctx, guild: discord.Guild, channel: discord.TextChannel | discord.Thread) -> bool:
        name = f"starboard_blacklist:{guild.id}"
        logger = set_up_guild_logger(guild.id)

        if await self.redis.sismember(name):
            logger.info(f"STARBOARD: User {ctx.author.name} unblacklisted #{channel.name} in {ctx.guild.name}")
            await self.redis.srem(name, channel.id)
            return True
        else:
            logger.info(f"STARBOARD: User {ctx.author.name} blacklisted #{channel.name} in {ctx.guild.name}")
            await self.redis.sadd(name, channel.id)
            return False
        
    async def blacklist_toggle_user(self, ctx, guild: discord.Guild, user: discord.User | discord.Member) -> bool:
        name = f"user_blacklist:{guild.id}"
        logger = set_up_guild_logger(guild.id)

        if await self.redis.sismember(name):
            logger.info(f"STARBOARD: User {ctx.author.name} unblacklisted @{user.name} in {ctx.guild.name}")
            await self.redis.srem(name, user.id)
            return True
        else:
            logger.info(f"STARBOARD: User {ctx.author.name} blacklisted @{user.name} in {ctx.guild.name}")
            await self.redis.sadd(name, user.id)
            return False
        
    async def blacklist_toggle_all_threads(self, ctx, guild: discord.Guild, user: discord.User | discord.Member) -> bool:
        name = f"thread_blacklist:{guild.id}"
        logger = set_up_guild_logger(guild.id)

        if await self.redis.sismember(name):
            logger.info(f"STARBOARD: User {ctx.author.name} unblacklisted #{user.name}'s threads in {ctx.guild.name}")

            await self.redis.srem(name, user.id)
            return True
        else:
            logger.info(f"STARBOARD: User {ctx.author.name} blacklisted #{user.name}'s threads in {ctx.guild.name}")
            await self.redis.sadd(name, user.id)
            return False
    #endregion

    #region blacklist commands
    @_blacklist.command(name="channel", description="Channel blacklist toggle")
    async def blacklist_channel(
            self,
            ctx: discord.ApplicationContext,
            channel: discord.Option(discord.TextChannel, description="The channel you want to blacklist", required=True) # type: ignore
    ):
        await ctx.defer()

        if await flags.get_guild_flag(self.redis, ctx.guild, flags.FlagEnum.STARBOARD):
            raise StarboardDisabledException
        
        if await self.blacklist_toggle_channel(ctx, ctx.guild, channel):
            await ctx.followup.send(f"Added {channel.mention} to the starboard blacklist.")
        else:
            await ctx.followup.send(f"Removed {channel.mention} from the starboard blacklist.")


    @_blacklist.command(name="user", description="User blacklist toggle")
    async def blacklist_user(
            self,
            ctx: discord.ApplicationContext,
            user: discord.Option(discord.Member, description="The user you want to toggle", required=True) # type: ignore
    ):
        await ctx.defer()

        if await flags.get_guild_flag(self.redis, ctx.guild, flags.FlagEnum.STARBOARD):
            raise StarboardDisabledException
        
        if await self.blacklist_toggle_user(ctx, ctx.guild, user):
            await ctx.followup.send(f"Added {user.name} to the starboard blacklist.")

        else:
            await ctx.followup.send(f"Removed {user.name} from the starboard blacklist.")

    @_blacklist.command(name="thread", description="Toggle blacklist for all threads of a channel")
    async def blacklist_all_threads(
            self,
            ctx: discord.ApplicationContext,
            thread: discord.Option(discord.Thread, description="The thread you want to blacklist", required=True) # type: ignore
    ):
        await ctx.defer()

        if await flags.get_guild_flag(self.redis, ctx.guild, flags.FlagEnum.STARBOARD):
            raise StarboardDisabledException
        
        if await self.blacklist_toggle_channel(ctx, ctx.guild, thread.id):
            await ctx.followup.send(f"Added {thread.mention} to the starboard blacklist.")

        else:
            await ctx.followup.send(f"Removed {thread.mention} from the starboard blacklist.")
    

    @_blacklist.command(name="threads", description="Toggle blacklist for all threads of a channel")
    async def blacklist_all_threads(
            self,
            ctx: discord.ApplicationContext,
            channel: discord.Option(discord.TextChannel, description="The channel", required=True) # type: ignore
    ):
        await ctx.defer()

        if await flags.get_guild_flag(self.redis, ctx.guild, flags.FlagEnum.STARBOARD):
            raise StarboardDisabledException
        
        if await self.blacklist_toggle_all_threads(ctx, ctx.guild, channel):
            await ctx.followup.send(f"Added {channel.mention} to the starboard blacklist.")

        else:
            await ctx.followup.send(f"Removed {channel.mention} from the starboard blacklist.")


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
            await ctx.followup.send("Error: Starboard settings could not be found, please make sure Starboard has been set up.")
            return

        if await flags.get_guild_flag(self.redis, guild=ctx.guild, flag_offset=flags.FlagEnum.STARBOARD):
            await ctx.followup.send("Error: Starboard is disabled.")
            return
        
        settings: StarboardSettings = await StarboardSettings.from_redis(self.redis, self.bot, ctx.guild_id)
        settings.threshold = threshold

        await settings.save()
        
        logger = set_up_guild_logger(ctx.guild_id)
        logger.info(f"STARBOARD: User {ctx.author.name} set global threshold to {threshold} in {ctx.guild.name}")
        

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
        
        logger = set_up_guild_logger(ctx.guild_id)
        logger.info(f"STARBOARD: User {ctx.author.name} set the threshold for {channel.name} to {threshold} in {ctx.guild.name}")

        await self.redis.hset(f"starboard_thresholds", str(channel.id), threshold)
        await ctx.followup.send(f"The threshold for {channel.mention} has been set to **{threshold}**.")

    #endregion
    
    #region settings
    @starboard.command(name="disable", description="Disables all starboard functionality while keeping all settings", checks=[pc.can_change_settings])
    async def _disable(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        # set the disable-flag to 1

        logger = set_up_guild_logger(ctx.guild_id)
        logger.info(f"STARBOARD: User {ctx.author.name} disabled starboard in {ctx.guild.name}")

        await flags.set_guild_flag(redis=self.redis, gid=ctx.guild_id, flag_offset=flags.FlagEnum.STARBOARD,value=True)
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

        await self.redis.hset(f"starboard_settings:{ctx.guild_id}", "max_age", parse_timestring(max_age))

        logger = set_up_guild_logger(ctx.guild_id)
        logger.info(f"STARBOARD: User {ctx.author.name} changed max_age to {max_age} in {ctx.guild.name}")

        await ctx.followup.send("Successfully updated the maximum age for new messages.")


    @starboard.command(name="video_enable", description="Enable or disable videos in starboard messages.")
    async def _video(self, ctx: discord.ApplicationContext, enable: discord.Option(bool, description="Whether to enable or disable videos", required=True)): # type: ignore
        await ctx.defer()

        if await flags.get_guild_flag(self.redis, ctx.guild, flags.FlagEnum.STARBOARD):
            raise StarboardDisabledException
        
        await self.redis.hset(f"starboard_settings:{ctx.guild_id}", "video", int(enable))
        
        logger = set_up_guild_logger(ctx.guild_id)
        status = "enabled" if enable else "disabled"
        logger.info(f"STARBOARD: User {ctx.author.name} {status} videos in starboard {ctx.guild.name}")
        await ctx.followup.send(f"Videos are now **{status}** in starboard messages.")
    #endregion    
    

    #region main listeners
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        self.bot.events_hour += 1
        self.bot.events_total += 1

        # lock the starboard lock
        async with self.starboard_lock:
            # return if not in a guild
            if not payload.guild_id or payload.member.bot or payload.user_id == self.bot.user.id:
                return
            
            # check if starboard is enabled on this guild
            # this flag is 1 to disable and 0 to enable to preserve compatibility
            if await flags.get_guild_flag(redis=self.redis, guild=payload.guild_id, flag_offset=flags.FlagEnum.STARBOARD):
                return
            
            # return if we don't have any starboard settings for this server
            if not await self.redis.exists(f"starboard_settings:{payload.guild_id}"):
                return

            # check if the channel is blacklisted
            if await self.redis.sismember(f"starboard_blacklist:{payload.guild_id}", str(payload.channel_id)):
                return
            
            # see if we have the channel already cached
            channel = await self.bot.get_or_fetch_channel(payload.channel_id)

            # load the starboard settings
            try:
                settings = await StarboardSettings.from_redis(self.redis, self.bot, payload.guild_id)
                reaction_emoji = str(payload.emoji)

            # The starboard is not initialized on this guild, return
            except KeyError:
                return

            # some checks specific to threads
            if isinstance(channel, discord.Thread):
                # check if it is a thread belonging to a blacklisted channel
                if await self.redis.sismember(f"starboard_blacklist:{channel.guild.id}", str(channel.parent_id)):
                    return
                
                if settings.ignore_threads:
                    return

            # load the message into the internal cache
            message = await self.bot.get_or_fetch_message(payload.message_id, channel_id=payload.channel_id)

            match settings.mode:
                case StarboardMode.GLOBAL_THRESHOLD | StarboardMode.SINGLE_CHANNEL_THRESHOLD:
                    # make sure nothing in the starboard channel is starred and put onto the starboard
                    if settings.channel == channel:
                        return

                    if settings.mode == StarboardMode.SINGLE_CHANNEL_THRESHOLD and str(message.channel.id) not in settings.channels:
                        return

                    # check if the star emoji is the same as the starboard emoji
                    if reaction_emoji == settings.emoji:
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

                        elif channel_threshold is None and not count >= int(settings.threshold):
                            return

                        # check the database if the message has already been posted to starboard
                        in_database = (await self.star_redis.get(f"{payload.guild_id}:{message.id}") or False)
                        already_posted = True
                        starboard_message = None

                        # check starboard channel history if message was not found in the database
                        if not in_database:
                            _starboard_message = await check_if_already_posted(message, settings.channel, self.bot.user.id)
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
                                starboard_message = await settings.channel.fetch_message(in_database)
                                already_posted = True

                            except discord.NotFound:
                                self.logger.warning(f"Message with id {in_database} has gone missing from starboard.")
                                already_posted = False

                        if not already_posted:

                            # ignore messages older than allowed
                            if settings.max_age != 0 and check_message_age(payload.message_id, settings.max_age):
                                return
                            
                            embed, pfp_file, video_file = await generate_embed(message, count, settings.emoji, aiohttp_session=self.bot.aiohttp_session, return_file=settings.video_enabled)
                            new_message = None

                            if video_file:
                                new_message = await settings.channel.send(embed=embed, files=[pfp_file, video_file])

                            else:
                                new_message = await settings.channel.send(embed=embed, files=[pfp_file])

                            # add the new message to the database
                            await self.star_redis.set(f"{payload.guild_id}:{message.id}", new_message.id)
                            return

                        elif already_posted and isinstance(starboard_message, discord.Message):
                            # update the starboard message
                            embed, pfp_file, _ = await generate_embed(message, count, settings.emoji, aiohttp_session=self.bot.aiohttp_session)
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
    
    @commands.is_owner()
    @commands.command()
    async def embed_test(self, ctx: commands.Context):
        msg = await self.bot.get_or_fetch_message(ctx.message.reference.message_id, ctx.message.reference.channel_id) if ctx.message.reference else ctx.message
        embed, pfp_file, video_file = await generate_embed(msg, randint(1, 1000), "⭐", True, self.bot.aiohttp_session)
        if video_file:
            await ctx.send(embed=embed,files=[pfp_file, video_file], view=StarboardView(self.bookmark_redis))
        else:
            await ctx.send(embed=embed,files=[pfp_file], view=StarboardView(self.bookmark_redis))
    
    #endregion


def setup(bot):
    bot.add_cog(StarboardCog(bot))