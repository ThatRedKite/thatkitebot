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
import re
from concurrent.futures import ProcessPoolExecutor
from io import BytesIO
import discord
import imageio
from discord.ext import commands
from typing import Optional
from os.path import join
from PIL import ImageDraw, ImageFont, Image
from wand.image import Image as WandImage
from wand.color import Color
from numpy import array

def magik(blob, format, fn, ra=False):
    buf = BytesIO(blob)
    buf.seek(0)
    with WandImage(file=buf, format=format) as a:
        buf.close()
        a.liquid_rescale(width=int(a.width / 2), height=int(a.height / 2), delta_x=1, rigidity=0)
        a.liquid_rescale(width=int(a.width * 2), height=int(a.height * 2), delta_x=2, rigidity=0)
        b = a.make_blob(format="png")
        a.destroy()
    if not ra:
        return b, fn
    else:
        return array(a), fn

def swirl(blob, format, fn, angle: int = -60):
    buf = BytesIO(blob)
    buf.seek(0)
    with WandImage(file=buf, format=format) as a:
        buf.close()
        a.swirl(degree=angle)
        b = a.make_blob(format="png")
        a.destroy()
    return b, fn


def invert(blob, format, fn):
    buf = BytesIO(blob)
    buf.seek(0)
    with WandImage(file=buf, format=format) as a:
        buf.close()
        a.negate()
        b = a.make_blob(format="png")
        a.destroy()
    return b, fn


def implode(blob, format, fn):
    buf = BytesIO(blob)
    buf.seek(0)
    with WandImage(file=buf, format=format) as a:
        buf.close()
        a.implode(0.6)
        b = a.make_blob(format="png")
        a.destroy()
    return b, fn


def opacify(blob, format, fn):
    buf = BytesIO(blob)
    buf.seek(0)
    with WandImage(file=buf, format=format) as a:
        buf.close()
        a.alpha_channel = "remove"
        a.background_color = Color("white")
        b = a.make_blob(format="png")
        a.destroy()
    return b, fn


def explode(blob, format, fn):
    buf = BytesIO(blob)
    buf.seek(0)
    with WandImage(file=buf, format=format) as a:
        buf.close()
        a.implode(-5.0)
        b = a.make_blob(format="png")
        a.destroy()
    return b, fn


def reduce(blob, format, fn):
    buf = BytesIO(blob)
    buf.seek(0)
    with WandImage(file=buf, format=format) as a:
        buf.close()
        a.posterize(levels=4)
        b = a.make_blob(format="png")
        a.destroy()
    return b, fn


def caption(blob, format, fn, ct, path):
    font = ImageFont.truetype(join(path, "DejaVuSans.ttf"), 47)  # load the font
    with Image.fromarray(blob) as im:
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
        with BytesIO() as ob:
            im.save(ob, format="png")
            b = ob.getvalue()
    return b, fn


def wide(blob, format, fn):
    buf = BytesIO(blob)
    buf.seek(0)
    with WandImage(file=buf, format=format) as a:
        buf.close()
        a.resize(width=int(a.width * 3.3), height=int(a.height / 1.8))
        a.crop(left=int(a.width / 4), top=1, right=(a.width - (int(a.width / 4))), bottom=a.height)
        b = a.make_blob(format="png")
        a.destroy()
    return b, fn


def deepfry(blob, format, fn):
    buf = BytesIO(blob)
    buf.seek(0)
    with WandImage(file=buf, format=format) as a:
        buf.close()
        a.modulate(saturation=600.00)
        a.noise("gaussian", attenuate=0.1)
        b = a.make_blob(format="png")
        a.destroy()
    return b, fn


