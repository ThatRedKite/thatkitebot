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



#region Imports
import asyncio
from typing import Optional
from urllib.parse import urlparse, parse_qs, urlencode

import discord
from discord.ext import commands

from thatkitebot.base import util, image_stuff
from thatkitebot.base.image_stuff import ImageFunction
from thatkitebot.tkb_redis.settings import RedisFlags
from thatkitebot.base.util import EmbedColors as ec
from thatkitebot.base.url import get_avatar_url
#endregion

#region Cog
class ImageStuff(commands.Cog, name="image commands"):
    """
    Image commands for the bot. Can be disabled by the bot owner or an admin.
    """
    def __init__(self, bot):
        self.bot = bot
        self.datadir = bot.data_dir  # data directory

        self.session = bot.aiohttp_session

        self.loop = bot.loop
        self.sem = asyncio.Semaphore(12)
        self.process_pool = bot.process_pool

    async def cog_command_error(self, ctx, error):
        await util.errormsg(ctx, error)

    async def cog_check(self, ctx) -> bool:
        is_enabled = await RedisFlags.get_guild_flag(self.bot.redis, ctx.guild, RedisFlags.FlagEnum.IMAGE)
        can_attach = ctx.channel.permissions_for(ctx.author).attach_files
        can_embed = ctx.channel.permissions_for(ctx.author).embed_links
        return is_enabled and can_attach and can_embed

    def cog_unload(self):
        # make sure to cancel all futures before unloading
        if self.process_pool is not None:
            self.process_pool.shutdown(cancel_futures=True, wait=False)

    @commands.cooldown(3, 5, commands.BucketType.guild)
    @commands.command(aliases=["magic", "magick"])
    async def magik(self, ctx: commands.Context):
        """
        Applies some content aware and swirling scaling to an image.
        When the image is a GIF, it takes the first frame
        """
        print(RedisFlags.FlagEnum.IMAGE)
        buf = await image_stuff.download_last_image(ctx, aiohttp_session=self.session)
        async with ctx.channel.typing(), self.sem:
            image = ImageFunction(buf, 0, loop=self.loop, process_pool=self.process_pool)  # initialize the image class
            await image.magik()
            embed, file = await image.make_blob_close(name="magik")
            await ctx.reply(embed=embed, file=file, mention_author=False)
            file.close()

    @commands.cooldown(3, 5, commands.BucketType.guild)
    @commands.command(aliases=["swirlmagik", "smagic", "swirlmagic"])
    async def smagik(self, ctx: commands.Context, angle: float = 60.0):
        """
        Applies some content aware and swirling scaling to an image.
        When the image is a GIF, it takes the first frame
        """
        buf = await image_stuff.download_last_image(ctx, saiohttp_session=self.session)
        async with ctx.channel.typing(), self.sem:
            image = ImageFunction(buf, 1, loop=self.loop, process_pool=self.process_pool)  # initialize the image class
            await image.swirlmagik(angle)
            embed, file = await image.make_blob_close(name="smagik")
            await ctx.reply(embed=embed, file=file, mention_author=False)
            file.close()

    @commands.cooldown(3, 15, commands.BucketType.guild)
    @commands.command()
    async def deepfry(self, ctx: commands.Context):
        """'Deepfries' an image by oversaturating it and applying noise"""
        buf = await image_stuff.download_last_image(ctx, aiohttp_session=self.session)
        async with ctx.channel.typing(), self.sem:
            image = ImageFunction(buf, 2, loop=self.loop, process_pool=self.process_pool)  # initialize the image class
            await image.deepfry()
            embed, file = await image.make_blob_close(name="deepfry")
            await ctx.reply(embed=embed, file=file, mention_author=False)
            file.close()

    @commands.cooldown(3, 15, commands.BucketType.guild)
    @commands.command()
    async def wide(self, ctx: commands.Context):
        """Horizontally stretch an image"""
        buf = await image_stuff.download_last_image(ctx, aiohttp_session=self.session)
        async with ctx.channel.typing(), self.sem:
            image = ImageFunction(buf, 3, loop=self.loop, process_pool=self.process_pool)  # initialize the image class
            await image.wide()
            embed, file = await image.make_blob_close(name="wide")
            await ctx.reply(embed=embed, file=file, mention_author=False)
            file.close()

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["opacity"])
    async def opacify(self, ctx: commands.Context):
        """Remove the alpha channel and replace it with white"""
        buf = await image_stuff.download_last_image(ctx, aiohttp_session=self.session)
        async with ctx.channel.typing(), self.sem:
            image = ImageFunction(buf, 4, loop=self.loop, process_pool=self.process_pool)  # initialize the image class
            await image.opacify()
            embed, file = await image.make_blob_close(name="opacify")
            await ctx.reply(embed=embed, file=file, mention_author=False)
            file.close()

    @commands.cooldown(3, 10, commands.BucketType.user)
    @commands.command(aliases=["inflate"])
    async def explode(self, ctx: commands.Context, factor: float = 2.0):
        """Explodes an image"""
        buf = await image_stuff.download_last_image(ctx, aiohttp_session=self.session)
        async with ctx.channel.typing(), self.sem:
            image = ImageFunction(buf, 5, loop=self.loop, process_pool=self.process_pool)  # initialize the image class
            await image.explode(factor)
            embed, file = await image.make_blob_close(name="explode")
            await ctx.reply(embed=embed, file=file, mention_author=False)
            file.close()

    @commands.cooldown(3, 10, commands.BucketType.user)
    @commands.command(aliases=["deflate"])
    async def implode(self, ctx: commands.Context, factor: float = 1.0):
        """Implodes an image"""
        buf = await image_stuff.download_last_image(ctx, aiohttp_session=self.session)
        async with ctx.channel.typing(), self.sem:
            image = ImageFunction(buf, 6, loop=self.loop, process_pool=self.process_pool)  # initialize the image class
            await image.implode(factor)
            embed, file = await image.make_blob_close(name="implode")
            await ctx.reply(embed=embed, file=file, mention_author=False)
            file.close()

    @commands.cooldown(3, 10, commands.BucketType.user)
    @commands.command(aliases=["inverse", "anti"])
    async def invert(self, ctx: commands.Context):
        """Invert an image's colors"""
        buf = await image_stuff.download_last_image(ctx, aiohttp_session=self.session)
        async with ctx.channel.typing(), self.sem:
            image = ImageFunction(buf, 7, loop=self.loop, process_pool=self.process_pool)  # initialize the image class
            await image.invert()
            embed, file = await image.make_blob_close(name="invert")
            await ctx.reply(embed=embed, file=file, mention_author=False)
            file.close()

    @commands.cooldown(3, 10, commands.BucketType.user)
    @commands.command()
    async def reduce(self, ctx: commands.Context):
        """Reduces an image's total colors"""
        buf = await image_stuff.download_last_image(ctx, aiohttp_session=self.session)
        async with ctx.channel.typing(), self.sem:
            image = ImageFunction(buf, 8, loop=self.loop, process_pool=self.process_pool)  # initialize the image class
            await image.reduce()
            embed, file = await image.make_blob_close(name="reduce")
            await ctx.reply(embed=embed, file=file, mention_author=False)
            file.close()

    @commands.cooldown(3, 10, commands.BucketType.user)
    @commands.command()
    async def swirl(self, ctx: commands.Context, angle: int = 60):
        """Swirl an image"""
        buf = await image_stuff.download_last_image(ctx, aiohttp_session=self.session)
        async with ctx.channel.typing(), self.sem:
            image = ImageFunction(buf, 9, loop=self.loop, process_pool=self.process_pool)  # initialize the image class
            await image.swirl(angle)
            embed, file = await image.make_blob_close(name="swirl")
            await ctx.reply(embed=embed, file=file, mention_author=False)
            file.close()

    @commands.cooldown(3, 15, commands.BucketType.user)
    @commands.command()
    async def caption(self, ctx, *, text: str = ""):
        """
        Adds a caption to an image. You can add `color:` to the message to change text color using hex or decimal RGB values.
        Example: \n `caption funny color:ff2315` or  `caption funny color:255,123,22` or `caption funny color:firebrick`
        A full list of colors can be found here: https://imagemagick.org/script/color.php
        """
        buf = await image_stuff.download_last_image(ctx, aiohttp_session=self.session)
        async with ctx.channel.typing(), self.sem:
            image = ImageFunction(buf, 10, loop=self.loop, process_pool=self.process_pool)  # initialize the image class
            await image.caption(text=text, path="/app/data/static-resources/")
            embed, file = await image.make_blob_close(name="caption")
            await ctx.reply(embed=embed, file=file, mention_author=False)
            file.close()

    @commands.cooldown(5, 10, commands.BucketType.user)
    @commands.command()
    async def rotate(self, ctx: commands.Context, angle: int = 90):
        """Rotate an image clockwise 90 degrees by default, you can specify the degree value as an argument"""
        buf = await image_stuff.download_last_image(ctx, aiohttp_session=self.session)
        async with ctx.channel.typing(), self.sem:
            image = ImageFunction(buf, 11, loop=self.loop, process_pool=self.process_pool)  # initialize the image class
            await image.rotate(angle)
            embed, file = await image.make_blob_close(name="rotate")
            await ctx.reply(embed=embed, file=file, mention_author=False)
            file.close()

    @commands.cooldown(5, 10, commands.BucketType.user)
    @commands.command(aliases=["bw", "blackwhite"])
    async def grey(self, ctx: commands.Context):
        """Make an image black and white"""
        buf = await image_stuff.download_last_image(ctx, aiohttp_session=self.session)
        async with ctx.channel.typing(), self.sem:
            image = ImageFunction(buf, 12, loop=self.loop, process_pool=self.process_pool)  # initialize the image class
            await image.black_white()
            embed, file = await image.make_blob_close(name="blackwhite")
            await ctx.reply(embed=embed, file=file, mention_author=False)
            file.close()

    @commands.cooldown(5, 10, commands.BucketType.user)
    @commands.command(aliases=["piss"])
    async def sepia(self, ctx: commands.Context, threshold: float = 0.8):
        """Add a sepia filter to an image"""
        buf = await image_stuff.download_last_image(ctx, aiohttp_session=self.session)
        async with ctx.channel.typing(), self.sem:
            image = ImageFunction(buf, 13, loop=self.loop, process_pool=self.process_pool)  # initialize the image class
            await image.sepia()
            embed, file = await image.make_blob_close(name="sepia")
            await ctx.reply(embed=embed, file=file, mention_author=False)
            file.close()

    @commands.cooldown(5, 10, commands.BucketType.user)
    @commands.command()
    async def polaroid(self, ctx: commands.Context):
        """Add a polaroid filter to an image"""
        buf = await image_stuff.download_last_image(ctx, aiohttp_session=self.session)
        async with ctx.channel.typing(), self.sem:
            image = ImageFunction(buf, 14, loop=self.loop, process_pool=self.process_pool)  # initialize the image class
            await image.polaroid()
            embed, file = await image.make_blob_close(name="polaroid")
            await ctx.reply(embed=embed, file=file, mention_author=False)
            file.close()

    @commands.cooldown(5, 10, commands.BucketType.user)
    @commands.command(aliases=["coal"])
    async def charcoal(self, ctx: commands.Context, radius: float = 1.5, sigma: float = 0.5):
        """Add a charcoal filter to an image, making it look like a charcoal drawing"""
        buf = await image_stuff.download_last_image(ctx, aiohttp_session=self.session)
        async with ctx.channel.typing(), self.sem:
            image = ImageFunction(buf, 15, loop=self.loop, process_pool=self.process_pool)  # initialize the image class
            await image.charcoal(radius, sigma)
            embed, file = await image.make_blob_close(name="charcoal")
            await ctx.reply(embed=embed, file=file, mention_author=False)
            file.close()

    @commands.cooldown(5, 10, commands.BucketType.user)
    @commands.command()
    async def vignette(self, ctx: commands.Context, sigma: int = 3, x: int = 10, y: int = 10):
        """Tries to emulate old school 3d effect"""
        buf = await image_stuff.download_last_image(ctx, aiohttp_session=self.session)
        async with ctx.channel.typing(), self.sem:
            image = ImageFunction(buf, 16, loop=self.loop, process_pool=self.process_pool)  # initialize the image class
            await image.make_vignette(sigma, x , y)
            embed, file = await image.make_blob_close(name="vignette")
            await ctx.reply(embed=embed, file=file, mention_author=False)
            file.close()

    @commands.cooldown(5, 10, commands.BucketType.user)
    @commands.command(aliases=["bubble"])
    async def speech_bubble(self, ctx: commands.Context, flip: bool = False):
        """Create a speech bubble like those memes"""
        buf = await image_stuff.download_last_image(ctx, aiohttp_session=self.session)
        async with ctx.channel.typing(), self.sem:
            image = ImageFunction(buf, 17, loop=self.loop, process_pool=self.process_pool)  # initialize the image class
            await image.bubble()
            embed, file = await image.make_blob_close(name="bubble", gif=True)
            await ctx.reply(embed=embed, file=file, mention_author=False)
            file.close()

    @commands.cooldown(5, 10, commands.BucketType.user)
    @commands.command(aliases=["scale"])
    async def resize(self, ctx: commands.Context, scale: float = 0.5):
        """Resizes an image to a set factor"""
        buf = await image_stuff.download_last_image(ctx, aiohttp_session=self.session)
        async with ctx.channel.typing(), self.sem:
            image = ImageFunction(buf, 18, loop=self.loop, process_pool=self.process_pool)  # initialize the image class
            await image.scale(scale)
            embed, file = await image.make_blob_close(name="resize")
            await ctx.reply(embed=embed, file=file, mention_author=False)
            file.close()

    @commands.cooldown(5, 10, commands.BucketType.user)
    @commands.command()
    async def blur(self, ctx: commands.Context, radius: int = 0, sigma: int = 3):
        """Applies blur"""
        buf = await image_stuff.download_last_image(ctx, aiohttp_session=self.session)
        async with ctx.channel.typing(), self.sem:
            image = ImageFunction(buf, 19, loop=self.loop, process_pool=self.process_pool)  # initialize the image class
            await image.blur(radius, sigma)
            embed, file = await image.make_blob_close(name="blur")
            await ctx.reply(embed=embed, file=file, mention_author=False)
            file.close()

    @commands.cooldown(5, 10, commands.BucketType.user)
    @commands.command(aliases=["ablur"])
    async def adaptive_blur(self, ctx: commands.Context, radius: int = 0, sigma: int = 3):
        """Applies blur, but tries to utilize edge detect for a better result"""
        buf = await image_stuff.download_last_image(ctx, aiohttp_session=self.session)
        async with ctx.channel.typing(), self.sem:
            image = ImageFunction(buf, 20, loop=self.loop, process_pool=self.process_pool)  # initialize the image class
            await image.adaptive_blur(radius, sigma)
            embed, file = await image.make_blob_close(name="ablur")
            await ctx.reply(embed=embed, file=file, mention_author=False)
            file.close()

    @commands.cooldown(5, 10, commands.BucketType.user)
    @commands.command(aliases=["mblur"])
    async def motion_blur(self, ctx: commands.Context, radius: int = 0, sigma: int = 3, angle: int = -45):
        """Applies motion blur"""
        buf = await image_stuff.download_last_image(ctx, aiohttp_session=self.session)
        async with ctx.channel.typing(), self.sem:
            image = ImageFunction(buf, 21, loop=self.loop, process_pool=self.process_pool)  # initialize the image class
            await image.motion_blur(radius, sigma, angle)
            embed, file = await image.make_blob_close(name="motion_blur")
            await ctx.reply(embed=embed, file=file, mention_author=False)
            file.close()

    @commands.cooldown(5, 10, commands.BucketType.user)
    @commands.command()
    async def edge(self, ctx: commands.Context, radius: int = 1):
        """Returns a black and white image with edges in white and the rest in black"""
        buf = await image_stuff.download_last_image(ctx, aiohttp_session=self.session)
        async with ctx.channel.typing(), self.sem:
            image = ImageFunction(buf, 22, loop=self.loop, process_pool=self.process_pool)  # initialize the image class
            await image.edge(radius)
            embed, file = await image.make_blob_close(name="edge")
            await ctx.reply(embed=embed, file=file, mention_author=False)
            file.close()

    @commands.cooldown(5, 10, commands.BucketType.user)
    @commands.command()
    async def emboss(self, ctx: commands.Context, radius: float = 3.0, sigma: float = 1.75):
        """Creates an embossed image"""
        buf = await image_stuff.download_last_image(ctx, aiohttp_session=self.session)
        async with ctx.channel.typing(), self.sem:
            image = ImageFunction(buf, 23, loop=self.loop, process_pool=self.process_pool)  # initialize the image class
            await image.emboss(radius, sigma)
            embed, file = await image.make_blob_close(name="emboss")
            await ctx.reply(embed=embed, file=file, mention_author=False)
            file.close()

    @commands.cooldown(5, 10, commands.BucketType.user)
    @commands.command(aliases=["smooth"])
    async def kuwahara(self, ctx: commands.Context, radius: int = 1, sigma: float = 1.5):
        """Attempts to smooth the image while preserving edges"""
        buf = await image_stuff.download_last_image(ctx, aiohttp_session=self.session)
        async with ctx.channel.typing(), self.sem:
            image = ImageFunction(buf, 24, loop=self.loop, process_pool=self.process_pool)  # initialize the image class
            await image.kuwahara(radius, sigma)
            embed, file = await image.make_blob_close(name="kuwahara")
            await ctx.reply(embed=embed, file=file, mention_author=False)
            file.close()

    @commands.cooldown(5, 10, commands.BucketType.user)
    @commands.command()
    async def shade(self, ctx: commands.Context, gray: bool = True, azimuth: float = 286.0, elevation: float = 45.0):
        """Attempts to smooth the image while preserving edges"""
        buf = await image_stuff.download_last_image(ctx, aiohttp_session=self.session)
        async with ctx.channel.typing(), self.sem:
            image = ImageFunction(buf, 25, loop=self.loop, process_pool=self.process_pool)  # initialize the image class
            await image.shade(gray, azimuth, elevation)
            embed, file = await image.make_blob_close(name="shade")
            await ctx.reply(embed=embed, file=file, mention_author=False)
            file.close()

    @commands.cooldown(3, 10, commands.BucketType.channel)
    @commands.command()
    async def pfp(self, ctx, user: Optional[discord.Member] = None):
        """This sends someone's profile picture"""
        if user is None:
            user = ctx.author
        embed = discord.Embed(title=f"{user.name}'s profile picture", color=user.color)
        embed.set_image(url=get_avatar_url(user))
        await ctx.reply(embed=embed, mention_author=False)

    @commands.cooldown(3, 10, commands.BucketType.guild)
    @commands.command(aliases=["banner", "profilebanner"])
    async def pfbanner(self, ctx, user: Optional[discord.Member] = None):
        """This sends someone's profile banner"""
        if user is None:
            user = ctx.author
        embed = discord.Embed(title=f"{user.name}'s profile banner", color=user.color)
        # fetch user
        user = await self.bot.fetch_user(user.id)
        if user.banner:
            url = urlparse(user.banner.url)
            query = parse_qs(url.query, keep_blank_values=True)
            # set the size to 2048
            query["size"] = "2048"
            # reassemble the url
            url = url._replace(query=urlencode(query, True))
            embed.set_image(url=url.geturl())
        else:
            # if there is no banner, send a message with the user color as an accent color
            embed.description = f"{user.name} doesn't have a profile banner."
            if user.accent_color:
                embed.color = user.accent_color
                embed.set_footer(text="The profile accent color is: " + str(user.accent_color))
            else:
                embed.color = user.color
        await ctx.reply(embed=embed, mention_author=False)

    @commands.cooldown(3, 10, commands.BucketType.guild)
    @commands.command()
    async def serverpfp(self, ctx, user: Optional[discord.Member] = None):
        """This sends the users server icon"""
        if user is None:
            user = ctx.author
        embed = discord.Embed(title=f"{user.name}'s server icon", color=user.color)
        if user.display_avatar:
            embed.set_image(url=user.display_avatar)
        else:
            embed.description = "This user doesn't have a profile picture."
        await ctx.reply(embed=embed, mention_author=False)

    @commands.cooldown(3, 10, commands.BucketType.guild)
    @commands.command(aliases=["emote"])
    async def emoji(self, ctx, emoji: discord.Emoji):
        """This sends an emote as an image"""
        embed = discord.Embed(title=f"{emoji.name}", color=ec.lime_green)
        embed.set_image(url=emoji.url)
        await ctx.reply(embed=embed, mention_author=False)
#endregion

def setup(bot):
    bot.add_cog(ImageStuff(bot))
