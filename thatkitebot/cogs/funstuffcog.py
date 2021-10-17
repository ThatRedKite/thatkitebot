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
from thatkitebot.backend import url


async def markov(guild, chan, old=50, new=10, leng=5):
    messages = []
    for channel in guild.text_channels:
        # add :old: messages of the user :chan: to the list :messages: (from every channel of the guild)
        try:
            async for message in channel.history(limit=new).filter(lambda m: m.author == chan):
                messages.append(str(message.clean_content))
        except discord.Forbidden:
            continue
    # generate a model based on the messages in :messages:
    print(messages)
    model = markovify.NewlineText("\n".join(messages))

    generated_list = list()

    for i in range(leng):
        a = model.make_sentence()
        print(a)
        if a:
            generated_list.append(a)

    return generated_list


class FunStuff(commands.Cog, name="fun commands"):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
        self.dirname = bot.dirname
        # Variables for markov game

    @commands.command()
    async def inspirobot(self, ctx):
        """Sends a motivational quote from inspirobot.me."""
        await ctx.send(embed=await url.inspirourl(session=self.bot.aiohttp_session))

    @commands.command(name="markov", aliases=["mark", "m"])
    async def _markov(self, ctx, user: typing.Optional[discord.Member]):
        if not user:
            user = ctx.message.author
        async with ctx.channel.typing():
            generated_list = await markov(ctx.guild, user)
            embed = discord.Embed(title="**Markov Chain Output: **", description=f"*{'. '.join(generated_list)}*")
            embed.color = 0x6E3513
            embed.set_thumbnail(url=user.avatar_url)
            await ctx.send(embed=embed)

    @commands.command()
    async def fakeword(self, ctx):
        """Sends a fake word from thisworddoesnotexist.com."""
        async with ctx.channel.typing():
            embed = await url.word(self.bot.aiohttp_session, embedmode=True)
            await ctx.send(embed=embed)

    @commands.command(hidden=True)
    async def vision(self, ctx):
        """Ignore this."""
        await ctx.send("https://media.discordapp.net/attachments/401372087349936139/566665541465669642/vision.gif")

    @commands.cooldown(1, 1, commands.BucketType.user)
    @commands.command(name="train", aliases=["zug"])
    async def _train(self, ctx):
        """Sends a random image of a train."""
        images = [image for image in glob.glob("/app/data/trains/*.jpg")]
        train = discord.File(choice(images), "train.jpg")
        async with ctx.typing():
            await ctx.send(file=train)


def setup(bot):
    bot.add_cog(FunStuff(bot))
    

