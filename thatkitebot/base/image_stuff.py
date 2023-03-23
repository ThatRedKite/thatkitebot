import io
import re
from datetime import datetime
from typing import Union

import discord
import imagehash
import aiohttp

from PIL import Image as PILImage
from wand.image import Image as WandImage
from wand.color import Color
from wand.font import Font

from .exceptions import *


def hasher(data):
    """
    Returns a hash of the image data.
    """
    pil_image = PILImage.open(io.BytesIO(data))
    return str(imagehash.phash(pil_image, hash_size=16))


async def download_image(session: aiohttp.ClientSession, url: str):
    """
    Downloads an image from a given URL. Deprecated.
    """
    async with session.get(url) as r:
        return await r.read()


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
        elif embed.type == "rich" and message.embeds[0].image:
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


class ImageFunction:
    def __init__(self, buffer: io.BytesIO, fn:int):
        buffer.seek(0)
        self.image = WandImage(file=buffer)

        if self.image.height >= 6000 or self.image.height >= 6000:
            self.image.destroy()
            raise ImageTooLargeException

        self.fn = fn

    def make_blob_close(self) -> (bytes, int):
        self.image.format = "png"
        b = self.image.make_blob()
        self.image.destroy()
        return b, self.fn

    def make_blob(self) -> (bytes, int):
        self.image.format = "png"
        b = self.image.make_blob()
        return b, self.fn

    def close(self):
        self.image.destroy()

    def magik(self):
        self.image.sample(width=int(self.image.width * 0.5), height=int(self.image.height * 0.5))
        self.image.liquid_rescale(width=int(self.image.width / 2), height=int(self.image.height / 1.5), delta_x=1, rigidity=0)
        self.image.liquid_rescale(width=int(self.image.width * 2), height=int(self.image.height * 1.5), delta_x=2, rigidity=0)
        self.image.sample(width=int(self.image.width * 2), height=int(self.image.height * 2))

    def swirlmagik(self, angle):
        self.image.swirl(angle)
        self.magik()
        self.image.swirl(-angle)

    def swirl(self, angle: int = -60):
        self.image.swirl(degree=angle)

    def invert(self):
        self.image.negate()

    def implode(self, factor):
        self.image.implode(factor)

    def opacify(self):
        self.image.alpha_channel = 'remove'
        self.image.background_color = Color('white')

    def explode(self, factor):
        self.image.implode(-factor)

    def reduce(self):
        self.image.posterize(levels=2)

    def caption(self, ct, path):
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
        x = re.findall(r'color:(?:\d{2}|[1-f]{2}){3}', in_str)
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

    def wide(self):
        self.image.resize(width=int(self.image.width * 3.3), height=int(self.image.height / 1.8))
        self.image.crop(left=int(self.image.width / 4), top=1, right=(self.image.width - (int(self.image.width / 4))), bottom=self.image.height)

    def deepfry(self):
        self.image.modulate(saturation=600.00)
        self.image.noise('gaussian', attenuate=0.1)

    def rotate(self, angle: int = 90):
        self.image.rotate(degree=angle)

    def black_white(self):
        self.image.transform_colorspace('gray')

    def sepia(self, threshold: float = 0.8):
        self.image.sepia_tone(threshold)

    def polaroid(self):
        self.image.polaroid()

    def charcoal(self, radius: float = 1.5, sigma: float = 0.5):
        self.image.charcoal(radius, sigma)


    def make_vignette(self, sigma: int = 3, x: int = 10, y: int = 10):
        
            self.image.vignette(sigma, x, y)
            


    def bubble(self):
        # grab the template files stored in the data directory
        negative = '/app/data/resources/bubble_negative.png'
        outline = '/app/data/resources/bubble_outline.png'

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
            self.image = neg

    def scale(self, factor: float = 0.5):
        # input protection
        if 1 > factor < 0.1:
            factor = 0.5
        self.image.resize(width=int(self.image.width * factor), height=int(self.image.height * factor))

    def blur(self, radius: int = 0, sigma: int = 3):
        self.image.blur(radius, sigma)

    def adaptive_blur(self, radius: int = 8, sigma: int = 4):
        self.image.adaptive_blur(radius, sigma)

    def motion_blur(self, radius: int = 8, sigma: int = 4, angle: int = -45):
        self.image.motion_blur(radius, sigma, angle)

    def edge(self, radius: int = 1):
        self.image.transform_colorspace('gray')
        self.image.edge(radius)

    def emboss(self, radius: float = 3.0, sigma: float = 1.75):
        self.image.transform_colorspace('gray')
        self.image.emboss(radius, sigma)

    def kuwahara(self, radius: int = 1, sigma: float = 1.5):
        self.image.kuwahara(radius, sigma)

    def shade(self, gray: bool = True, azimuth: float = 286.0, elevation: float = 45.0):
        self.image.shade(gray, azimuth, elevation)
