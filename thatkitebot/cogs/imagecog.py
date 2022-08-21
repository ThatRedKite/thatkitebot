#  Copyright (c) 2019-2022 ThatRedKite and contributors

import asyncio
import functools
import re
from concurrent.futures import ProcessPoolExecutor
from io import BytesIO
from typing import Optional, Union

import discord
from discord.ext import commands, bridge

from thatkitebot.backend import util, magik


async def get_image_url(message: discord.Message, video: bool = False, gifv: bool = False) -> Union[tuple[str, str], tuple[None, None]]:
    # check if the message has an attachment or embed of the type "image"
    if message.attachments:
        return message.attachments[0].url, message.attachments[0].content_type

    if not message.embeds:
        return None, None

    if message.embeds[0].type == "image":
        # if it does, return the embed's url
        return message.embeds[0].url, "image"
    # check if the message has an embed of the type "rich" and if it contains an image
    elif message.embeds[0].type == "rich" and message.embeds[0].image:
        # if it does, return the embed's url
        return message.embeds[0].image.url, "rich"
    # check if the message has a video if the :video: argument is true
    elif message.embeds[0].type == "video" and video:
        return message.embeds[0].url, "video"
    # check if the message has a gif if the :gifv: argument is true
    elif message.embeds[0].type == "gifv" and gifv:
        return message.embeds[0].url, "gifv"
    else:
        # if it doesn't, return None
        return None, None