class ImageStuff(commands.Cog, name="image commands"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.td = bot.tempdir  # temp directory
        self.dd = bot.datadir  # data directory
        self.ll = self.bot.loop
        self.session = self.bot.aiohttp_session
        self.tt = self.bot.tenortoken
        self.tenor_pattern = re.compile("^https://tenor.com\S+-(\d+)$")

    # this function is originally from iangecko's pyrobot, modifications were made for this bot
    async def get_last_image(self, ctx):
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
                    case "gifv":
                        tenor_id = int(self.tenor_pattern.match(attachment.url).group(1))
                        if tenor_id:
                            headers = {
                                "User-Agent": f"ThatKiteBot/{self.bot.version}",
                                "content-type": "application/json"
                            }

                            payload = {
                                "key": self.tt,
                                "ids": tenor_id,
                                "media_filter": "minimal"
                            }

                            t_url = "https://api.tenor.com/v1/gifs"
                            async with self.session.get(url=t_url, params=payload, headers=headers) as r:
                                gifs = await r.json()
                                url = gifs["results"][0]["media"][0]["gif"]["url"]

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
        filetype = re.search("(^https?://\S+.(?i)(png|webp|gif|jpe?g))", url).group(2)
        return blob, filename, url, filetype

    # TODO: check if user has image permissions
    async def cog_check(self, ctx):
        return self.bot.redis.hget(ctx.guild.id, "IMAGE") == "TRUE"

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["magic"])
    async def magik(self, ctx: commands.Context):
        """Applies some content aware scaling to an image. When the image is a GIF, it takes the first frame"""
        async with ctx.channel.typing():
            blob, filename, url, filetype = await self.get_last_image(ctx)
            with ProcessPoolExecutor() as pool:
                b2, fn = await self.ll.run_in_executor(pool, magik, blob, filetype, 1)
            file = discord.File(BytesIO(b2), filename="magik.png")
            await ctx.send(file=file)

    @commands.cooldown(3, 10, commands.BucketType.user)
    @commands.command()
    async def pfp(self, ctx, user: Optional[discord.User] = None):
        """sends the pfp of someone"""
        if not user:
            user = ctx.message.author

        await ctx.send(user.avatar_url)

    @commands.cooldown(3, 10, commands.BucketType.user)
    @commands.command()
    async def deepfry(self, ctx: commands.Context):
        """deepfry an image"""
        async with ctx.channel.typing():
            blob, filename, url, filetype = await self.get_last_image(ctx)
            with ProcessPoolExecutor() as pool:
                b2, fn = await self.ll.run_in_executor(pool, deepfry, blob, filetype, 1)
            file = discord.File(BytesIO(b2), filename="deepfry.png")
            await ctx.send(file=file)

    @commands.cooldown(3, 10, commands.BucketType.user)
    @commands.command()
    async def wide(self, ctx: commands.Context):
        """Horizonally stretch an image"""
        async with ctx.channel.typing():
            blob, filename, url, filetype = await self.get_last_image(ctx)
            with ProcessPoolExecutor() as pool:
                b2, fn = await self.ll.run_in_executor(pool, wide, blob, filetype, 1)
            file = discord.File(BytesIO(b2), filename="wide.png")
            await ctx.send(file=file)

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["opacity"])
    async def opacify(self, ctx: commands.Context):
        """remove the alpha channel and replace it with white"""
        async with ctx.channel.typing():
            blob, filename, url, filetype = await self.get_last_image(ctx)
            with ProcessPoolExecutor() as pool:
                b2, fn = await self.ll.run_in_executor(pool, opacify, blob, filetype, 1)
            file = discord.File(BytesIO(b2), filename="opacify.png")
            await ctx.send(file=file)

    @commands.cooldown(3, 10, commands.BucketType.user)
    @commands.command(aliases=["inflate"])
    async def explode(self, ctx: commands.Context):
        """explode an image"""
        async with ctx.channel.typing():
            blob, filename, url, filetype = await self.get_last_image(ctx)
            with ProcessPoolExecutor() as pool:
                b2, fn = await self.ll.run_in_executor(pool, explode, blob, filetype, 1)
            file = discord.File(BytesIO(b2), filename="explode.png")
            await ctx.send(file=file)

    @commands.cooldown(3, 10, commands.BucketType.user)
    @commands.command(aliases=["deflate"])
    async def implode(self, ctx: commands.Context):
        """implode an image"""
        async with ctx.channel.typing():
            blob, filename, url, filetype = await self.get_last_image(ctx)
            with ProcessPoolExecutor() as pool:
                b2, fn = await self.ll.run_in_executor(pool, implode, blob, filetype, 1)
            file = discord.File(BytesIO(b2), filename="explode.png")
            await ctx.send(file=file)

    @commands.cooldown(3, 10, commands.BucketType.user)
    @commands.command(aliases=["inverse", "anti"])
    async def invert(self, ctx: commands.Context):
        """implode an image"""
        async with ctx.channel.typing():
            blob, filename, url, filetype = await self.get_last_image(ctx)
            with ProcessPoolExecutor() as pool:
                b2, fn = await self.ll.run_in_executor(pool, invert, blob, filetype, 1)
            file = discord.File(BytesIO(b2), filename="invert.png")
            await ctx.send(file=file)

    @commands.cooldown(3, 10, commands.BucketType.user)
    @commands.command()
    async def reduce(self, ctx: commands.Context):
        """reduce the amount of colors of an image"""
        async with ctx.channel.typing():
            blob, filename, url, filetype = await self.get_last_image(ctx)
            with ProcessPoolExecutor() as pool:
                b2, fn = await self.ll.run_in_executor(pool, reduce, blob, filetype, 1)
            file = discord.File(BytesIO(b2), filename="explode.png")
            await ctx.send(file=file)

    @commands.cooldown(3, 10, commands.BucketType.user)
    @commands.command()
    async def swirl(self, ctx: commands.Context, degree: int = 60):
        """swirl an image"""
        async with ctx.channel.typing():
            blob, filename, url, filetype = await self.get_last_image(ctx)
            with ProcessPoolExecutor() as pool:
                b2, fn = await self.ll.run_in_executor(pool, swirl, blob, filetype, 1, degree)
            file = discord.File(BytesIO(b2), filename="explode.png")
            await ctx.send(file=file)

    @commands.cooldown(3, 10, commands.BucketType.user)
    @commands.command()
    async def caption(self, ctx, *, text: str = ""):
        """Adds a caption to an image."""
        async with ctx.channel.typing():
            blob, filename, url, filetype = await self.get_last_image(ctx)
            newblob = imageio.imread(BytesIO(blob))
            with ProcessPoolExecutor() as pool:
                b2, fn = await self.ll.run_in_executor(pool, caption, newblob, filetype, 1, text, self.dd)
            file = discord.File(BytesIO(b2), filename="explode.png")
            await ctx.send(file=file)

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

def setup(bot):
    bot.add_cog(ImageStuff(bot))
