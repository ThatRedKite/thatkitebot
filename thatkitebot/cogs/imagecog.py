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
import asyncio
import functools
import re
from concurrent.futures import ProcessPoolExecutor
from io import BytesIO
import discord
from discord.ext import commands
from typing import Optional
from os.path import join
from PIL import ImageDraw, ImageFont, Image
from wand.image import Image as WandImage
from wand.color import Color
from wand.drawing import Drawing
from wand.font import Font
from thatkitebot.backend import util


def magik(buf, fn):
    with WandImage(file=buf) as a:
        if a.width > 3000 or a.height > 3000:
            a.destroy()
            return None, -1
        a.sample(width=int(a.width * 0.5), height=int(a.height * 0.5))
        a.liquid_rescale(width=int(a.width / 2), height=int(a.height / 1.5), delta_x=1, rigidity=0)
        a.liquid_rescale(width=int(a.width * 2), height=int(a.height * 1.5), delta_x=2, rigidity=0)
        a.sample(width=int(a.width * 2), height=int(a.height * 2))
        b = a.make_blob(format="png")
        a.destroy()
    return b, fn


def swirlmagik(buf, fn):
    with WandImage(file=buf) as a:
        if a.width > 3000 or a.height > 3000:
            a.destroy()
            return None, -1
        a.sample(width=int(a.width * 0.5), height=int(a.height * 0.5))
        a.swirl(60)
        a.liquid_rescale(width=int(a.width / 2), height=int(a.height / 1.5), delta_x=1, rigidity=0)
        a.liquid_rescale(width=int(a.width * 2), height=int(a.height * 1.5), delta_x=2, rigidity=0)
        a.swirl(-60)
        a.sample(width=int(a.width * 2), height=int(a.height * 2))
        b = a.make_blob(format="png")
        a.destroy()
    return b, fn


def swirl(buf, fn, angle: int = -60):
    with WandImage(file=buf) as a:
        a.swirl(degree=angle)
        b = a.make_blob(format="png")
        a.destroy()
    return b, fn


def invert(buf, fn):
    with WandImage(file=buf) as a:
        a.negate()
        b = a.make_blob(format="png")
        a.destroy()
    return b, fn


def implode(buf, fn):
    with WandImage(file=buf) as a:
        a.implode(0.6)
        b = a.make_blob(format="png")
        a.destroy()
    return b, fn


def opacify(buf, fn):
    with WandImage(file=buf) as a:
        a.alpha_channel = "remove"
        a.background_color = Color("white")
        b = a.make_blob(format="png")
        a.destroy()
    return b, fn


def explode(buf, fn):
    with WandImage(file=buf) as a:
        a.implode(-4.0)
        b = a.make_blob(format="png")
        a.destroy()
    return b, fn


def reduce(buf, fn):
    with WandImage(file=buf) as a:
        a.posterize(levels=2)
        b = a.make_blob(format="png")
        a.destroy()
    return b, fn


def caption(blob, fn, ct, path):
    color_alias = {
        "piss":"#f9fc12",
        "cum":"#ededd5",
        "pickle":"#12a612"
    }
    in_str = str(ct)
    # find any emotes in the text 
    x = re.findall(r"[<]:\w{2,}:\d{15,}[>]", in_str)
    for n in x: in_str = in_str.replace(str(n), re.findall(r":\w{2,}:", n)[0])
    # find any parameters in the command
    color = "white"
    x = re.findall(r"color:\d{1,3},\d{1,3},\d{1,3}", in_str)
    if len(x) > 0: 
        color = x[0].lower().replace("color:", "rgb(") + ")"
        in_str = in_str.replace(x[0], "")
    x = re.findall(r"color:(?:\d{2}|[1-f]{2}){3}", in_str)
    if len(x) > 0: 
        color = x[0].lower().replace("color:", "#") 
        in_str = in_str.replace(x[0], "")
    x = re.findall(r"color:[\w]{3,30}", in_str)
    if len(x) > 0: 
        color = x[0].lower().replace("color:", "") 
        in_str = in_str.replace(x[0], "")
        if color in color_alias:
            color = color_alias[color]
    try:
        with WandImage(file=blob) as image:
            # Calculate image parameters for the text to wrap and fit.
            txt_top = int(0.70 * image.height)  # add text to the bottom 25% of the image
            txt_left = int(0.10 * image.width)  # leave 10 % the image from the left
            txt_width = image.width - (
                        txt_left * 2)  # total width - 10% * 2 will leave 10% of with on the right side as well
            txt_height = image.height - txt_top  # use the whole 15% for text
            stroke_width = (txt_height * txt_width)/(10000 + (2500 * len(in_str)))
            if stroke_width < 1.5 or color != "white":
                font = Font(path + "OpenSansEmoji.ttf", color=color)
            else:
                font = Font(path + "OpenSansEmoji.ttf", color=color, stroke_color="black", stroke_width=stroke_width)
            image.caption(in_str, left=txt_left, top=txt_top, width=txt_width, height=txt_height, font=font,
                        gravity='center')
            image.format = 'png'
            b = image.make_blob()
            image.destroy()
    except:
        fn = -3 # probably wrong color
        b = None
    return b, fn


