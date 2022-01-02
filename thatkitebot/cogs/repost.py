# Copyright (c) 2019-2021 ThatRedKite and contributors

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

tenorpattern = re.compile(r"^https://tenor.com\S+-(\d+)$")
otherpattern = re.compile(r"(^https?://\S+.(?i)(png|webp|gif|jpe?g))")


def hasher(data):
    pil_image = PILImage.open(BytesIO(data))
    return str(imagehash.phash(pil_image, hash_size=16))


class RepostCog(commands.Cog, name="Repost Commands"):
    def __init__(self, bot):
        self.bot = bot
        self.aiohttp = bot.aiohttp_session
        self.settings_redis: aioredis.Redis = bot.redis
        self.repost_redis: aioredis.Redis = bot.redis_repost
        self.tt = bot.tenortoken

    async def get_tenor_image(self, url, token):
        # define the header and the payload:
        tenor = tenorpattern.findall(url)
        if not tenor:
            return
        headers = {"User-Agent": "ThatKiteBot/3.4", "content-type": "application/json"}
        payload = {"key": token, "ids": int(tenor[0]), "media_filter": "minimal"}

        async with self.aiohttp.get(url="https://api.tenor.com/v1/gifs", params=payload, headers=headers) as r:
            gifs = await r.json()
            url = gifs["results"][0]["media"][0]["gif"]["url"]  # dictionary magic to get the url of the gif

        async with self.aiohttp.get(url) as r2:
            return hasher(await r2.read())

    async def channel_is_enabled(self, channel):
        return await self.settings_redis.sismember("REPOST_CHANNELS", channel.id)

    async def cog_check(self, ctx):
        return await self.settings_redis.hget(ctx.guild.id, "REPOST") == "TRUE"

    async def extract_imagehash(self, message):
        if message.attachments:
            # if the file was uploaded directly, get the image data from the attachment directly
            for attachment in message.attachments:
                return hasher(await attachment.read())

        elif message.embeds:
            # links to images or GIFs are
            for embed in message.embeds:
                match embed.type:
                    case "rich":
                        return None  # rich embeds do not contain any images that could be useful; just return
                    case "image":
                        async with self.aiohttp.get(embed.url) as r:  # download the image
                            return hasher(await r.read())  # generate the hash
                    case "gifv":
                        #  this feature *requires* a tenor API Token!
                        if self.tt:
                            # download and hash the tenor gif
                            return await self.get_tenor_image(message.content, self.tt)
                    case "video":
                        return None# video support might be added soon
        else:
            return None

    async def check_distance(self, imghash, return_hash = False):
        imghash = imagehash.hex_to_hash(imghash)
        hashes = [key async for key in self.repost_redis.scan_iter("*")] or None  # get all hashes
        if not hashes:
            return False
        distances = [(imagehash.hex_to_hash(h.split(":")[1]) - imghash) <= 20 for h in hashes]
        if return_hash:
            return hashes[distances.index(True)] or False
        else:
            return any(distances)   # return if any hash is too similar

    @commands.group()
    async def repost(self, ctx: commands.Context):
        """
        This is a command group for commands related to repost detection.
        """
        if not ctx.subcommand_passed:
            pass

    @commands.check(can_change_settings)
    @repost.command(name="add")
    async def _add(self, ctx, channel: typing.Optional[discord.TextChannel]):
        """
        Add a channel to the list of repost-activated channels.
        Requires Administrator permissions.
        """
        if not channel:
            channel = ctx.channel
        # add the curent channel to the list of repost channels
        await self.settings_redis.sadd("REPOST_CHANNELS", channel.id)

    @commands.check(can_change_settings)
    @repost.command(name="remove", aliases=["rm"])
    async def _remove(self, ctx, channel: typing.Optional[discord.TextChannel]):
        """
        Remove a channel from the list of repost-activated channels.
        Requires Administrator permissions.
        """
        if not channel:
            channel = ctx.channel
        # remove the curent channel from the list of repost channels
        await self.settings_redis.srem("REPOST_CHANNELS", channel.id)

    @repost.command(name="check")
    async def _check(self, ctx: commands.Context, message: discord.Message = None):
        """
        Check if a message is a message is a repost.
        Simply reply to a message or use its id or message link as a parameter.
        """
        if not await self.channel_is_enabled(ctx.channel):
            return

        if not message and ctx.message.reference:
            message_id = ctx.message.reference.message_id

        elif message and not ctx.message.reference:
            message_id = message.id

        else:
            await errormsg(ctx, "You need to reply to a message or specify its id!")
            return

        # forefully load the message because discord.py's message cache cannot be trusted (it sucks) and get the hash
        try:
            imghash = await self.extract_imagehash(await ctx.channel.fetch_message(message_id))
            original_key = await self.check_distance(imghash, return_hash=True)
            if original_key:
                original = await self.repost_redis.hget(str(original_key), "jump_url")
                embed = discord.Embed(
                    title="Repost Found!",
                    description=f"Press [here]({original}) to jump to the original message.")
                await ctx.send(embed=embed)
            else:
                await errormsg(ctx, "No repost was found!")
        except TypeError:
            await errormsg(ctx, "No repost was found!")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not await self.channel_is_enabled(message.channel) or message.author.bot:
            return
        imghash = await self.extract_imagehash(message)
        # check if the hash already exists or is close enough to another hash
        # TODO: the repost counter has yet to be implemented
        if imghash and (await self.repost_redis.exists(imghash) or await self.check_distance(imghash)):
            await message.add_reaction("♻️")  # add repost reaction
            # await self.repost_redis.hincrby(f"{message.id}:{imghash}", "repost_counter", 1)  # increment repost counter

        elif not imghash:
            return

        else:
            mapping_dict = dict(repost_counter=0, jump_url=message.jump_url)  # create initial values
            # add the image hash to the database
            await self.repost_redis.hset(f"{message.id}:{imghash}", mapping=mapping_dict)


def setup(bot):
    bot.add_cog(RepostCog(bot))
