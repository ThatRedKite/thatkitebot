#  Copyright (c) 2019-2023 ThatRedKite and contributors

import discord
from redis import asyncio as aioredis
from discord.ext import commands

from thatkitebot.base.util import PermissonChecks as pc
from thatkitebot.base.util import Parsing
from thatkitebot.embeds.starboard import generate_embed


async def set_starboard(redis, channel_id, mode, threshold, emoji, guild_id, channel_list=None):
    redis: aioredis.Redis
    """
    Set the starboard settings for a guild
    """
    key = f"starboard_settings:{guild_id}"
    setdict = {
        "channel_id": channel_id,
        "mode": mode,
        "threshold": threshold,
        "star_emoji": emoji.strip(),
        "channels": ";".join(channel_list) if channel_list else "None"
    }
    await redis.hmset(key, setdict)


async def check_permissions(ctx, channel: discord.TextChannel):
    if not channel.permissions_for(ctx.me).send_messages:
        await ctx.respond("I don't have permission to send messages in that channel.")
        return False
    elif not channel.permissions_for(ctx.me).embed_links:
        await ctx.respond("I don't have permission to embed links in that channel.")
        return False
    elif not channel.permissions_for(ctx.me).manage_messages:
        await ctx.respond("I don't have permission to manage messages in that channel.")
        return False
    return True


async def check_if_already_posted(message: discord.Message, starboard_channel: discord.TextChannel, bot_id: int):
    """
    Check if the message has already been posted to the starboard
    """
    async for starmsg in starboard_channel.history().filter(lambda m: m.embeds and m.author.bot):
        if not starmsg.author.id == bot_id:
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

    # read the starboard blacklist from redis
    async def get_blacklist(self, guild_id):
        key = f"starboard_blacklist:{guild_id}"
        return await self.redis.hgetall(key)

    # starboard modes:
    # 1: threshold mode (guild global)
    # 2: top message mode (guild global)
    # 3: threshold mode (channel specific)
    # 4: top message mode (channel specific)

    # starboard channel setting
    # redis: key = "starboard:<channel_id>" values = "mode", "threshold", "message_id" (if in thereshold mode)
    # as well as a list of channels if in channel specific mode (list of channel ids) and the star emoji
    # and the starboard channel
    # example:

    # starboard:424394851170385921
    # >mode = 1
    # >threshold = 5
    # >starboard_channel = 586312434592120851
    # >star_emoji = ⭐
    # >channels = None

    # databases
    # settings: settings redis database
    # messages: message cache redis database with star count

    # the channel specific modes will override the global modes for that channel

    # command for adding a global threshold starboard

    starboard = discord.SlashCommandGroup(
        "starboard",
        "starboard Commands",
        checks=[pc.can_change_settings, lambda ctx: ctx.guild is not None]
    )

    @starboard.command(
        name="enable",
        description="Set the starboard settings for this guild",
        checks=[pc.can_change_settings]
    )
    async def _starboard_enable(
            self,
            ctx: discord.ApplicationContext,
            threshold: discord.Option(int, description="Minimum amount of emojis", required=True, min_value=1, max_value=99),
            channel: discord.Option(discord.TextChannel, "The channel where starboard messages are sent", required=True),
            emoji: discord.Option(str, "The emoji to count", required=True)
    ):
        await ctx.defer()
        if not await check_permissions(ctx, channel):
            return

        if not Parsing.check_emoji(emoji):
            await ctx.followup.send("Invalid Emoji!")

        await set_starboard(
            redis=self.redis,
            channel_id=channel.id,
            mode=1,
            threshold=threshold,
            emoji=emoji,
            guild_id=ctx.guild.id,
            channel_list=[]
        )
        await ctx.followup.send(
            f"Starboard set to threshold mode for {channel.mention} with threshold {threshold} and emoji {emoji}."
        )

    @starboard.command(
        name="channel_specific_starboard",
        description="A starboard that will only listen in specific channels",
        checks=[pc.can_change_settings]
    )
    async def _starboard_channel_specific(
            self,
            ctx: discord.ApplicationContext,
            threshold: discord.Option(int, description="Minimum amount of emojis", required=True, min_value=1, max_value=99),
            emoji: discord.Option(str, description="The emoji to count", required=True),
            starboard_channel: discord.Option(str, description="The channel where starboard messages are sent", required=True),
            listen_channel: discord.Option(discord.TextChannel, description="The channel to listen in.", required=True)
    ):
        await ctx.defer()
        if not await check_permissions(ctx, listen_channel):
            return

        if not Parsing.check_emoji(emoji):
            await ctx.followup.send("Invalid Emoji!")

        await set_starboard(self.redis, starboard_channel.id, 2, threshold, emoji, ctx.guild.id, [str(listen_channel.id)])
        await ctx.followup.send(
            f"Starboard in {starboard_channel.mention} will now listen in the channel {listen_channel} for the {emoji} emoji."
        )

    @starboard.command(
        name="blacklist",
        description="Blacklist or unblacklist a channel from the starboard",
        checks=[pc.can_change_settings]
    )
    async def starboard_blacklist(self, ctx: discord.ApplicationContext, channel: discord.TextChannel, add: bool = True):
        """
        Add or remove a channel from the blacklist. Blacklisted channels will be ignored by the starboard.
        **Only usable by guild administrators or the bot owner.**
        If the add argument is *True* then the channel will be added to the blacklist.
        If the add argument is *False* then the channel will be removed from the blacklist.
        """
        await ctx.defer()
        key = f"starboard_blacklist:{ctx.guild.id}"
        if add:
            await self.redis.sadd(key, channel.id)
            await ctx.followup.send(f"Added {channel.mention} to the starboard blacklist.")
        else:
            try:
                await self.redis.srem(key, channel.id)
            # notify the user if the channel is not in the blacklist
            except aioredis.ResponseError:
                await ctx.followup.send(f"{channel.mention} is not in the starboard blacklist.")

            await ctx.followup.send(f"Removed {channel.mention} from the starboard blacklist.")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        self.bot.events_hour += 1
        self.bot.events_total += 1

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
            star_channel = await self.bot.fetch_channel(starboard_settings["channel_id"])
            channels = starboard_settings["channels"].split(";")
            reaction_emoji = str(payload.emoji)
        except KeyError:
            return

        # load the message into the internal cache
        message = await channel.fetch_message(payload.message_id)

        match mode:
            case 1 | 2:
                # make sure nothing in the starboard channel is starred and put onto the starboard
                if star_channel == channel or not starboard_settings:
                    return

                if mode == 2 and str(message.channel.id) not in channels:
                    return

                # check if the star emoji is the same as the starboard emoji
                if reaction_emoji == star_emoji:
                    # sort the reactions to get the reaction count for the star emoji
                    message.reactions.sort(key=lambda e: str(e) == str(payload.emoji), reverse=True)
                    count = message.reactions[0].count

                    # check if the count is greater than the threshold, else return
                    if not count >= threshold:
                        return

                    already_posted = await check_if_already_posted(message, star_channel, self.bot.user.id)

                    if not already_posted:
                        embed, file = await generate_embed(message, count, star_emoji, aiohttp_session=self.bot.aiohttp_session, return_file=True)
                        if file:
                            await star_channel.send(embed=embed, file=file)
                        else:
                            await star_channel.send(embed=embed)
                    else:
                        # update the starboard message
                        embed, _ = await generate_embed(message, count, star_emoji)
                        await already_posted.edit(embed=embed)
                else:
                    return
            case _:
                return


def setup(bot):
    bot.add_cog(StarBoard(bot))
