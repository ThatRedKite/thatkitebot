# ------------------------------------------------------------------------------
#  MIT License
#
#  Copyright (c) 2019-2021 ThatRedKite
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
#  documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
#  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
#  and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all copies or substantial portions of
#  the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
#  THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
#  TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
# ------------------------------------------------------------------------------

from io import BytesIO
import random
import imageio
from wand.image import Image as WandImage
from wand.color import Color
import numpy as np
from discord.ext.commands import Context
from . import url as url_util
from discord import File
from os.path import join
from numpy import array
from PIL import ImageDraw, ImageFont, Image
from concurrent.futures import ProcessPoolExecutor


# define filters which all take one argument (i) which is a numpy array:

def magik(i, fn):
    with WandImage.from_array(i) as a:
        a.liquid_rescale(width=int(a.width / 2), height=int(a.height / 2), delta_x=1, rigidity=0)
        a.liquid_rescale(width=int(a.width * 2), height=int(a.height * 2), delta_x=2, rigidity=0)
        return np.array(a), fn


def swirl(i, fn, param: int = -60):
    with WandImage.from_array(i) as a:
        a.swirl(degree=param)
        return np.array(a), fn


def implode(i, fn):
    with WandImage.from_array(i) as a:
        a.implode(0.6)
        return np.array(a), fn


def opacify(i, fn):
    with WandImage.from_array(i) as a:
        a.alpha_channel = "remove"
        a.background_color = Color("white")
        return np.array(a), fn


def explode(i, fn):
    with WandImage.from_array(i) as a:
        a.implode(-4.0)
        return np.array(a), fn


def eightbit(i, fn):
    with WandImage.from_array(i) as a:
        a.posterize(levels=4)
        return np.array(a), fn


def caption(i, fn, ct, path):
    font = ImageFont.truetype(join(path, "DejaVuSans.ttf"), 47)  # load the font
    with Image.fromarray(i) as im:
        outline_width = 3
        W, H = im.size
        w, h = font.getsize(ct)
        # convert the image to RGBA to avoid some problems
        im = im.convert("RGBA")
        draw = ImageDraw.Draw(im)
        # draw the outline
        draw.text(((W - w) / 2 - outline_width, int((H - h) / 1.15) - outline_width), ct, fill="black", font=font)
        draw.text(((W - w) / 2 - outline_width, int((H - h) / 1.15) + outline_width), ct, fill="black", font=font)
        draw.text(((W - w) / 2 + outline_width, int((H - h) / 1.15) - outline_width), ct, fill="black", font=font)
        draw.text(((W - w) / 2 + outline_width, int((H - h) / 1.15) + outline_width), ct, fill="black", font=font)
        # draw the text itself
        draw.text(((W - w) / 2, int((H - h) / 1.15)), ct, fill="white", font=font)
        return array(im), fn


def wide(i, fn):
    with WandImage.from_array(i) as a:
        a.resize(width=int(a.width * 3.3), height=int(a.height / 1.8))
        a.crop(left=int(a.width / 4), top=1, right=(a.width - (int(a.width / 4))), bottom=a.height)
        return np.array(a), fn


def deepfry(i, fn):
    with WandImage.from_array(i) as a:
        a.modulate(saturation=600.00)
        a.noise("gaussian", attenuate=0.1)
        return np.array(a), fn


async def do_stuff(loop, session, history, mode: str, text: str = "", path="", gif: bool = False, tk="", deg=60):
    # get the url of the image and download it
    if type(history) is Context:
        url = await url_util.imageurlgetter(session, history.channel.history(limit=30), gif=gif, token=tk)
    else:
        url = str(history)
    io = await url_util.imagedownloader(session, url)

    modes = {
        "magik": magik,
        "deepfry":deepfry,
        "wide": wide,
        "caption": caption,
        "implode": implode,
        "explode": explode,
        "swirl": swirl,
        "opacify": opacify,
        "reduce": eightbit
    }

    chosen_mode = modes.get(mode, magik)
    if gif:
        return io, chosen_mode
    with ProcessPoolExecutor() as pool:

        if chosen_mode is swirl:
            io, frame = await loop.run_in_executor(pool, chosen_mode, list(io)[0], 1, deg)
        elif chosen_mode is not caption:
            io, frame = await loop.run_in_executor(pool, chosen_mode, list(io)[0], 1)
        else:
            io, frame = await loop.run_in_executor(pool, chosen_mode, list(io)[0], 1, text, path)
        del frame  # delete that frame counter, we don't need it

    with BytesIO() as image_buffer:
        imageio.imwrite(image_buffer, io, format="png")  # this writes the images to the image buffer, use PNG as format
        image_buffer.seek(0)  # "rewind" the buffer. Otherwise the discord.File object can't see any image file
        return File(image_buffer, filename="processed.png")  # return a discord.File object
