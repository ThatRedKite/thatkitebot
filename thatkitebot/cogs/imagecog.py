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
from functools import partial
from typing import Optional
from urllib.parse import urlparse, parse_qs, urlencode
from typing import Callable

import discord
from discord.ext import commands

from thatkitebot.base import util, image_stuff
from thatkitebot.base.image_stuff import ImageFunction
from thatkitebot.tkb_redis.settings import RedisFlags
from thatkitebot.base.util import EmbedColors as ec
from thatkitebot.base.url import get_avatar_url
#endregion

def image_command(*args, **kwargs):
    def deco(func: Callable):
        # set filename to function name
        name = func.__code__.co_name

        @commands.cooldown(4, 10, commands.BucketType.user)
        async def wrapper(self, ctx: commands.Context,*args):
            file = None
            async with ctx.typing():
                try:
                    buf = await image_stuff.download_last_image(ctx, aiohttp_session=self.session)
                    image = ImageFunction(buf, 0, loop=self.loop, process_pool=self.process_pool)
                    
                    await func(self, ctx, image, *args)
                    
                    embed, file = await image.make_blob_close(name)
                    print(embed)
                    await ctx.reply(embed=embed, file=file, mention_author=False)
                    
                finally:
                    # close all the stuff
                    buf.close()
                    if file is not None:
                        file.close()
                    image.image.destroy()
                    
        # fix default command name
        if not kwargs.get("name"):
            kwargs.update({"name": name})

        command: commands.Command = commands.command(*args, **kwargs)(wrapper)

        return command
    
    return deco

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


    async def cog_check(self, ctx) -> bool:
        is_enabled = await RedisFlags.get_guild_flag(self.bot.redis, ctx.guild, RedisFlags.FlagEnum.IMAGE)
        can_attach = ctx.channel.permissions_for(ctx.author).attach_files
        can_embed = ctx.channel.permissions_for(ctx.author).embed_links
        return is_enabled and can_attach and can_embed

    def cog_unload(self) -> None:
        # make sure to cancel all futures before unloading
        if self.process_pool is not None:
            self.process_pool.shutdown(cancel_futures=True, wait=False)

    
    @image_command(name="magik", aliases=["magic", "magick"])
    async def magik(self, ctx: commands.Context, image: ImageFunction,) -> None:
        """
        Applies some content aware and swirling scaling to an image.
        When the image is a GIF, it takes the first frame
        """
        await image.magik()

    @image_command(name="swirlmagik", aliases=["smagik", "smagick"])
    async def smagik(self, ctx: commands.Context, image: ImageFunction, angle:float = 60) -> None:
        """
        Applies some content aware and swirling scaling to an image.
        When the image is a GIF, it takes the first frame
        """
        await image.swirlmagik(angle)

    @image_command(name="deepfry")
    async def deepfry(self, ctx: commands.Context, image: ImageFunction) -> None:
        """'Deepfries' an image by oversaturating it and applying noise"""
        await image.deepfry()

    @image_command(name="wide")
    async def wide(self, ctx: commands.Context, image: ImageFunction) -> None:
        """Horizontally stretch an image"""
        await image.wide()

    @image_command(name="opacify")
    async def opacify(self, ctx: commands.Context, image: ImageFunction) -> None:
        """Remove the alpha channel and replace it with white"""
        await image.opacify()

    @image_command(aliases=["inflate"])
    async def explode(self, ctx: commands.Context, image: ImageFunction, factor: float = 2.0) -> None:
        """Explodes an image"""
        await image.explode(factor)


    @image_command(aliases=["deflate"])
    async def implode(self, ctx: commands.Context, image: ImageFunction, factor: float = 1.0) -> None:
        """Implodes an image"""
        await image.implode(factor)

    
    @image_command()
    async def invert(self, ctx: commands.Context, image: ImageFunction) -> None:
        """Invert an image's colors"""
        await image.invert()


    @image_command()
    async def reduce(self, ctx: commands.Context, image: ImageFunction) -> None:
        """Reduces an image's total colors"""
        await image.reduce()

    @image_command()
    async def swirl(self, ctx: commands.Context, image: ImageFunction, angle: int = 60) -> None:
        """Swirl an image"""
        await image.swirl(angle)


    @image_command()
    async def caption(self, ctx, image: ImageFunction, text: str = "", color: str = "") -> None:
        """
        Adds a caption to an image. You can add `color:` to the message to change text color using hex or decimal RGB values.
        Example: \n `caption funny color:ff2315` or  `caption funny color:255,123,22` or `caption funny color:firebrick`
        A full list of colors can be found here: https://imagemagick.org/script/color.php
        """
        print(text)
        await image.caption(text=f"{text} {color}", path="/app/data/static-resources/")


    @image_command()
    async def rotate(self, ctx: commands.Context, image: ImageFunction, angle:float = 90) -> None:
        """Rotate an image clockwise 90 degrees by default, you can specify the degree value as an argument"""
        await image.rotate(angle)
 
    @image_command(aliases=["bw", "blackwhite"])
    async def grey(self, ctx: commands.Context, image: ImageFunction) -> None:
        """Make an image black and white"""
        await image.black_white()

    @image_command(aliases=["piss"])
    async def sepia(self, ctx: commands.Context, image: ImageFunction, threshold: float = 0.8) -> None:
        """Add a sepia filter to an image"""
        await image.sepia(threshold)

    @image_command()
    async def polaroid(self, ctx: commands.Context, image: ImageFunction) -> None:
        """Add a polaroid filter to an image"""
        await image.polaroid()

    @image_command(aliases=["coal"])
    async def charcoal(self, ctx: commands.Context, image: ImageFunction, radius: float = 1.5, sigma: float = 0.5) -> None:
        """Add a charcoal filter to an image, making it look like a charcoal drawing"""
        await image.charcoal(radius, sigma)

    @image_command()
    async def vignette(self, ctx: commands.Context, image: ImageFunction, sigma: int = 3, x: int = 10, y: int = 10) -> None:
        """Tries to emulate old school 3d effect"""
        await image.make_vignette(sigma, x , y)

    @image_command(aliases=["bubble"])
    async def speech_bubble(self, ctx: commands.Context, image: ImageFunction, flip: bool = False) -> None:
        """Create a speech bubble like those memes"""
        await image.bubble(flip)

    @image_command(aliases=["scale"])
    async def resize(self, ctx: commands.Context, image: ImageFunction, scale: float = 0.5) -> None:
        """Resizes an image to a set factor"""
        await image.scale(scale)

    @image_command()
    async def blur(self, ctx: commands.Context, image: ImageFunction, radius: int = 0, sigma: int = 3) -> None:
        """Applies blur"""
        await image.blur(radius, sigma)

    @image_command(aliases=["ablur"])
    async def adaptive_blur(self, ctx: commands.Context, image: ImageFunction, radius: int = 0, sigma: int = 3) -> None:
        """Applies blur, but tries to utilize edge detect for a better result"""
        await image.adaptive_blur(radius, sigma)

    @image_command(aliases=["mblur"])
    async def motion_blur(self, ctx: commands.Context, image: ImageFunction, radius: int = 0, sigma: int = 3, angle: int = -45) -> None:
        """Applies motion blur"""
        await image.motion_blur(radius, sigma, angle)

    @image_command()
    async def edge(self, ctx: commands.Context, image: ImageFunction, radius: int = 1) -> None:
        """Returns a black and white image with edges in white and the rest in black"""
        await image.edge(radius)

    @image_command()
    async def emboss(self, ctx: commands.Context, image: ImageFunction, radius: float = 3.0, sigma: float = 1.75) -> None:
        """Creates an embossed image"""

        await image.emboss(radius, sigma)


    @image_command()
    async def shade(self, ctx: commands.Context, image: ImageFunction, gray: bool = True, azimuth: float = 286.0, elevation: float = 45.0) -> None:
        """Attempts to smooth the image while preserving edges"""
        await image.shade(gray, azimuth, elevation)

    @commands.cooldown(3, 10, commands.BucketType.channel)
    @commands.command()
    async def pfp(self, ctx, user: Optional[discord.Member] = None) -> None:
        """This sends someone's profile picture"""
        if user is None:
            user = ctx.author
        embed = discord.Embed(title=f"{user.name}'s profile picture", color=user.color)
        embed.set_image(url=get_avatar_url(user))
        await ctx.reply(embed=embed, mention_author=False)

    @commands.cooldown(3, 10, commands.BucketType.guild)
    @commands.command(aliases=["banner", "profilebanner"])
    async def pfbanner(self, ctx, user: Optional[discord.Member] = None) -> None:
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
            elif user.color:
                embed.color = user.color
                embed.set_footer(text="The user color is: " + str(user.color))

        await ctx.reply(embed=embed, mention_author=False)

    @commands.cooldown(3, 10, commands.BucketType.guild)
    @commands.command()
    async def serverpfp(self, ctx, user: Optional[discord.Member] = None) -> None:
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

def setup(bot) -> None:
    bot.add_cog(ImageStuff(bot))
