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

import argparse
import gc
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from datetime import datetime
from functools import partial
from io import BytesIO
from os.path import join
from queue import Queue
from random import choice
import discord
import imageio
from PIL import Image, ImageDraw, ImageFont
from discord.ext import commands
from wand.image import Image as WandImage
from backend import util, magik
from backend import url as url_util
from cogs.funstuffcog import mark


# an argparse parser that does not terminate the program when an error occurs
class NoExitParser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


def deepfried(buffer):
    buffer.seek(0)
    with WandImage(file=buffer) as img:
        # increase the saturation and att some noise
        img.modulate(saturation=500.00)
        img.noise("gaussian", attenuate=0.1)
        with BytesIO() as outbuffer:
            img.save(file=outbuffer)
            outbuffer.seek(0)
            image_file = discord.File(outbuffer, filename="deepfried.png")
            img.destroy()

        buffer.close()
        del img, outbuffer
        embed = discord.Embed()
        embed.set_image(url="attachment://deepfried.png")
    gc.collect()
    return embed, image_file


def do_magik(buffer: BytesIO):
    buffer.seek(0)
    with WandImage(file=buffer) as i:
        i.alpha_channel = True
        height, width = i.height, i.width

        i.liquid_rescale(width=int(i.width * 0.5), height=int(i.height * 0.5), delta_x=1, rigidity=0)
        i.liquid_rescale(width=int(i.width * 1.89), height=int(i.height * 1.89), delta_x=2, rigidity=0)

        i.resize(width, height)
        with BytesIO() as outbuffer:
            i.save(file=outbuffer)
            outbuffer.seek(0)
            image_file = discord.File(outbuffer, filename="magik.png")
            i.destroy()

        del i, outbuffer
        buffer.close()
        embed = discord.Embed()
        embed.set_image(url="attachment://magik.png")
    gc.collect()
    return embed, image_file


def make_wide(buffer):
    buffer.seek(0)
    with WandImage(file=buffer) as img:
        img.resize(width=int(img.width * 3), height=int(img.height / 1.7))
        img.crop(
            left=int(img.width / 4),
            top=1,
            right=(img.width - (int(img.width / 4.3))),
            bottom=img.height,
        )
        with BytesIO() as outbuffer:
            img.save(file=outbuffer)
            outbuffer.seek(0)
            image_file = discord.File(outbuffer, filename="wide.png")
            img.destroy()

        embed = discord.Embed()
        embed.set_image(url="attachment://wide.png")
        buffer.close()
        del img, outbuffer
        gc.collect()
        return embed, image_file


def quoter(buffer, chan, path, quotestring):
    buffer.seek(0)
    with Image.open(buffer) as im:
        draw = ImageDraw.Draw(im)
        if im.size <= (512, 512):
            outline_width = 1
        else:
            outline_width = 3
        x, y = im.size
        fontsize = int(x / (int(len(quotestring) / 2) + outline_width))
        font = ImageFont.truetype(join(path, "DejaVuSans.ttf"), fontsize)
        quotestring += f"\n-{chan.name}"
        draw.text(
            (4 - outline_width, (y - int(y / 5)) - outline_width),
            quotestring,
            (0, 0, 0),
            font=font,
        )
        draw.text(
            (4 + outline_width, (y - int(y / 5)) + outline_width),
            quotestring,
            (0, 0, 0),
            font=font,
        )
        draw.text(
            (4 - outline_width, (y - int(y / 5)) + outline_width),
            quotestring,
            (0, 0, 0),
            font=font,
        )
        draw.text(
            (4 + outline_width, (y - int(y / 5)) - outline_width),
            quotestring,
            (0, 0, 0),
            font=font,
        )
        draw.text(
            (4, (y - int(y / 5)) - outline_width),
            quotestring,
            (255, 255, 555),
            font=font,
        )
        im = im.convert("RGBA")

        with BytesIO() as outbuffer:
            im.save(outbuffer)
            im.destroy()
            del draw, x, y, fontsize, font, quotestring
            file = discord.File(outbuffer, filename="pfp_edit.png")
            embed = discord.Embed()
            embed.set_image(url="attachment://pfp_edit.png")
        buffer.close()
        del buffer
        gc.collect()
        return embed, file


