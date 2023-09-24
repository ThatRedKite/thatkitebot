#  Copyright (c) 2019-2023 ThatRedKite and contributors

import asyncio
import typing
import re

import imagehash
import discord

from redis import asyncio as aioredis
from discord.ext import commands

from thatkitebot.base.image_stuff import hasher, download_image, get_image_urls
from thatkitebot.base.util import ids_from_link
from thatkitebot.tkb_redis.settings import RedisFlags
from thatkitebot.tkb_redis import cache as ca
from thatkitebot.base.util import PermissonChecks as pc


tenor_pattern = re.compile(r"^https://tenor.com\S+-(\d+)$")
otherpattern = re.compile(r"(^https?://\S+.(?i)(png|webp|gif|jpe?g))")


class RepostCog(commands.Cog, name="Repost Commands"):
    """
    Repost commands.
    """
    def __init__(self, bot):
        self.bot = bot
        self.aiohttp = bot.aiohttp_session

        self.redis = bot.redis

        self.settings_redis: aioredis.Redis = bot.redis
        self.repost_redis: aioredis.Redis = bot.redis_repost
        self.cache_redis: aioredis.Redis = bot.redis_cache

        self.tt = bot.tenor_token

        self.repost_database_lock = asyncio.Lock()

    async def get_tenor_image(self, url, token):
        """
        Downloads a tenor gif and returns the hash of the image.
        """
        # define the header and the payload:
        tenor = tenor_pattern.findall(url)
        if not tenor:
            return
        headers = {"User-Agent": "ThatKiteBot/4.0", "content-type": "application/json"}
        payload = {"key": token, "ids": int(tenor[0]), "media_filter": "minimal"}

        async with self.aiohttp.get(url="https://api.tenor.com/v1/gifs", params=payload, headers=headers) as r:
            gifs = await r.json()
            url = gifs["results"][0]["media"][0]["gif"]["url"]  # dictionary magic to get the url of the gif

        async with self.aiohttp.get(url) as r2:
            return hasher(await r2.read())

    async def channel_is_enabled(self, channel):
        """
        Checks if the channel is enabled for repost detection.
        """
        return await self.settings_redis.sismember("REPOST_CHANNELS", channel.id)

    async def cog_check(self, ctx):
        return await RedisFlags.get_guild_flag(self.redis, ctx.guild.id, RedisFlags.REPOST)

    # this is kinda dumb but i guess it works :)
    async def hash_from_url(self, urls: list[str]):
        for url in urls:
            image_data = await download_image(self.aiohttp, url)
            yield hasher(image_data)

    async def extract_imagehash(self, message):
        """
        Extracts the image hash from a message's attachments or embeds.
        Yields the imagehash
        """
        if message.attachments:
            # if the file was uploaded directly, get the image data from the attachment directly
            for attachment in message.attachments:
                yield hasher(await attachment.read())

        elif message.embeds:
            # links to images or GIFs are embedded in the message
            for embed in message.embeds:
                match embed.type:
                    case "rich":
                        yield None
                    case "image":
                        async with self.aiohttp.get(embed.url) as r:  # download the image
                            yield hasher(await r.read())  # generate the hash
                    case "gifv":
                        #  this feature *requires* a tenor API Token!
                        if self.tt:
                            # download and hash the teno r gif
                            yield await self.get_tenor_image(message.content, self.tt) or None
                    case "video":
                        yield None
        else:
            yield None

    async def check_distance(self, imghash):
        """
        Checks the distance between the image hashes.
        """
        image_hash_to_check = imagehash.hex_to_hash(imghash)

        async for hash_key in self.repost_redis.scan_iter("*"):
            # turns out calling hgetall on *every* entry is a **really** bad idea
            # this is just a really stupid hack that will make this *horrible* code suck slightly less
            #attrs = await self.repost_redis.hgetall(h)

            image_hash_original = imagehash.hex_to_hash(hash_key.split(":")[1])

            distance = image_hash_original - image_hash_to_check

            yield distance, hash_key

    @commands.group(aliases=["repc", "repostchannel"])
    async def repost_channel(self, ctx: commands.Context):
        """
        This is a command group for commands related adding and removing repost channels
        """
        if not ctx.subcommand_passed:
            # if no subcommand was passed check if the channel id is in the list of repost channels
            not_enabled_string = "not " if not await self.channel_is_enabled(ctx.channel) else ""
            await ctx.send(f"{ctx.channel.mention} is {not_enabled_string}enabled for repost detection.")

    @commands.check(pc.can_change_settings)
    @repost_channel.command(name="add")
    async def _add(self, ctx, channel: typing.Optional[discord.TextChannel]):
        """
        Add a channel to the list of repost-activated channels.
        Requires Administrator permissions. If no channel is specified, the current channel is used.
        """
        if not channel:
            channel = ctx.channel

        # add the current channel to the list of repost channels
        await self.settings_redis.sadd("REPOST_CHANNELS", channel.id)
        await ctx.send(f"{channel.mention} has been added to the repost-activated channels.")

    @commands.check(pc.can_change_settings)
    @repost_channel.command(name="remove", aliases=["rm"])
    async def _remove(self, ctx, channel: typing.Optional[discord.TextChannel]):
        """*/+-
        Remove a channel from the list of repost-activated channels.
        Requires Administrator permissions. If no channel is specified, the current channel is used.
        """
        if not channel:
            channel = ctx.channel
        # remove the current channel from the list of repost channels
        await self.settings_redis.srem("REPOST_CHANNELS", channel.id)
        await ctx.send(f"{channel.mention} has been removed from the repost-activated channels.")

    @commands.guild_only()
    @commands.group(name="repost")
    async def repost(self, ctx: commands.Context, *, message: typing.Optional[discord.Message]):
        if not ctx.subcommand_passed:
            # set some default values
            if ctx.message.reference:
                message_id = ctx.message.reference.message_id
                channel_id = ctx.message.reference.channel_id
            else:
                if not message:
                    await ctx.send("You did not specify any message. Please respond to a message or provide as a command argument.")
                message_id = message.id
                channel_id = message.channel.id

            # load the message from the discord api

            urls = []
            # todo see if tenor stuff works
            try:
                # try to get the message from the cache to get the attachment urls
                cache = ca.RedisCache(self.cache_redis, self.bot, auto_exec=True)
                ids, message_json = await cache.get_message(message_id, ctx.guild.id)
                urls = [url for url in message_json["urls"]]

            except ca.CacheInvalidMessageException:
                # oh no, the message is not cached, time to use the Discord API
                channel = await self.bot.fetch_channel(channel_id)
                message = await channel.fetch_message(message_id)
                urls = await get_image_urls(message, video=False, gifv=True)

            async with self.repost_database_lock:
                async for imghash in self.hash_from_url(urls):
                    try:
                        repost = False
                        async for distance, hash_key in self.check_distance(imghash):
                            if distance < 20:
                                repost = True
                                jump_url, repost_count = await self.repost_redis.hmget(
                                    hash_key,
                                    ["jump_url", "repost_count"]
                                )

                                ms = "s" if int(repost_count) > 1 else ""  # pluralize the word "time"

                                embed = discord.Embed(
                                    title="Repost Detected",
                                    description=f"This message is a repost of [this message]({jump_url}) it has been reposted {repost_count} time{ms}.",
                                )
                                await ctx.send(embed=embed)
                                break
                            else:
                                repost = False
                        if not repost:
                            # the message seems to be the original
                            await ctx.send("This seems to be the original image.")
                    except TypeError:
                        # the message is not an image
                        await ctx.send("There doesn't seem to be any images in this message.")

        else:
            return

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        self.bot.events_hour += 1
        self.bot.events_total += 1
        if not message.embeds and not message.attachments:
            return  # return if the message does not contain an image

        if not await self.channel_is_enabled(message.channel) or message.author.bot and message.guild:
            return  # return, if the channel is not enabled or the message is from a bot and not a DM

        repost = False
        hash_key = None
        pipe = self.repost_redis.pipeline()
        async with self.repost_database_lock:
            # iterate over every image in the message and get the image hash for them
            async for image_hash in self.extract_imagehash(message):
                # first check for a direct match
                async for scan_key in self.repost_redis.scan_iter(f"*:{image_hash}"):
                    # get the jump url
                    jump_url = await self.repost_redis.hget(scan_key, "jump_url")

                    # turn the jump url into IDs
                    message_id, channel_id, guild_id = ids_from_link(jump_url)

                    repost = (int(message.guild.id) == int(guild_id) and int(message.channel.id) == int(channel_id))
                    if repost:
                        # direct match found, break loop and bypass scanning for similar images
                        hash_key = scan_key
                        break

                if not repost:
                    async for distance, hash_key in self.check_distance(image_hash):
                        #print(distance)
                        # if the distance is less than 20, it's a repost
                        if distance <= 20:
                            jump_url = await self.repost_redis.hget(hash_key, "jump_url")
                            message_id, channel_id, guild_id = ids_from_link(jump_url)
                            repost = (int(message.guild.id) == int(guild_id) and int(message.channel.id) == int(channel_id))
                            break

                if repost:
                    await message.add_reaction("♻️")  # add the repost reaction
                    await self.repost_redis.hincrby(hash_key, "repost_count", 1)  # increment the repost count
                else:
                    # the message does not appear to be a repost, let's add it to the database
                    await pipe.hset(key := f"{message.id}:{image_hash}", "jump_url", message.jump_url)
                    await pipe.hset(key, "repost_count", str(0))

            await pipe.execute()  # execute the pipeline to commit the changes


def setup(bot):
    bot.add_cog(RepostCog(bot))
