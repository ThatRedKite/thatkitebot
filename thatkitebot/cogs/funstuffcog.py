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
import os
import discord
import markovify
from discord.ext import commands
import typing
import glob
from random import choice
from thatkitebot.backend import url, util


async def is_trainpost_channel(ctx):
    if ctx.guild.id == 424394851170385921:
        return ctx.channel.id == 909159696798220400
    else:
        return True


def can_send_image(ctx):
    can_attach = ctx.channel.permissions_for(ctx.author).attach_files
    can_embed = ctx.channel.permissions_for(ctx.author).embed_links
    return can_attach and can_embed


class FunStuff(commands.Cog, name="fun commands"):
    def __init__(self, bot):
        self.bot: discord.Client = bot
        self._last_member = None
        self.dirname = bot.dirname
        # Variables for markov game

    @commands.command()
    @commands.check(can_send_image)
    async def inspirobot(self, ctx):
        """Sends a motivational quote from inspirobot.me."""
        await ctx.send(embed=await url.inspirourl(session=self.bot.aiohttp_session))

    @commands.cooldown(1, 90, commands.BucketType.user)
    @commands.command(name="markov", aliases=["mark", "m"])
    async def _markov(self, ctx, user: typing.Optional[discord.Member],  channel: typing.Optional[discord.TextChannel]):
        """
        This command generates a bunch of nonsense text by feeding your messages to a markov chain.
        Optional Arguments: `user` and `channel` (they default to yourself and the current channel)
        """
        if not user:
            user = ctx.message.author
        if not channel:
            channel = ctx.channel
        async with ctx.channel.typing():
            try:
                messagelist = [message.clean_content for message in self.bot.cached_messages if message.author is user and message.guild is ctx.guild and ctx.channel is channel]
                if not len(messagelist) > 150:
                    async for message in channel.history(limit=2500).filter(lambda m: m.author is user):
                        messagelist.append(str(message.clean_content))
            except discord.Forbidden:
                await util.errormsg(ctx, "It seems like I don't have access to that channel <:molvus:798286553553436702>")
                return
            try:
                 gen1 = markovify.NewlineText("\n".join(messagelist))
            except KeyError:
                await util.errormsg(ctx, "You don't appear to have enough messages for me to generate sentences!")
                return
            genlist = set()
            for i in range(30):
                    a = gen1.make_sentence(tries=30)
                    if a:
                        genlist.add(a)
                    else:
                        a = gen1.make_short_sentence(5)
                        genlist.add(a)

            try:
                 gen2 = markovify.NewlineText('\n'.join([a for a in genlist if a]))
            except KeyError:
                await util.errormsg(ctx, "You don't appear to have enough messages for me to generate sentences!")
                return

            genlist2 = set()
            for i in range(3):
                    b = gen2.make_sentence(tries=20)
                    if b:
                        genlist2.add(b)
                    else:
                        b = gen2.make_short_sentence(10)
                        genlist2.add(b)

            if len(genlist) > 0:
                out = ". ".join([a for a in genlist2 if a])
                embed = discord.Embed(title=f"Markov chain output for {user.display_name}:", description=f"*{out}*")
                embed.set_footer(text=f"User: {str(user)}, channel: {str(channel)}")
                embed.color = 0x6E3513
                embed.set_thumbnail(url=user.avatar_url)
                await ctx.send(embed=embed)
            else:
                await util.errormsg(ctx, "You don't appear to have enough messages for me to generate sentences!")

    @commands.command()
    async def fakeword(self, ctx):
        """Sends a fake word from thisworddoesnotexist.com."""
        async with ctx.channel.typing():
            embed = await url.word(self.bot.aiohttp_session, embedmode=True)
            await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.check(can_send_image)
    async def vision(self, ctx):
        """Ignore this."""
        await ctx.send("https://media.discordapp.net/attachments/401372087349936139/566665541465669642/vision.gif")

    @commands.cooldown(1, 1, commands.BucketType.user)
    @commands.command(name="train", aliases=["zug"])
    @commands.check(is_trainpost_channel)
    @commands.check(can_send_image)
    async def _train(self, ctx):
        """Sends a random image of a train."""
        images = [image for image in glob.glob("/app/data/trains/*.jpg")]
        train = discord.File(choice(images), "train.jpg")
        async with ctx.typing():
            await ctx.send(file=train)

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.check(can_send_image)
    @commands.command(name="1984")
    async def _1984(self, ctx):
        """
        Literally 1984
        """
        await ctx.send("https://cdn.discordapp.com/attachments/759419756620546080/911279036146258000/unknown.png")

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(name="eval", hidden=True)
    async def _eval(self, ctx):
        await ctx.send("Get real. <:troll:910540961958989934>")

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.check(can_send_image)
    @commands.command(name="fakeperson")
    async def _tpdne(self, ctx):
        """Send an image from thispersondoesnotexist.com"""
        file, embed = await url.tpdne(self.bot.aiohttp_session)
        async with ctx.typing():
            await ctx.send(file=file, embed=embed)

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.check(can_send_image)
    @commands.command(name="fakecat")
    async def _tcdne(self, ctx):
        """Send an image from thiscatdoesnotexist.com"""
        file, embed = await url.tcdne(self.bot.aiohttp_session)
        async with ctx.typing():
            await ctx.send(file=file, embed=embed)

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.check(can_send_image)
    @commands.command(name="fakeart")
    async def _tadne(self, ctx):
        """Send an image from thisartworkdoesnotexist.com"""
        file, embed = await url.tadne(self.bot.aiohttp_session)
        async with ctx.typing():
            await ctx.send(file=file, embed=embed)

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.check(can_send_image)
    @commands.command(name="fakewaifu")
    async def _twdne(self, ctx):
        """Send an image from thiswaifudoesnotexist.net"""
        file, embed = await url.twdne(self.bot.aiohttp_session)
        async with ctx.typing():
            await ctx.send(file=file, embed=embed)

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.check(can_send_image)
    @commands.command(name="fakefur", hidden=True)
    async def _tfdne(self, ctx):
        """Send an image from thisfursonadoesnotexist.com <:amsmiles:910537357613228072>"""
        file, embed = await url.tfdne(self.bot.aiohttp_session)
        async with ctx.typing():
            await ctx.send(file=file, embed=embed)


    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.check(can_send_image)
    @commands.command(name="fakevessel", aliases=["fakeceramic", "tvdne", "fakevase"])
    async def _tvdne(self, ctx):
        """Send an image from thisvesseldoesnotexist.com"""
        file, embed = await url.tvdne(self.bot.aiohttp_session)
        async with ctx.typing():
            await ctx.send(file=file, embed=embed)


def setup(bot):
    bot.add_cog(FunStuff(bot))
    