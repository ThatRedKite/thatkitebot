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
import backend
import typing
from discord_slash import cog_ext, SlashContext
import glob
from random import choice


class NoExitParser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


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


class FunStuff(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
        self.dirname = bot.dirname
        # Variables for markov game

    @commands.command()
    async def inspirobot(self, ctx):
        await ctx.send(embed=await backend.url.inspirourl(session=self.bot.aiohttp_session))

    @commands.command(name="markov", aliases=["mark", "m"])
    async def _markov(self, ctx, user: typing.Optional[discord.Member], tts: bool = False):
        if not user:
            user = ctx.message.author
        async with ctx.channel.typing():
            generated_list = await markov(ctx.guild, user)
            embed = discord.Embed(title="**Markov Chain Output: **", description=f"*{'. '.join(generated_list)}*")
            embed.color = 0x6E3513
            embed.set_thumbnail(url=user.avatar_url)

            if tts:
                text = ". ".join(generated_list)
                tts = gTTS(text=text, lang="en_US")
                tts.save(os.path.join(self.dirname, "data/tts.mp3"))
                file_attachment = discord.File(os.path.join(self.dirname, "data/tts.mp3"), filename="tts.mp3")
                await ctx.send(embed=embed, file=file_attachment)

            else:
                await ctx.send(embed=embed)

    @commands.command()
    async def fakeword(self, ctx):
        async with ctx.channel.typing():
            embed = await backend.url.word(self.bot.aiohttp_session, embedmode=True)
            await ctx.send(embed=embed)

    @commands.command()
    async def vision(self, ctx):
        await ctx.send("https://media.discordapp.net/attachments/401372087349936139/566665541465669642/vision.gif")

    @cog_ext.cog_slash(name="train", description="Sends a random image of a train", guild_ids=[685989658555056212])
    async def train(self, ctx: SlashContext):
        images = [image for image in glob.glob(os.path.join(self.dirname, "data", "static", "*.jpg"))]
        train = discord.File(choice(images))
        await ctx.defer()
        await ctx.send(file=train)


def setup(bot):
    bot.add_cog(FunStuff(bot))
    

