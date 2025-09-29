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

import functools
import re
import asyncio
from typing import Union, Optional
from io import BytesIO
from concurrent.futures import ProcessPoolExecutor

import discord
import imagehash
import aiohttp

from discord.ext import commands
from PIL import Image as PILImage
from wand.exceptions import *
from wand.image import Image as WandImage
from wand.color import Color
from wand.font import Font

from .url import get_embed_urls

from .exceptions import *

def _hasher(data: bytes) -> Optional[str]:
    """
    Returns a hash of the image data.
    """
    # load the raw bytes into a BytesIO buffer so that PIL can handle it better
    with BytesIO(data) as data_buffer:
        try:
            with PILImage.open(data_buffer) as pil_image:
                hash_string = str(imagehash.phash(pil_image, hash_size=16))
            
        except Exception:
            # return None if the image cannot be opened correctly for whatever reason
            return None
        
    return hash_string
    

# async function to run the hashing in its own process without blocking
async def hasher(loop: asyncio.AbstractEventLoop, data: bytes, pool: Optional[ProcessPoolExecutor] = None) -> Optional[str]:
    # placeholder variable for the hash string
    hash_string: Optional[str] = None

    try:
        # try to get the hash string from the executor
        hash_string = await asyncio.wait_for(loop.run_in_executor(pool, functools.partial(_hasher, data)), timeout=10)

    except asyncio.TimeoutError:
        return None
    
    except Exception as e:
        raise e
    
    return hash_string
    

async def download_image(session: aiohttp.ClientSession, url: str):
    """
    Downloads an image from a given URL. Deprecated.
    """
    async with session.get(url) as r:
        return await r.read()


async def download_last_image(
        ctx: Union[discord.ApplicationContext, commands.Context],
        aiohttp_session: aiohttp.ClientSession,
        search_len: int = 30
    ) -> BytesIO:
    
    # search past 30 messages for suitable media content, only search messages with an attachment or embed
    # first, get a suitable message
    if ctx.message.reference:
        # fetch the message from the reference
        message = await ctx.bot.get_or_fetch_message(ctx.message.reference.message_id, ctx.message.reference.channel_id)
        url = [url for url in get_embed_urls(message)][0][0]
    else:
        async for msg in ctx.channel.history(limit=search_len):
            for urls in get_embed_urls(msg):
                if (new_url := urls[0]) is not None and urls[1] == "image":
                    url = new_url
                    break
            else:
                continue
            break

    # if the url is not None, download the image and return it
    async with aiohttp_session.get(url) as resp:
        # if return_buffer is True, return a BytesIO buffer of the image and seek to the beginning
        buf = BytesIO(await resp.read())
        buf.seek(0)
        return buf