class image_stuff(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.td = bot.tempdir  # temp directory
        self.dd = bot.datadir  # data directory

        # compile the patterns for someregexes
        self.gifpattern = re.compile("(^https?://\S+.(gif))")  # only gif images
        # detects PNG, JPEG, WEBP and GIF images
        self.otherpattern = re.compile("(^https?://\S+.(?i)(png|webp|gif|jpe?g))")
        # gets the ID of a tenor GIF from its URL
        self.tenorpattern = re.compile("^https://tenor.com\S+-(\d+)$")

    async def image_url_fetcher(
            self, ctx, api_token: str = None, bypass=False, gif=False
    ):
        # when bypass is True, the ctx variable is actually treated as a plain string
        # instead of a commands.Context object. This is needed, if you already have the URL
        # and you just want to download it, it bypasses the url detection routines
        if not bypass:
            # select the appropriate pattern
            if gif:
                pattern = self.gifpattern
            else:
                pattern = self.otherpattern

            # iterate over the last 50 messages in current channel and look for image links
            async for message in ctx.channel.history(limit=50, around=datetime.now()):
                # a list of the message's attachments
                attachments = message.attachments
                if attachments:
                    found_url = pattern.findall(attachments[0].url)
                    if found_url:
                        url, fe = found_url[0]
                        break  # break the loop, a valid url has been found
                else:
                    # found_url is a list of all urls the regex found,
                    # this should only be one value, or no value at all
                    found_url = pattern.findall(message.clean_content)
                    # the tenor ID of the GIF.It only contains anything, if there actually is a tenor GIF
                    tenor = self.tenorpattern.findall(message.clean_content)
                    if found_url and not tenor:
                        # unpack the url and the file extension
                        url, fe = found_url[0]
                        break  # break the loop, a valid url has been found
                    elif tenor:
                        # define the header and the payload
                        headers = {
                            "User-Agent": "ThatKiteBot/2.3.4",
                            "content-type": "application/json",
                        }
                        payload = {
                            "key": api_token,
                            "ids": int(tenor[0]),
                            "media_filter": "minimal",
                        }

                        async with self.bot.aiohttp_session.get(
                                url="https://api.tenor.com/v1/gifs",
                                params=payload,
                                headers=headers,
                        ) as r:
                            gifs = await r.json()
                        # some dictionary magic to get the source url of the gif
                        url = str(gifs["results"][0]["media"][0]["gif"]["url"])
                        assert url
                        break  # break the loop, a valid url has been found
        else:
            url = str(ctx)

        async with self.bot.aiohttp_session.get(url) as r:
            inbuffer = BytesIO(await r.read())
            # gifs should not be converted to PNG
            #
            if not gif:
                inbuffer.seek(0)
                with Image.open(inbuffer) as img:
                    outbuffer = BytesIO()
                    # convert the image to RGBA and PNG
                    with img.convert("RGBA") as outimg:
                        outbuffer.seek(0)
                        outimg.save(outbuffer, "png")
                return outbuffer
            else:
                # this just seeks the buffer to 0
                # and then returns the buffer without altering it
                inbuffer.seek(0)
                gc.collect()
                return inbuffer

    async def captioner(self, buffer, text, size):

        buffer.seek(0)
        with Image.open(buffer) as img:
            outline_width = 3

            W, H = img.size
            font = ImageFont.truetype(join(self.td, "DejaVuSans.ttf"), size=size)
            w, h = font.getsize(text)
            img = img.convert("RGB")
            draw = ImageDraw.Draw(img)

            draw.text(
                ((W - w) / 2 - outline_width, int((H - h) / 1.15) - outline_width),
                text,
                fill="black",
                font=font,
            )
            draw.text(
                ((W - w) / 2 - outline_width, int((H - h) / 1.15) + outline_width),
                text,
                fill="black",
                font=font,
            )
            draw.text(
                ((W - w) / 2 + outline_width, int((H - h) / 1.15) - outline_width),
                text,
                fill="black",
                font=font,
            )
            draw.text(
                ((W - w) / 2 + outline_width, int((H - h) / 1.15) + outline_width),
                text,
                fill="black",
                font=font,
            )

            draw.text(((W - w) / 2, int((H - h) / 1.15)), text, fill="white", font=font)

            with BytesIO() as outbuffer:
                img.save(outbuffer, "JPEG", quality=100)
                outbuffer.seek(0)
                file = discord.File(outbuffer, filename="caption.jpeg")
                embed = discord.Embed()
                embed.set_image(url="attachment://caption.jpeg")
                gc.collect()
                return embed, file

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command()
    async def quote(self, ctx,user="dsad",old: int = 100,new: int = 100):
        """Generates a fake quote of a user using a markov chain"""
        with ctx.channel.typing():
            generated_list, chan = await mark(
                bot=self.bot,
                ctx=ctx,
                user=user,
                old=old,
                new=new,
                leng=5,
                leng2=30,
                mode="short",
            )

            # download the profile picture of the user
            buffer = await self.image_url_fetcher(ctx=chan.avatar_url, bypass=True)
            with ThreadPoolExecutor() as executor:
                if generated_list:
                    quotestring = choice(generated_list)
                    embed, file = await self.bot.loop.run_in_executor(
                        executor, quoter, buffer, chan, self.td, quotestring
                    )
            await ctx.send(file=file, embed=embed)
            del buffer, embed, file

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command()
    async def magik(self, ctx: commands.Context):
        """Applies some content aware scaling to an image. When the image is a GIF, it takes the first frame"""
        with ctx.channel.typing():
            buffer = await self.image_url_fetcher(ctx=ctx, api_token=self.bot.tom.tenortoken)
            with ThreadPoolExecutor(4) as executor:
                embed, image_file = await self.bot.loop.run_in_executor(executor, do_magik, buffer)
                executor.shutdown()
            await ctx.send(file=image_file)
            del buffer, embed, image_file

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command()
    async def widepfp(self, ctx: commands.Context, usermention="transfergesetz"):
        """sends a horizontally stretched version of someonme's profile picture"""
        with ctx.channel.typing():
            message = ctx.message
            chan, is_user, is_channel = util.mentioner(
                self.bot, ctx, message, usermention, False
            )
            buffer = await self.image_url_fetcher(ctx=chan.avatar_url, bypass=True)
            with ThreadPoolExecutor(4) as executor:
                embed, image_file = await self.bot.loop.run_in_executor(
                    executor, make_wide, buffer
                )
            await ctx.send(file=image_file)
            del buffer, embed, image_file

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command()
    async def pfp(self, ctx, usermention="passatwind"):
        """sends the pfp of someone"""
        message = ctx.message
        chan, is_user, is_channel = util.mentioner(
            self.bot, ctx, message, usermention, False
        )
        buffer = await self.image_url_fetcher(ctx=chan.avatar_url, bypass=True)
        buffer.seek(0)
        image_file = discord.File(buffer, filename="pfp.png")
        await ctx.send(file=image_file)
        del buffer, image_file

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command()
    async def pfpmagik(self, ctx, usermention="nonetti"):
        """applies content aware scaling to someone's pfp"""
        with ctx.channel.typing():
            message = ctx.message
            chan, is_user, is_channel = util.mentioner(
                self.bot, ctx, message, usermention, False
            )
            buffer = await self.image_url_fetcher(ctx=chan.avatar_url, bypass=True)
            with ThreadPoolExecutor() as executor:
                embed, image_file = await self.bot.loop.run_in_executor(
                    executor, do_magik, buffer
                )
            await ctx.send(file=image_file)
            del buffer, embed, image_file

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command()
    async def deepfry(self, ctx: commands.Context):
        """deepfry an image"""
        with ctx.channel.typing():
            buffer = await self.image_url_fetcher(
                ctx=ctx, api_token=self.bot.tom.tenortoken
            )
            with ThreadPoolExecutor() as executor:
                embed, image_file = await self.bot.loop.run_in_executor(
                    executor, deepfried, buffer
                )
            await ctx.send(file=image_file)
            del buffer, embed, image_file

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command()
    async def wide(self, ctx: commands.Context):
        """Horizonally stretch an image"""
        with ctx.channel.typing():
            buffer = await self.image_url_fetcher(
                ctx=ctx, api_token=self.bot.tom.tenortoken
            )
            with ThreadPoolExecutor() as executor:
                embed, image_file = await self.bot.loop.run_in_executor(
                    executor, make_wide, buffer
                )
            await ctx.send(file=image_file)
            del buffer, embed, image_file

    @commands.command()
    async def caption(self, ctx, *, text: str = ""):
        """Adds a caption to an image."""
        with ctx.channel.typing():
            buffer = await self.image_url_fetcher(
                gif=False, ctx=ctx, api_token=self.bot.tom.tenortoken
            )
            embed, image_file = await self.captioner(buffer, text, size=64)
        await ctx.send(file=image_file)
        del buffer, embed, image_file

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
        ll = self.bot.loop
        p = join(self.dd, "DejaVuSans.ttf")

        with ctx.channel.typing():
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
                fps = (io.get_meta_data()["duration"]) * 2
                dry = True

        with ctx.channel.typing():
            # dict of possible functions to call
            fc = {
                "deepfry": magik.deepfry,
                "magik": magik.magik,
                "wide": magik.wide,
            }

            # only process the frames if the dry variable is False
            if not dry:
                with ProcessPoolExecutor() as pool:
                    if not mode.lower() == "caption":
                        cf = fc.get(mode.lower(), magik.magik)  # get the right function for the set mode
                        # create a list of awaitable future objects
                        futures = [ll.run_in_executor(pool, cf, fra, fn) for fn, fra in enumerate(io)]
                    else:
                        futures = [ll.run_in_executor(pool, magik.caption, fra, fn, ct, p)for fn, fra in enumerate(io)]

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
