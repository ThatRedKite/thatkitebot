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

from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from io import BytesIO
from os.path import join
import discord
import imageio
from discord.ext import commands
from backend import util, magik
from backend import url as url_util
from typing import Optional


class ImageStuff(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.td = bot.tempdir  # temp directory
        self.dd = bot.datadir  # data directory
        self.ll = self.bot.loop
        self.session = self.bot.aiohttp_session

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command()
    async def magik(self, ctx: commands.Context):
        """Applies some content aware scaling to an image. When the image is a GIF, it takes the first frame"""
        async with ctx.channel.typing():
            image_file = await magik.do_stuff(self.ll, self.session, ctx, "magik")
            await ctx.send(file=image_file)

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command()
    async def widepfp(self, ctx: commands.Context, user: Optional[discord.User] = None):
        """sends a horizontally stretched version of someonme's profile picture"""
        if not user:
            user = ctx.message.author

        async with ctx.channel.typing():
            image_file = await magik.do_stuff(self.ll, self.session, str(user.avatar_url), "wide")
            await ctx.send(file=image_file)

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command()
    async def pfp(self, ctx, user: Optional[discord.User] = None):
        """sends the pfp of someone"""
        if not user:
            user = ctx.message.author

        await ctx.send(user.avatar_url)

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command()
    async def pfpmagik(self, ctx, user: Optional[discord.User] = None):
        """applies content aware scaling to someone's pfp"""
        if not user:
            user = ctx.message.author

        async with ctx.channel.typing():
            image_file = await magik.do_stuff(self.ll, self.session, str(user.avatar_url), "magik")
            await ctx.send(file=image_file)

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command()
    async def deepfry(self, ctx: commands.Context):
        """deepfry an image"""
        async with ctx.channel.typing():
            image_file = await magik.do_stuff(self.ll, self.session, ctx, "deepfry")
            await ctx.send(file=image_file)

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command()
    async def wide(self, ctx: commands.Context):
        """Horizonally stretch an image"""
        async with ctx.channel.typing():
            image_file = await magik.do_stuff(self.ll, self.session, ctx, "wide")
            await ctx.send(file=image_file)

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command()
    async def explode(self, ctx: commands.Context):
        """explode an image"""
        async with ctx.channel.typing():
            image_file = await magik.do_stuff(self.ll, self.session, ctx, "explode")
            await ctx.send(file=image_file)

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command()
    async def implode(self, ctx: commands.Context):
        """implode an image"""
        async with ctx.channel.typing():
            image_file = await magik.do_stuff(self.ll, self.session, ctx, "implode")
            await ctx.send(file=image_file)


    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command()
    async def swirl(self, ctx: commands.Context):
        """swirl an image"""
        async with ctx.channel.typing():
            image_file = await magik.do_stuff(self.ll, self.session, ctx, "swirl")
            await ctx.send(file=image_file)


    @commands.command()
    async def caption(self, ctx, *, text: str = ""):
        """Adds a caption to an image."""
        async with ctx.channel.typing():
            image_file = await magik.do_stuff(self.ll, self.session, ctx, "caption", text, self.dd)
            await ctx.send(file=image_file)

    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.command()
    async def gmagik(self, ctx: commands.Context, mode: str = "", *, ct: str = ""):
        """
        Syntax: gmagik <mode> [caption text]
        This command has multiple modes: `speedup`, `wide`, `caption`, `deepfry` and `magik`
        If no mode is supplied it defaults to `magik`
        Inspired by NotSoBot but with extra features and improvements
        """
        dry = False
        ll = self.ll
        p = join(self.dd, "DejaVuSans.ttf")

        async with ctx.channel.typing():
            # this just gets an image url to download
            image_url = await url_util.imageurlgetter(
                session=self.bot.aiohttp_session,
                history=ctx.channel.history(limit=30, around=datetime.now()),
                token=self.bot.tom.tenortoken,
                gif=True,
            )

            # download the image from the URL and send a message which indicates a successful download
            io = await url_util.imagedownloader(session=self.bot.aiohttp_session, url=image_url)
            pmsg = await ctx.send(f"This GIF has {len(io)} frames. Too many frames make the file too big for discord.")

            # when we speed the GIF up, we don't need any processing to be done, just double the framerate
            if not mode.lower() == "speedup":
                fps = io.get_meta_data()["duration"]
            else:
                # double the framerate and set the variable to bypass any processing
                fps = (io.get_meta_data()["duration"]) * 4
                dry = True

        async with ctx.channel.typing():
            # dict of possible functions to call
            fc = {
                "deepfry": magik.deepfry,
                "magik": magik.magik,
                "wide": magik.wide
            }

            # only process the frames if the dry variable is False
            if not dry:
                with ProcessPoolExecutor() as pool:
                    if not mode.lower() == "caption":
                        cf = fc.get(mode.lower(), magik.magik)  # get the right function for the set mode
                        # create a list of awaitable future objects
                        futures = [ll.run_in_executor(pool, cf, fra, fn) for fn, fra in enumerate(io)]
                    else:
                        futures = [ll.run_in_executor(pool, magik.caption, fra, fn, ct, p) for fn, fra in enumerate(io)]

                    # wait for the futures to finish and add them to the :io: list
                    # TODO: turn this into a list comprehension
                    io = []
                    for x in futures:
                        x = await x  # get the result of the future object
                        io.append([x[1], x[0]])

                io.sort(key=lambda fn: fn[0])  # this sorts the frame list by frame number :fn:
                io = [frame[1] for frame in io]  # we don't need the frame numbers anymore, just keep the image data

            with BytesIO() as image_buffer:
                imageio.mimwrite(image_buffer, io, fps=fps, format="gif")  # this writes the images to the image buffer
                image_buffer.seek(0)  # "rewind" the buffer. Otherwise the discord.File object can't see any image file
                # discord doesn't know what to do with an image_buffer object, that's why we need to convert it first
                image_file = discord.File(image_buffer, filename="gmagik.gif")

        await ctx.send(file=image_file)  # send the result to the channel where the command was sent
        await pmsg.delete()  # delete the "download successful" message from earlier


def setup(bot):
    bot.add_cog(ImageStuff(bot))
