#  Copyright (c) 2019-2023 ThatRedKite and contributors

import functools
import re
import asyncio
from typing import Union
from io import BytesIO

import discord
import imagehash
import aiohttp

from discord.ext import commands
from PIL import Image as PILImage
from wand.image import Image as WandImage
from wand.color import Color
from wand.font import Font

from .exceptions import *

def hasher(data):
    """
    Returns a hash of the image data.
    """
    pil_image = PILImage.open(BytesIO(data))
    return str(imagehash.phash(pil_image, hash_size=16))

async def download_image(session: aiohttp.ClientSession, url: str):
    """
    Downloads an image from a given URL. Deprecated.
    """
    async with session.get(url) as r:
        return await r.read()

async def get_last_image(ctx, aiohttp_session: aiohttp.ClientSession, return_buffer=False) -> Union[
    BytesIO, bytes, None]:
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
    async with aiohttp_session.get(url) as resp:
        # if return_buffer is True, return a BytesIO buffer of the image and seek to the beginning
        if return_buffer:
            buf = BytesIO(await resp.read())
            buf.seek(0)
            return buf
        # if return_buffer is False, return the image as a blob
        else:
            return await resp.read()

async def get_image_url(message: discord.Message, video: bool = False, gifv: bool = False) -> Union[
    tuple[str, str], tuple[None, None]]:
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

async def get_image_urls(message: discord.Message, video: bool = False, gifv: bool = False) -> list[str]:
    # check if the message has an attachment or embed of the type "image"
    if message.attachments:
        return [attachment.url for attachment in message.attachments]

    if not message.embeds:
        raise NoImageFoundException

    embed_urls = []
    for embed in message.embeds:
        if embed.type == "image":
            # if it does, return the embed's url
            embed_urls.append(embed.url)
            continue
        # check if the message has an embed of the type "rich" and if it contains an image
        elif embed.type == "rich" and embed.image:
            embed_urls.append(embed.image.url)
            continue
        # check if the message has a video if the :video: argument is true
        elif embed.type == "video" and video:
            embed_urls.append(embed.url)
        # check if the message has a gif if the :gifv: argument is true
        elif embed.type == "gifv" and gifv:
            embed_urls.append(embed.url)
        else:
            # if it doesn't, return None
            raise NoImageFoundException

    return embed_urls

def get_embed_urls(message: discord.Message, video_enabled: bool = False, gifv: bool = False) -> (str | None, str | None):
    """
    clone of :get_image_urls but with different output format: [(url, embed_type), ...]
    """
    if message.attachments:
        for attachment in message.attachments:
            content_type = attachment.content_type
            if "image" in content_type:
                yield attachment.url, "image"

            elif "video" in content_type:
                yield attachment.url, "video"

    if not message.embeds:
        yield None, None
        return

    for embed in message.embeds:
        if embed.type == "image":
            # if it does, return the embed's url
            yield embed.url, "image"
            continue

        # check if the message has an embed of the type "rich" and if it contains an image
        elif embed.type == "rich" and embed.image:
            yield embed.image.url, "image"
            continue

        # check if the message has a video if the :video: argument is true
        elif embed.type == "video" and video_enabled:

            # --- special cases for different websites ---

            if embed.provider and embed.provider.name == "YouTube":
                # special case for youtube, ignore any videos, return video thumbnail instead
                yield embed.thumbnail.url, "image"
                continue


            yield embed.video.url, "video"
            continue

        # embeds where a thumbnail (if present) will be returned
        elif embed.type in ["link", "article"] and embed.thumbnail:
            yield embed.thumbnail.url, "image"
            continue

        # check if the message has a gif if the :gifv: argument is true
        elif embed.type == "gifv" and gifv:
            yield embed.url, "image"
            continue

        else:
            # if it doesn't, stop the generator
            yield None, None
            return
        
    return