class ImageFunction:
    def __init__(self, buffer: BytesIO, fn: int, loop: asyncio.AbstractEventLoop, process_pool: Optional[ProcessPoolExecutor]):
        buffer.seek(0)
        self.loop = loop
        self.process_pool = process_pool
        self.embed = discord.Embed()
        
        try:
            self.image = WandImage(file=buffer)
        except CacheError:
            raise ImageTooLargeException
        finally:
            buffer.close()
        
        self.fn = fn
    
    def save_image(self, is_gif=False) -> BytesIO:
        buf = None
        try:
            buf = self._save_to_buffer()
            self.embed.title = "Processed image"
            extension = 'png' if not is_gif else 'gif'
            self.embed.set_image(url=f"attachment://image.{extension}")
            file = discord.File(fp=buf, filename=f"image.{extension}")
            return self.embed, file
            
        except Exception as e:
            self.embed.title = "Fatal Error"
            self.embed.description = "There has been a fatal error processing this image"
            self.embed.color = discord.Color.red()
            return self.embed, None
        
        finally:
            if self.image is not None:
                self.image.destroy()

            if buf is not None:
                buf.close()

    async def image_worker(self, func, *args):
        try:
            await self.loop.run_in_executor(executor=self.process_pool, func=functools.partial(func, *args))
        except WandException as e:
            # wand-related exceptions
            print(e)
            
    def _save_to_buffer(self) -> BytesIO:
        self.image.format = "png"
        buf = BytesIO()
        self.image.save(file=buf)
        self.image.close()
        buf.seek(0)
        return buf

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
        await self.image_worker(functools.partial(self._swirlmagik, float(angle)))

    def _swirlmagik(self, angle):
        self.image.swirl(angle)
        self._magik()
        self.image.swirl(-angle)

    async def swirl(self, angle: float):
        await self.image_worker(functools.partial(self._swirl, float(angle)))

    def _swirl(self, angle: int=-60):
        self.image.swirl(degree=angle)

    async def invert(self):
        await self.image_worker(self._invert)

    def _invert(self):
        self.image.negate()

    async def implode(self, factor):
        await self.image_worker(functools.partial(self._implode, float(factor)))

    def _implode(self, factor):
        self.image.implode(factor)

    async def opacify(self):
        await self.image_worker(self._opacify)

    def _opacify(self):
        self.image.alpha_channel = 'remove'
        self.image.background_color = Color('white')

    async def explode(self, factor):
        await self.image_worker(functools.partial(self._implode, -float(factor)))

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
        self.image.resize(width=int(self.image.width * 3.2), height=int(self.image.height / 1.7))
        self.image.crop(left=int(self.image.width / 4), top=1, right=(self.image.width - (int(self.image.width / 4))),
                        bottom=self.image.height)

    async def deepfry(self):
        await self.image_worker(self._deepfry)

    def _deepfry(self):
        self.image.sharpen(30,16)
        self.image.colorize(color="#f9fc12", alpha="rgb(10%, 10%, 10%)")
        self.image.modulate(saturation=600.00)
        self.image.noise('gaussian', attenuate=0.072)
        self.image.sharpen(7,16)
        self.image.compression_quality = 0

    async def rotate(self, angle:float = 90):
        await self.image_worker(functools.partial(self._rotate, float(angle)))

    def _rotate(self, angle:float = 90):
        self.image.rotate(degree=angle)

    async def black_white(self):
        await self.image_worker(self._black_white)

    def _black_white(self):
        self.image.transform_colorspace('gray')

    async def sepia(self, threshold: float = 0.8):
        await self.image_worker(functools.partial(self._sepia, float(threshold)))

    def _sepia(self, threshold: float = 0.8):
        self.image.sepia_tone(float(threshold))

    async def polaroid(self):
        await self.image_worker(self._polaroid)

    def _polaroid(self):
        self.image.polaroid()

    async def charcoal(self, radius: float = 1.5, sigma: float = 0.5):
        await self.image_worker(functools.partial(self._charcoal, float(radius), float(sigma)))

    def _charcoal(self, radius: float = 1.5, sigma: float = 0.5):
        self.image.charcoal(float(radius),float(sigma))

    async def make_vignette(self, sigma: int = 3, x: int = 10, y: int = 10):
        await self.image_worker(functools.partial(self._make_vignette, float(sigma), float(x), float(y)))

    def _make_vignette(self, sigma: int = 3, x: int = 10, y: int = 10):
        self.image.vignette(float(sigma), int(x), int(y))

    async def bubble(self, flip=False):
        await self.image_worker(self._bubble, flip)

    def _bubble(self, flip=False):
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
            if flip:
                neg.flop()
                neg.flop()
            # compose the input image onto the negative
            neg.composite_channel(channel='default_channels', image=self.image, operator='src_in')
            # compose the outline image onto the composed negative
            neg.composite_channel(channel='default_channels', image=out, operator='over')
            # create self.image binary output for the upload
            self.image = neg.clone()
            neg.destroy()
            out.destroy()

    async def scale(self, factor: float = 0.5):
        await self.image_worker(functools.partial(self._scale, float(factor)))

    def _scale(self, factor: float = 0.5):
        # input protection
        if 1 > factor < 0.1:
            factor = 0.5
        self.image.resize(width=int(self.image.width * factor), height=int(self.image.height * factor))

    async def blur(self, radius: int = 0, sigma: int = 3):
        await self.image_worker(functools.partial(self._blur, float(radius), float(sigma)))

    def _blur(self, radius: int = 0, sigma: int = 3):
        self.image.blur(radius, sigma)

    async def adaptive_blur(self, radius: int = 8, sigma: int = 4):
        await self.image_worker(functools.partial(self._adaptive_blur, float(radius), float(sigma)))

    def _adaptive_blur(self, radius: int = 8, sigma: int = 4):
        self.image.adaptive_blur(radius, sigma)

    async def motion_blur(self, radius: int = 8, sigma: int = 4, angle: int = -45):
        await self.image_worker(functools.partial(self._motion_blur, float(radius), float(sigma), float(angle)))

    def _motion_blur(self, radius: int = 8, sigma: int = 4, angle: int = -45):
        self.image.motion_blur(radius, sigma, angle)

    async def edge(self, radius: int = 1):
        await self.image_worker(functools.partial(self._edge, float(radius)))

    def _edge(self, radius: int = 1):
        self.image.transform_colorspace('gray')
        self.image.edge(radius)

    async def emboss(self, radius: float = 3.0, sigma: float = 1.75):
        await self.image_worker(functools.partial(self._emboss, float(radius), float(sigma)))

    def _emboss(self, radius: float = 3.0, sigma: float = 1.75):
        self.image.transform_colorspace('gray')
        self.image.emboss(radius, sigma)

    async def kuwahara(self, radius: int = 1, sigma: float = 1.5):
        await self.image_worker(functools.partial(self._kuwahara, float(radius), float(sigma)))

    def _kuwahara(self, radius: int = 1, sigma: float = 1.5):
        self.image.kuwahara(radius, sigma)

    async def shade(self, gray: bool = True, azimuth: float = 286.0, elevation: float = 45.0):
        await self.image_worker(functools.partial(self._shade, bool(gray), float(azimuth), float(elevation)))

    def _shade(self, gray: bool = True, azimuth: float = 286.0, elevation: float = 45.0):
        self.image.shade(gray, azimuth, elevation)