def wide(buf, fn):
    with WandImage(file=buf) as a:
        if a.width > 3000 or a.height > 3000:
            a.destroy()
            return None, -1
        a.resize(width=int(a.width * 3.3), height=int(a.height / 1.8))
        a.crop(left=int(a.width / 4), top=1, right=(a.width - (int(a.width / 4))), bottom=a.height)
        b = a.make_blob(format="png")
        a.destroy()
    return b, fn


def deepfry(buf, fn):
    with WandImage(file=buf) as a:
        a.modulate(saturation=600.00)
        a.noise("gaussian", attenuate=0.1)
        b = a.make_blob(format="png")
        a.destroy()
    return b, fn


def rotate(buf, fn, angle: int = 90):
    with WandImage(file=buf) as a:
        a.rotate(degree=angle, )
        b = a.make_blob(format="png")
        a.destroy()
    return b, fn


class ImageStuff(commands.Cog, name="image commands"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sep = asyncio.Semaphore(12)
        self.pp = ProcessPoolExecutor(max_workers=4)
        self.td = bot.tempdir  # temp directory
        self.dd = bot.datadir  # data directory
        self.ll = asyncio.get_event_loop()
        self.session = self.bot.aiohttp_session
        self.tt = self.bot.tenortoken
        self.tenor_pattern = re.compile(r"^https://tenor.com\S+-(\d+)$")

    # this function is originally from iangecko's pyrobot, modifications were made for this bot
    async def get_last_image(self, ctx, return_buffer=False):
        # search past 30 messages for suitable media
        attachment = None
        url = None
        blob = None
        filename = "image"
        async for msg in ctx.channel.history(limit=30).filter(lambda m: m.attachments or m.embeds):
            if msg.attachments:
                blob = await msg.attachments[0].read()
                filename = msg.attachments[0].filename
                url = msg.attachments[0].url
            else:
                attachment = msg.embeds[0]
                match attachment.type:
                    case "image":
                        url = attachment.url
                    case "rich":
                        if attachment.image:
                            url = attachment.image.url
                        else:
                            continue
                    case _:
                        continue
                if url:
                    filename = attachment.image.filename
                    session = self.bot.aiohttp_session
                    async with session.get(url=url) as r:
                        blob = await r.read()
            break
        else:
            return None
        filetype = re.search(r"(^https?://\S+.(?i)(png|webp|gif|jpe?g))", url).group(2)
        if not return_buffer:
            return blob, filename, url, filetype
        else:
            buf = BytesIO(blob)
            buf.seek(0)
            return buf, filename, url, filetype

    async def cog_check(self, ctx):
        is_enabled = await self.bot.redis.hget(ctx.guild.id, "IMAGE") == "TRUE"
        can_attach = ctx.channel.permissions_for(ctx.author).attach_files
        can_embed = ctx.channel.permissions_for(ctx.author).embed_links
        return is_enabled and can_attach and can_embed

    async def image_worker(self, func, name):
        async with self.sep:
            try:
                b2, fn = await asyncio.wait_for(self.ll.run_in_executor(self.pp, func), timeout=30.0)
            except asyncio.TimeoutError:

                e = await util.errormsg(
                    msg="Processing timed out",
                    embed_only=True
                )
                return e, None
            if fn < 0 and fn != -3:
                a = await util.errormsg("Your image is too large! Image should be smaller than 3000x3000", embed_only=True)
                return a, None
            elif fn == -3:
                a = await util.errormsg("The color selected does not exist or is in the wrong format.", embed_only=True)
                return a, None
        embed = discord.Embed(title="Processed image")
        embed.set_image(url=f"attachment://{name}.png")
        file = discord.File(BytesIO(b2), filename=f"{name}.png")
        return embed, file

    @commands.cooldown(3, 5, commands.BucketType.guild)
    @commands.command(aliases=["magic"])
    async def magik(self, ctx: commands.Context):
        """Applies some content aware scaling to an image. When the image is a GIF, it takes the first frame"""
        buf, filename, url, filetype = await self.get_last_image(ctx, return_buffer=True)
        async with ctx.channel.typing():
            embed, file = await self.image_worker(functools.partial(magik, buf=buf, fn=0), "magik")
            buf.close()
        await ctx.send(file=file, embed=embed)

    @commands.cooldown(3, 5, commands.BucketType.guild)
    @commands.command(aliases=["swirlmagik", "smagic", "swirlmagic"])
    async def smagik(self, ctx: commands.Context):
        """
        Applies some content aware and swirling scaling to an image.
        When the image is a GIF, it takes the first frame
        """
        buf, filename, url, filetype = await self.get_last_image(ctx, return_buffer=True)
        async with ctx.channel.typing():
            embed, file = await self.image_worker(functools.partial(swirlmagik, buf=buf, fn=1), "swirlmagik")
            buf.close()
        await ctx.send(file=file, embed=embed)

    @commands.cooldown(3, 10, commands.BucketType.channel)
    @commands.command()
    async def pfp(self, ctx, user: Optional[discord.Member] = None):
        """sends the pfp of someone"""
        if not user:
            user = ctx.message.author
        await ctx.send(user.avatar.url)

    @commands.cooldown(3, 5, commands.BucketType.guild)
    @commands.command()
    async def deepfry(self, ctx: commands.Context):
        """deepfry an image"""
        buf, filename, url, filetype = await self.get_last_image(ctx, return_buffer=True)
        async with ctx.channel.typing():
            embed, file = await self.image_worker(functools.partial(deepfry, buf=buf, fn=2), "deepfry")
            buf.close()
        await ctx.send(file=file, embed=embed)

    @commands.cooldown(3, 5, commands.BucketType.guild)
    @commands.command()
    async def wide(self, ctx: commands.Context):
        """Horizonally stretch an image"""
        buf, filename, url, filetype = await self.get_last_image(ctx, return_buffer=True)
        async with ctx.channel.typing():
            embed, file = await self.image_worker(functools.partial(wide, buf=buf, fn=3), "wide")
            buf.close()
        await ctx.send(file=file, embed=embed)

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["opacity"])
    async def opacify(self, ctx: commands.Context):
        """remove the alpha channel and replace it with white"""
        buf, filename, url, filetype = await self.get_last_image(ctx, return_buffer=True)
        async with ctx.channel.typing():
            embed, file = await self.image_worker(functools.partial(opacify, buf=buf, fn=4), "opacify")
            buf.close()
        await ctx.send(file=file, embed=embed)

    @commands.cooldown(3, 10, commands.BucketType.user)
    @commands.command(aliases=["inflate"])
    async def explode(self, ctx: commands.Context):
        """Explodes an image"""
        buf, filename, url, filetype = await self.get_last_image(ctx, return_buffer=True)
        async with ctx.channel.typing():
            embed, file = await self.image_worker(functools.partial(explode, buf=buf, fn=5), "explode")
            buf.close()
        await ctx.send(file=file, embed=embed)

    @commands.cooldown(3, 10, commands.BucketType.user)
    @commands.command(aliases=["deflate"])
    async def implode(self, ctx: commands.Context):
        """Implodes an image"""
        buf, filename, url, filetype = await self.get_last_image(ctx, return_buffer=True)
        async with ctx.channel.typing():
            embed, file = await self.image_worker(functools.partial(implode, buf=buf, fn=6), "implode")
            buf.close()
        await ctx.send(file=file, embed=embed)

    @commands.cooldown(3, 10, commands.BucketType.user)
    @commands.command(aliases=["inverse", "anti"])
    async def invert(self, ctx: commands.Context):
        """implode an image"""
        buf, filename, url, filetype = await self.get_last_image(ctx, return_buffer=True)
        async with ctx.channel.typing():
            embed, file = await self.image_worker(functools.partial(invert, buf=buf, fn=7), "inverted")
            buf.close()
        await ctx.send(file=file, embed=embed)

    @commands.cooldown(3, 10, commands.BucketType.user)
    @commands.command()
    async def reduce(self, ctx: commands.Context):
        buf, filename, url, filetype = await self.get_last_image(ctx, return_buffer=True)
        async with ctx.channel.typing():
            embed, file = await self.image_worker(functools.partial(reduce, buf=buf, fn=8), "reduced")
            buf.close()
        await ctx.send(file=file, embed=embed)

    @commands.cooldown(5, 10, commands.BucketType.user)
    @commands.command()
    async def swirl(self, ctx: commands.Context, degree: int = 60):
        """swirl an image"""
        buf, filename, url, filetype = await self.get_last_image(ctx, return_buffer=True)
        async with ctx.channel.typing():
            embed, file = await self.image_worker(functools.partial(swirl, buf=buf, fn=9, angle=degree), "swirled")
            buf.close()
        await ctx.send(file=file, embed=embed)

    @commands.cooldown(3, 10, commands.BucketType.user)
    @commands.command()
    async def caption(self, ctx, *, text: str = ""):
        """
        Adds a caption to an image. You can add `color:` to the message to change text color using hex or decimal RGB values.
        Example: \n `caption funny color:ff2315` or  `caption funny color:255,123,22` or `caption funny color:firebrick`
        A full list of colors can be found here: https://imagemagick.org/script/color.php
        """
        buf, filename, url, filetype = await self.get_last_image(ctx, return_buffer=True)
        async with ctx.channel.typing():
            embed, file = await self.image_worker(functools.partial(caption, buf, 10, text, self.dd), "captioned")
            buf.close()
        await ctx.send(file=file, embed=embed)

    @commands.cooldown(3, 20, commands.BucketType.user)
    @commands.command()
    async def gmagik(self, ctx: commands.Context, mode: str = "", *, ct: str = ""):
        """
        Syntax: gmagik <mode> [caption text]
        This command has multiple modes: `speedup`, `wide`, `caption`, `deepfry` and `magik`
        If no mode is supplied it defaults to `magik`
        Inspired by NotSoBot but with extra features and improvements
        """
        await ctx.send("This command is currently broken and will be disabled until it works again.")
        """
        dry = False
        ll = self.ll
        p = join(self.dd, "DejaVuSans.ttf")

        async with ctx.channel.typing():
            # download the image from the URL and send a message which indicates a successful download
            blob, filename, url, filetype = await self.get_last_image(ctx)
            io = imageio.get_reader(blob)
            frames = [(imageio.imsave("<bytes>", arr, format="png"), fn) for fn, arr in enumerate(io)]

            pmsg = await ctx.send(f"This GIF has {len(frames)} frames. Too many frames make the file too big for discord.")

            # when we speed the GIF up, we don't need any processing to be done, just double the framerate
            if not mode.lower() == "speedup":
                fps = io.get_meta_data()["duration"]
            else:
                # double the framerate and set the variable to bypass any processing
                fps = (io.get_meta_data()["duration"]) * 2
                dry = True
            io.close()
        async with ctx.channel.typing():
            # only process the frames if the dry variable is False
            if not dry:
                with ProcessPoolExecutor() as pool:
                    if not mode.lower() == "caption":  # get the right function for the set mode
                        # create a list of awaitable future objects and do stuff with asyncio.gather
                        r = await asyncio.gather(*[ll.run_in_executor(pool, magik, fra, "png", fn, True) for fra, fn in frames])
                    else:
                        r = await asyncio.gather(*[ll.run_in_executor(pool, magik.caption, fra, fn, ct, p) for fn, fra in frames])

                    # wait for the futures to finish and add them to the :io: list
                    # TODO: turn this into a list comprehension
                    processed_output = []
                    for x in r:
                        processed_output.append([x[1], x[0]])

                processed_output.sort(key=lambda fn: fn[0])  # this sorts the frame list by frame number :fn:
                clean_output_sorted = [frame[1] for frame in processed_output]  # we don't need the frame numbers anymore, just keep the image data

            with BytesIO() as image_buffer:
                imageio.mimwrite(image_buffer, clean_output_sorted, fps=fps, format="gif")
                image_buffer.seek(0)  # "rewind" the buffer. Otherwise the discord.File object can't see any image file
                # discord doesn't know what to do with an image_buffer object, that's why we need to convert it first
                image_file = discord.File(image_buffer, filename="gmagik.gif")

        await ctx.send(file=image_file)  # send the result to the channel where the command was sent
        await pmsg.delete()  # delete the "download successful" message from earlier
        """

    @commands.cooldown(5, 10, commands.BucketType.user)
    @commands.command()
    async def rotate(self, ctx: commands.Context, degree: int = 90):
        """Rotate an image clockwise 90 degrees by default, you can specify the degree value as an argument"""
        buf, filename, url, filetype = await self.get_last_image(ctx, return_buffer=True)
        async with ctx.channel.typing():
            embed, file = await self.image_worker(functools.partial(rotate, buf=buf, fn=11, angle=degree), "rotated")
            buf.close()
        await ctx.send(file=file, embed=embed)


def setup(bot):
    bot.add_cog(ImageStuff(bot))