class ImageFunction:
    def __init__(self, buffer: BytesIO, fn: int, loop: asyncio.AbstractEventLoop):
        buffer.seek(0)
        self.loop = loop
        self.image = WandImage(file=buffer)

        if self.image.height >= 6000 or self.image.height >= 6000:
            self.image.destroy()
            raise ImageTooLargeException

        self.fn = fn

    async def image_worker(self, func, name="_", gif: bool = False, does_return=False):
        if not does_return:
            # for some reason it never runs the function if you use an actual executor
            # so this is a temporary workaround
            try:
                await asyncio.wait_for(self.loop.run_in_executor(executor=None, func=func), timeout=30.0)
            except asyncio.TimeoutError:
                self.image.destroy()
                return
        else:
            try:
                b2, fn = await asyncio.wait_for(self.loop.run_in_executor(None, func), timeout=30.0)
            except asyncio.TimeoutError:
                self.image.destroy()
                return

            # generate the embed and file object
            embed = discord.Embed(title="Processed image")
            extension = 'png' if not gif else 'gif'
            embed.set_image(url=f"attachment://{name}.{extension}")
            with BytesIO(b2) as buf:
                file = discord.File(buf, filename=f"{name}.{extension}")
            return embed, file

    async def make_blob_close(self, name: str = "image", gif=False):
        return await self.image_worker(self._make_blob_close, name=f"{name}_{self.__hash__()}", does_return=True, gif=gif)

    def _make_blob_close(self) -> (bytes, int):
        self.image.format = "png"
        b = self.image.make_blob()
        self.image.destroy()
        return b, self.fn

    async def make_blob(self, name: str = "image"):
        return await self.image_worker(self._make_blob, name=f"{name}_{self.__hash__()}", does_return=True)

    def _make_blob(self) -> (bytes, int):
        self.image.format = "png"
        b = self.image.make_blob()
        return b, self.fn

    def close(self):
        self.image.destroy()

    async def magik(self):
        await self.image_worker(self._magik)

    def _magik(self):
        self.image.sample(width=int(self.image.width * 0.5), height=int(self.image.height * 0.5))
        self.image.liquid_rescale(width=int(self.image.width / 2), height=int(self.image.height / 1.5), delta_x=1,
                                  rigidity=0)
        self.image.liquid_rescale(width=int(self.image.width * 2), height=int(self.image.height * 1.5), delta_x=2,
                                  rigidity=0)
        self.image.sample(width=int(self.image.width * 2), height=int(self.image.height * 2))

    async def swirlmagik(self, angle: float):
        await self.image_worker(functools.partial(self._swirlmagik, angle))

    def _swirlmagik(self, angle):
        self.image.swirl(angle)
        self._magik()
        self.image.swirl(-angle)

    async def swirl(self, angle: float):
        await self.image_worker(functools.partial(self._swirl, angle))

    def _swirl(self, angle: int = -60):
        self.image.swirl(degree=angle)

    async def invert(self):
        await self.image_worker(self._invert)

    def _invert(self):
        self.image.negate()

    async def implode(self, factor):
        await self.image_worker(functools.partial(self._implode, factor))

    def _implode(self, factor):
        self.image.implode(factor)

    async def opacify(self):
        await self.image_worker(self._opacify)

    def _opacify(self):
        self.image.alpha_channel = 'remove'
        self.image.background_color = Color('white')

    async def explode(self, factor):
        await self.image_worker(functools.partial(self._implode, -factor))

    async def reduce(self):
        await self.image_worker(self._reduce)

    def _reduce(self):
        self.image.posterize(levels=2)

    async def caption(self, text, path):
        await self.image_worker(functools.partial(self._caption, text, path))

    def _caption(self, ct, path):
        color_alias = {
            'piss': '#f9fc12',
            'cum': '#ededd5',
            'pickle': '#12a612',
            'white': '#ffffff',
        }
        in_str = str(ct)
        # find any emotes in the text
        x = re.findall(r'[<]:\w{2,}:\d{15,}[>]', in_str)
        for n in x: in_str = in_str.replace(str(n), re.findall(r':\w{2,}:', n)[0])
        # find any parameters in the command
        color = 'white'
        x = re.findall(r'color:\d{1,3},\d{1,3},\d{1,3}', in_str)
        if len(x) > 0:
            color = x[0].lower().replace('color:', 'rgb(') + ')'
            in_str = in_str.replace(x[0], '')
        x = re.findall(r'color:(?:\d{2}|[0-9A-Fa-f]{2}){3}', in_str)
        if len(x) > 0:
            color = x[0].lower().replace('color:', '#')
            in_str = in_str.replace(x[0], '')
        x = re.findall(r'color:\w{3,30}', in_str)
        if len(x) > 0:
            color = x[0].lower().replace('color:', '')
            in_str = in_str.replace(x[0], '').rstrip()
            if color in color_alias:
                color = color_alias[color]

        # Calculate image parameters for the text to wrap and fit.
        txt_top = int(0.70 * self.image.height)  # add text to the bottom 25% of the image
        txt_left = int(0.10 * self.image.width)  # leave 10 % the image from the left
        txt_width = self.image.width - (
                txt_left * 2)  # total width - 10% * 2 will leave 10% of with on the right side as well
        txt_height = self.image.height - txt_top  # use the whole 15% for text
        stroke_width = (txt_height * txt_width) / (10000 + (2500 * len(in_str)))
        if stroke_width < 1.5 or color != 'white':
            font = Font(path + 'OpenSansEmoji.ttf', color=color)
        else:
            font = Font(path + 'OpenSansEmoji.ttf', color=color, stroke_color='black', stroke_width=stroke_width)
        self.image.caption(in_str, left=txt_left, top=txt_top, width=txt_width, height=txt_height, font=font,
                           gravity='center')

    async def wide(self):
        await self.image_worker(self._wide)

    def _wide(self):
        self.image.resize(width=int(self.image.width * 3.3), height=int(self.image.height / 1.8))
        self.image.crop(left=int(self.image.width / 4), top=1, right=(self.image.width - (int(self.image.width / 4))),
                        bottom=self.image.height)

    async def deepfry(self):
        await self.image_worker(self._deepfry)

    def _deepfry(self):
        self.image.modulate(saturation=600.00)
        self.image.noise('gaussian', attenuate=0.1)

    async def rotate(self, angle: int = 90):
        await self.image_worker(functools.partial(self._rotate, angle))

    def _rotate(self, angle: int = 90):
        self.image.rotate(degree=angle)

    async def black_white(self):
        await self.image_worker(self._black_white)

    def _black_white(self):
        self.image.transform_colorspace('gray')

    async def sepia(self, threshold: float = 0.8):
        await self.image_worker(functools.partial(self._sepia, threshold))

    def _sepia(self, threshold: float = 0.8):
        self.image.sepia_tone(threshold)

    async def polaroid(self):
        await self.image_worker(self._polaroid)

    def _polaroid(self):
        self.image.polaroid()

    async def charcoal(self, radius: float = 1.5, sigma: float = 0.5):
        await self.image_worker(functools.partial(self._charcoal, radius, sigma))

    def _charcoal(self, radius: float = 1.5, sigma: float = 0.5):
        self.image.charcoal(radius, sigma)

    async def make_vignette(self, sigma: int = 3, x: int = 10, y: int = 10):
        await self.image_worker(functools.partial(self._make_vignette, sigma, x, y))

    def _make_vignette(self, sigma: int = 3, x: int = 10, y: int = 10):
        self.image.vignette(sigma, x, y)

    async def bubble(self):
        await self.image_worker(self._bubble)

    def _bubble(self):
        # grab the template files stored in the data directory
        negative = '/app/data/static-resources/bubble_negative.png'
        outline = '/app/data/static-resources/bubble_outline.png'

        # load in all the images
        with (
            WandImage(filename=negative) as neg,
            WandImage(filename=outline) as out
        ):
            # ensure the input image does not exceed 1024 in either direction
            if self.image.width > 1024 or self.image.height > 1024:
                aspect_ratio = self.image.width / self.image.height
                # and yes kite, the elif won't work here as we rely on it to make sure both sides are within specs
                if self.image.width > 1024:
                    self.image.resize(width=1024, height=int(1024 / aspect_ratio))
                if self.image.height > 1024:
                    self.image.resize(width=int(1024 * aspect_ratio), height=1024)
            # resize the images accordingly
            neg.resize(width=self.image.width, height=self.image.height)
            out.resize(width=self.image.width, height=self.image.height)
            # compose the input image onto the negative
            neg.composite_channel(channel='default_channels', image=self.image, operator='src_in')
            # compose the outline image onto the composed negative
            neg.composite_channel(channel='default_channels', image=out, operator='over')
            # create self.image binary output for the upload
            self.image = neg.clone()
            neg.destroy()
            out.destroy()
            del neg
            del out

    async def scale(self, factor: float = 0.5):
        await self.image_worker(functools.partial(self._scale, factor))

    def _scale(self, factor: float = 0.5):
        # input protection
        if 1 > factor < 0.1:
            factor = 0.5
        self.image.resize(width=int(self.image.width * factor), height=int(self.image.height * factor))

    async def blur(self, radius: int = 0, sigma: int = 3):
        await self.image_worker(functools.partial(self._blur, radius, sigma))

    def _blur(self, radius: int = 0, sigma: int = 3):
        self.image.blur(radius, sigma)

    async def adaptive_blur(self, radius: int = 8, sigma: int = 4):
        await self.image_worker(functools.partial(self._adaptive_blur, radius, sigma))

    def _adaptive_blur(self, radius: int = 8, sigma: int = 4):
        self.image.adaptive_blur(radius, sigma)

    async def motion_blur(self, radius: int = 8, sigma: int = 4, angle: int = -45):
        await self.image_worker(functools.partial(self._motion_blur, radius, sigma, angle))

    def _motion_blur(self, radius: int = 8, sigma: int = 4, angle: int = -45):
        self.image.motion_blur(radius, sigma, angle)

    async def edge(self, radius: int = 1):
        await self.image_worker(functools.partial(self._edge, radius))

    def _edge(self, radius: int = 1):
        self.image.transform_colorspace('gray')
        self.image.edge(radius)

    async def emboss(self, radius: float = 3.0, sigma: float = 1.75):
        await self.image_worker(functools.partial(self._emboss, radius, sigma))

    def _emboss(self, radius: float = 3.0, sigma: float = 1.75):
        self.image.transform_colorspace('gray')
        self.image.emboss(radius, sigma)

    async def kuwahara(self, radius: int = 1, sigma: float = 1.5):
        await self.image_worker(functools.partial(self._kuwahara, radius, sigma))

    def _kuwahara(self, radius: int = 1, sigma: float = 1.5):
        self.image.kuwahara(radius, sigma)

    async def shade(self, gray: bool = True, azimuth: float = 286.0, elevation: float = 45.0):
        await self.image_worker(functools.partial(self._shade, gray, azimuth, elevation))

    def _shade(self, gray: bool = True, azimuth: float = 286.0, elevation: float = 45.0):
        self.image.shade(gray, azimuth, elevation)