class ImageStuff(commands.Cog, name="image commands"):
    """
    Image commands for the bot. Can be disabled by the bot owner or an admin.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sep = asyncio.Semaphore(12)
        self.pp = ProcessPoolExecutor(max_workers=4)
        self.td = bot.temp_dir  # temp directory
        self.dd = bot.data_dir  # data directory
        self.ll = asyncio.get_event_loop()
        self.session = self.bot.aiohttp_session
        self.tt = self.bot.tenor_token
        self.tenor_pattern = re.compile(r"^https://tenor.com\S+-(\d+)$")

    async def cog_command_error(self, ctx, error):
        await util.errormsg(ctx, error)

    async def cog_check(self, ctx) -> bool:
        is_enabled = await self.bot.redis.hget(ctx.guild.id, "IMAGE") == "TRUE" if ctx.guild else True
        can_attach = ctx.channel.permissions_for(ctx.author).attach_files
        can_embed = ctx.channel.permissions_for(ctx.author).embed_links
        return is_enabled and can_attach and can_embed

    async def cog_unload(self):
        # make sure to cancel all futures before unloading
        self.pp.shutdown(cancel_futures=True, wait=False)

    async def get_last_image(self, ctx, return_buffer=False) -> Union[BytesIO, None]:
        # search past 30 messages for suitable media content, only search messages with an attachment or embed
        # first, get a suitable message

        if ctx.message.reference:
            # fetch the message from the reference
            message = await ctx.fetch_message(ctx.message.reference.message_id)
            url, embed_type = await get_image_url(message)

        # check if the message has an attachment
        elif ctx.message.attachments or ctx.message.embeds:
            url, embed_type = await get_image_url(ctx.message)
        else:
            # iterate over the last 30 messages
            async for msg in ctx.channel.history(limit=30).filter(lambda m: m.attachments or m.embeds):
                # get the url of the image and break the loop if it's not None
                url, embed_type = await get_image_url(msg)
                if url:
                    break
                else:
                    continue

        # if the url is None, return None because there is no suitable image in the last 30 messages
        if not url:
            raise commands.BadArgument("No suitable image found.")

        # if the url is not None, download the image and return it
        async with self.session.get(url) as resp:
            # if return_buffer is True, return a BytesIO buffer of the image and seek to the beginning
            if return_buffer:
                buf = BytesIO(await resp.read())
                buf.seek(0)
                return buf
            # if return_buffer is False, return the image as a blob
            else:
                return await resp.read()

    async def image_worker(self, func, name, gif: bool = False):
        async with self.sep:
            try:
                # for some reason it never runs the function if you use an actual executor, so this is a temporary workaround
                b2, fn = await asyncio.wait_for(self.ll.run_in_executor(executor=None, func=func), timeout=30.0)
                #b2, fn = await asyncio.wait_for(self.ll.run_in_executor(self.pp, func), timeout=30.0)
            except asyncio.TimeoutError:
                e = await util.errormsg(msg="Processing timed out", embed_only=True)
                return None, None
            if fn < 0 and fn != -3:
                e = await util.errormsg(msg="The image should be smaller than 6000x6000 pixels", embed_only=True)
                return e, None
            elif fn == -3:
                e = await util.errormsg(msg="Selected color doesn't exist or is in the wrong format.", embed_only=True)
                return e, None

        embed = discord.Embed(title="Processed image")
        extension = 'png' if not gif else 'gif'
        embed.set_image(url=f"attachment://{name}.{extension}")
        file = discord.File(BytesIO(b2), filename=f"{name}.{extension}")
        return embed, file

    @commands.cooldown(3, 5, commands.BucketType.guild)
    @bridge.bridge_command(name="magik", aliases=["magic", "magick"], guild_ids=[759419755253465188])
    async def magik(self, ctx: commands.Context):
        # the GIF part is a lie btw
        """Applies some content aware scaling to an image. When the image is a GIF, it takes the first frame"""
        await ctx.defer()
        buf = await self.get_last_image(ctx, return_buffer=True)
        embed, file = await self.image_worker(functools.partial(magik.magik, buf=buf, fn=0), "magik")
        buf.close
        await ctx.respond(file=file, embed=embed)

    @commands.cooldown(3, 5, commands.BucketType.guild)
    @commands.command(aliases=["swirlmagik", "smagic", "swirlmagic"])
    async def smagik(self, ctx: commands.Context):
        """
        Applies some content aware and swirling scaling to an image.
        When the image is a GIF, it takes the first frame
        """
        buf = await self.get_last_image(ctx, return_buffer=True)
        async with ctx.channel.typing():
            embed, file = await self.image_worker(functools.partial(magik.swirlmagik, buf=buf, fn=1), "swirlmagik")
            buf.close()
        await ctx.send(file=file, embed=embed)

    @commands.cooldown(3, 10, commands.BucketType.channel)
    @commands.command()
    async def pfp(self, ctx, user: Optional[discord.Member] = None):
        """This sends someone's profile picture"""
        if user is None:
            user = ctx.author
        embed = discord.Embed(title=f"{user.name}'s profile picture", color=user.color)
        embed.set_image(url=user.avatar.url)
        await ctx.send(embed=embed)

    @commands.cooldown(3, 15, commands.BucketType.guild)
    @commands.command()
    async def deepfry(self, ctx: commands.Context):
        """'Deepfries' an image by oversaturating it and applying noise"""
        buf = await self.get_last_image(ctx, return_buffer=True)
        async with ctx.channel.typing():
            embed, file = await self.image_worker(functools.partial(magik.deepfry, buf=buf, fn=2), "deepfry")
            buf.close()
        await ctx.send(file=file, embed=embed)

    @commands.cooldown(3, 15, commands.BucketType.guild)
    @commands.command()
    async def wide(self, ctx: commands.Context):
        """Horizontally stretch an image"""
        buf = await self.get_last_image(ctx, return_buffer=True)
        async with ctx.channel.typing():
            embed, file = await self.image_worker(functools.partial(magik.wide, buf=buf, fn=3), "wide")
            buf.close()
        await ctx.send(file=file, embed=embed)

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["opacity"])
    async def opacify(self, ctx: commands.Context):
        """Remove the alpha channel and replace it with white"""
        buf = await self.get_last_image(ctx, return_buffer=True)
        async with ctx.channel.typing():
            embed, file = await self.image_worker(functools.partial(magik.opacify, buf=buf, fn=4), "opacify")
            buf.close()
        await ctx.send(file=file, embed=embed)

    @commands.cooldown(3, 10, commands.BucketType.user)
    @commands.command(aliases=["inflate"])
    async def explode(self, ctx: commands.Context):
        """Explodes an image"""
        buf = await self.get_last_image(ctx, return_buffer=True)
        async with ctx.channel.typing():
            embed, file = await self.image_worker(functools.partial(magik.explode, buf=buf, fn=5), "explode")
            buf.close()
        await ctx.send(file=file, embed=embed)

    @commands.cooldown(3, 10, commands.BucketType.user)
    @commands.command(aliases=["deflate"])
    async def implode(self, ctx: commands.Context):
        """Implodes an image"""
        buf = await self.get_last_image(ctx, return_buffer=True)
        async with ctx.channel.typing():
            embed, file = await self.image_worker(functools.partial(magik.implode, buf=buf, fn=6), "implode")
            buf.close()
        await ctx.send(file=file, embed=embed)

    @commands.cooldown(3, 10, commands.BucketType.user)
    @commands.command(aliases=["inverse", "anti"])
    async def invert(self, ctx: commands.Context):
        """Invert an image's colors"""
        buf = await self.get_last_image(ctx, return_buffer=True)
        async with ctx.channel.typing():
            embed, file = await self.image_worker(functools.partial(magik.invert, buf=buf, fn=7), "inverted")
            buf.close()
        await ctx.send(file=file, embed=embed)

    @commands.cooldown(3, 10, commands.BucketType.user)
    @commands.command()
    async def reduce(self, ctx: commands.Context):
        """Reduces an image's total colors"""
        buf = await self.get_last_image(ctx, return_buffer=True)
        async with ctx.channel.typing():
            embed, file = await self.image_worker(functools.partial(magik.reduce, buf=buf, fn=8), "reduced")
            buf.close()
        await ctx.send(file=file, embed=embed)

    @commands.cooldown(3, 10, commands.BucketType.user)
    @commands.command()
    async def swirl(self, ctx: commands.Context, degree: int = 60):
        """Swirl an image"""
        buf = await self.get_last_image(ctx, return_buffer=True)
        async with ctx.channel.typing():
            embed, file = await self.image_worker(functools.partial(magik.swirl, buf=buf, fn=9, angle=degree), "swirled")
            buf.close()
        await ctx.send(file=file, embed=embed)

    @commands.cooldown(3, 15, commands.BucketType.user)
    @commands.command()
    async def caption(self, ctx, *, text: str = ""):
        """
        Adds a caption to an image. You can add `color:` to the message to change text color using hex or decimal RGB values.
        Example: \n `caption funny color:ff2315` or  `caption funny color:255,123,22` or `caption funny color:firebrick`
        A full list of colors can be found here: https://imagemagick.org/script/color.php
        """
        buf = await self.get_last_image(ctx, return_buffer=True)
        async with ctx.channel.typing():
            embed, file = await self.image_worker(functools.partial(magik.caption, buf, 10, text, self.dd), "captioned")
            buf.close()
        await ctx.send(file=file, embed=embed)

    @commands.cooldown(5, 10, commands.BucketType.user)
    @commands.command()
    async def rotate(self, ctx: commands.Context, degree: int = 90):
        """Rotate an image clockwise 90 degrees by default, you can specify the degree value as an argument"""
        buf = await self.get_last_image(ctx, return_buffer=True)
        async with ctx.channel.typing():
            embed, file = await self.image_worker(functools.partial(magik.rotate, buf=buf, fn=11, angle=degree), "rotated")
            buf.close()
        await ctx.send(file=file, embed=embed)

    @commands.cooldown(5, 10, commands.BucketType.user)
    @commands.command(aliases=["bw", "blackwhite"])
    async def grey(self, ctx: commands.Context):
        """Make an image black and white"""
        buf = await self.get_last_image(ctx, return_buffer=True)
        async with ctx.channel.typing():
            embed, file = await self.image_worker(functools.partial(magik.black_white, buf=buf, fn=12), "black_and_white")
            buf.close()
        await ctx.send(file=file, embed=embed)

    @commands.cooldown(5, 10, commands.BucketType.user)
    @commands.command(aliases=["piss"])
    async def sepia(self, ctx: commands.Context, threshold: float = 0.8):
        """Add a sepia filter to an image"""
        buf = await self.get_last_image(ctx, return_buffer=True)
        async with ctx.channel.typing():
            embed, file = await self.image_worker(functools.partial(magik.make_sepia, buf=buf, fn=13, threshold=threshold), "sepia")
            buf.close()
        await ctx.send(file=file, embed=embed)

    @commands.cooldown(5, 10, commands.BucketType.user)
    @commands.command()
    async def polaroid(self, ctx: commands.Context):
        """Add a polaroid filter to an image"""
        buf = await self.get_last_image(ctx, return_buffer=True)
        async with ctx.channel.typing():
            embed, file = await self.image_worker(
                functools.partial(magik.make_polaroid, buf=buf, fn=14), "polaroid")
            buf.close()
        await ctx.send(file=file, embed=embed)

    @commands.cooldown(5, 10, commands.BucketType.user)
    @commands.command(aliases=["coal"])
    async def charcoal(self, ctx: commands.Context, radius: float = 1.5, sigma: float = 0.5):
        """Add a charcoal filter to an image, making it look like a charcoal drawing"""
        buf = await self.get_last_image(ctx, return_buffer=True)
        async with ctx.channel.typing():
            embed, file = await self.image_worker(
                functools.partial(magik.charcoal, buf=buf, fn=15, radius=radius, sigma=sigma), "charcoal")
            buf.close()
        await ctx.send(file=file, embed=embed)

    @commands.cooldown(5, 10, commands.BucketType.user)
    @commands.command()
    async def vignette(self, ctx: commands.Context, sigma: int = 3, x: int = 10, y: int = 10):
        """Tries to emulate old school 3d effect"""
        buf = await self.get_last_image(ctx, return_buffer=True)
        async with ctx.channel.typing():
            embed, file = await self.image_worker(
                functools.partial(magik.make_vignette, buf=buf, fn=16, sigma=sigma, x=x, y=y), "vignette")
            buf.close()
        await ctx.send(file=file, embed=embed)

    @commands.cooldown(5, 10, commands.BucketType.user)
    @commands.command(aliases=["bubble"])
    async def speech_bubble(self, ctx: commands.Context):
        """Create a speech bubble like those memes"""
        buf = await self.get_last_image(ctx, return_buffer=True)
        async with ctx.channel.typing():
            embed, file = await self.image_worker(
                functools.partial(magik.bubble, buf=buf, fn=17), "speech_bubble", gif=True)
            buf.close()
        await ctx.send(file=file, embed=embed)

    @commands.cooldown(5, 10, commands.BucketType.user)
    @commands.command(aliases=["scale"])
    async def resize(self, ctx: commands.Context, scale: float = 0.5):
        """Resizes an image to a set factor"""
        buf = await self.get_last_image(ctx, return_buffer=True)
        async with ctx.channel.typing():
            embed, file = await self.image_worker(
                functools.partial(magik.scale, buf=buf, fn=18, factor=scale), "resized")
            buf.close()
        await ctx.send(file=file, embed=embed)

    @commands.cooldown(5, 10, commands.BucketType.user)
    @commands.command()
    async def blur(self, ctx: commands.Context, radius: int = 0, sigma: int = 3):
        """Applies blur"""
        buf = await self.get_last_image(ctx, return_buffer=True)
        async with ctx.channel.typing():
            embed, file = await self.image_worker(
                functools.partial(magik.blur, buf=buf, fn=19, radius=radius, sigma=sigma), "blur")
            buf.close()
        await ctx.send(file=file, embed=embed)

    @commands.cooldown(5, 10, commands.BucketType.user)
    @commands.command(aliases=["ablur"])
    async def adaptive_blur(self, ctx: commands.Context, radius: int = 0, sigma: int = 3):
        """Applies blur, but tries to utilize edge detect for a better result"""
        buf = await self.get_last_image(ctx, return_buffer=True)
        async with ctx.channel.typing():
            embed, file = await self.image_worker(
                functools.partial(magik.adaptive_blur, buf=buf, fn=20, radius=radius, sigma=sigma), "adaptive_blur")
            buf.close()
        await ctx.send(file=file, embed=embed)

    @commands.cooldown(5, 10, commands.BucketType.user)
    @commands.command(aliases=["mblur"])
    async def motion_blur(self, ctx: commands.Context, radius: int = 0, sigma: int = 3, angle: int = -45):
        """Applies motion blur"""
        buf = await self.get_last_image(ctx, return_buffer=True)
        async with ctx.channel.typing():
            embed, file = await self.image_worker(
                functools.partial(magik.motion_blur, buf=buf, fn=21, radius=radius, sigma=sigma, angle=angle),
                "motion_blur")
            buf.close()
        await ctx.send(file=file, embed=embed)

    @commands.cooldown(5, 10, commands.BucketType.user)
    @commands.command()
    async def edge(self, ctx: commands.Context, radius: int = 1):
        """Returns a black and white image with edges in white and the rest in black"""
        buf = await self.get_last_image(ctx, return_buffer=True)
        async with ctx.channel.typing():
            embed, file = await self.image_worker(
                functools.partial(magik.edge, buf=buf, fn=22, radius=radius), "edge")
            buf.close()
        await ctx.send(file=file, embed=embed)

    @commands.cooldown(5, 10, commands.BucketType.user)
    @commands.command()
    async def emboss(self, ctx: commands.Context, radius: float = 3.0, sigma: float = 1.75):
        """Creates an embossed image"""
        buf = await self.get_last_image(ctx, return_buffer=True)
        async with ctx.channel.typing():
            embed, file = await self.image_worker(
                functools.partial(magik.emboss, buf=buf, fn=23, radius=radius, sigma=sigma), "emboss")
            buf.close()
        await ctx.send(file=file, embed=embed)

    @commands.cooldown(5, 10, commands.BucketType.user)
    @commands.command(aliases=["smooth"])
    async def kuwahara(self, ctx: commands.Context, radius: int = 1, sigma: float = 1.5):
        """Attempts to smooth the image while preserving edges"""
        buf = await self.get_last_image(ctx, return_buffer=True)
        async with ctx.channel.typing():
            embed, file = await self.image_worker(
                functools.partial(magik.kuwahara, buf=buf, fn=24, radius=radius, sigma=sigma), "kuwahara")
            buf.close()
        await ctx.send(file=file, embed=embed)

    @commands.cooldown(5, 10, commands.BucketType.user)
    @commands.command()
    async def shade(self, ctx: commands.Context, gray: bool = True, azimuth: float = 286.0, elevation: float = 45.0):
        """Attempts to smooth the image while preserving edges"""
        buf = await self.get_last_image(ctx, return_buffer=True)
        async with ctx.channel.typing():
            embed, file = await self.image_worker(
                functools.partial(magik.shade, buf=buf, fn=25, gray=gray, azimuth=azimuth, elevation=elevation),
                "shade")
            buf.close()
        await ctx.send(file=file, embed=embed)


def setup(bot):
    bot.add_cog(ImageStuff(bot))
