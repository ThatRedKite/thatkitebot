# Copyright (c) 2019-2021 ThatRedKite and contributors
import asyncio
import typing
import re
from io import BytesIO

import aioredis
import imagehash
import discord
from discord.ext import commands
from PIL import Image as PILImage

from thatkitebot.cogs.settings import can_change_settings
from thatkitebot.backend.util import errormsg

tenor_pattern = re.compile(r"^https://tenor.com\S+-(\d+)$")
otherpattern = re.compile(r"(^https?://\S+.(?i)(png|webp|gif|jpe?g))")


def hasher(data):
    """
    Returns a hash of the image data.
    """
    pil_image = PILImage.open(BytesIO(data))
    return str(imagehash.phash(pil_image, hash_size=16))


class RepostCog(commands.Cog, name="Repost Commands"):
    """
    Repost commands.
    """
    def __init__(self, bot):
        self.bot = bot
        self.aiohttp = bot.aiohttp_session
        self.settings_redis: aioredis.Redis = bot.redis
        self.repost_redis: aioredis.Redis = bot.redis_repost
        self.tt = bot.tenor_token

    async def get_tenor_image(self, url, token):
        """
        Downloads a tenor gif and returns the hash of the image.
        """
        # define the header and the payload:
        tenor = tenor_pattern.findall(url)
        if not tenor:
            return
        headers = {"User-Agent": "ThatKiteBot/3.7", "content-type": "application/json"}
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
        return await self.settings_redis.hget(ctx.guild.id, "REPOST") == "TRUE"

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
        async for h in self.repost_redis.scan_iter("*"):
            attrs = await self.repost_redis.hgetall(h)
            yield (imagehash.hex_to_hash(h.split(":")[1]) - imagehash.hex_to_hash(imghash)), h, attrs

    @commands.group(aliases=["repc", "repostchannel"])
    async def repost_channel(self, ctx: commands.Context):
        """
        This is a command group for commands related adding and removing repost channels
        """
        if not ctx.subcommand_passed:
            # if no subcommand was passed check if the channel id is in the list of repost channels
            not_enabled_string = "not " if not await self.channel_is_enabled(ctx.channel) else ""
            await ctx.send(f"{ctx.channel.mention} is {not_enabled_string}enabled for repost detection.")

    @commands.check(can_change_settings)
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

    @commands.check(can_change_settings)
    @repost_channel.command(name="remove", aliases=["rm"])
    async def _remove(self, ctx, channel: typing.Optional[discord.TextChannel]):
        """
        Remove a channel from the list of repost-activated channels.
        Requires Administrator permissions. If no channel is specified, the current channel is used.
        """
        if not channel:
            channel = ctx.channel
        # remove the current channel from the list of repost channels
        await self.settings_redis.srem("REPOST_CHANNELS", channel.id)
        await ctx.send(f"{channel.mention} has been removed from the repost-activated channels.")

    @commands.command()
    async def repost(self, ctx, *, message: typing.Optional[discord.Message]):
        # set some default values
        if ctx.message.reference:
            message_id = ctx.message.reference.message_id
            channel_id = ctx.message.reference.channel_id
        else:
            message_id = message.id
            channel_id = message.channel.id

        # load the message from the discord api
        channel = await self.bot.fetch_channel(channel_id)
        message = await channel.fetch_message(message_id)
        # check if the message is a repost
        async for imghash in self.extract_imagehash(message):
            repost = False
            try:
                async for distance, h, attrs in self.check_distance(imghash):
                    if distance < 20 and (jump_url := attrs.get("jump_url")) != message.jump_url:
                        repost = True
                        repost_count = attrs.get("repost_count", 1)  # get the repost count, default to 1 if not set
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
                await ctx.send("This message is not an image.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not await self.channel_is_enabled(message.channel) or message.author.bot and message.guild:
            return  # return, if the channel is not enabled or the message is from a bot and not a DM

        if not message.embeds and not message.attachments:
            return  # return if the message does not contain an image

        async for image_hash in self.extract_imagehash(message):
            repost = False

            pipe = self.repost_redis.pipeline()
            async for distance, key, attrs in self.check_distance(image_hash):
                # if the distance is less than 20, it's a repost
                if distance <= 20:
                    jump_url = attrs["jump_url"]
                    # extract the guild id from the jump url
                    guild_id = int(jump_url.split("/")[4])
                    channel_id = int(jump_url.split("/")[5])
                    # set the repost flag to true if the guild id and channel id
                    # match the current message's guild id and channel id
                    repost = True if message.guild.id == guild_id and message.channel.id == channel_id else False
                    break

            if repost:
                await message.add_reaction("♻️")  # add the repost reaction
                await pipe.hincrby(key, "repost_count", 1)  # increment the repost count
            else:
                # the message does not appear to be a repost, let's add it to the database
                await pipe.hmset(f"{message.id}:{image_hash}", {"jump_url": message.jump_url, "repost_count": 0})

            await pipe.execute()  # execute the pipeline to commit the changes
            await pipe.close()  # close the pipeline


def setup(bot):
    bot.add_cog(RepostCog(bot))
