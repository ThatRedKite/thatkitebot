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
import re
from random import choice
import discord
import markovify
from discord.ext import commands
from gtts import gTTS
import backend


class NoExitParser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


async def mark(
    bot,
    ctx: commands.Context,
    user,
    old: int = 200,
    new: int = 200,
    leng: int = 5,
    leng2: int = 20,
    mode: str = "long",
):
    # some general variables
    guild = ctx.guild
    author: discord.User = ctx.message.author
    message: discord.Message = ctx.message
    # change the bot's status to "do not disturb" and set its game
    await bot.change_presence(
        status=discord.Status.dnd, activity=discord.Game("fetching . . .")
    )
    chan, is_user, is_channel = backend.util.mentioner(bot, ctx, message, user, True)
    messages = []
    if is_user and not is_channel:
        for channel in guild.text_channels:
            # add :old: messages of the user :chan: to the list :messages: (from every channel of the guild)
            async for message in channel.history(limit=old, oldest_first=True).filter(
                lambda m: m.author == chan
            ):
                messages.append(str(message.clean_content))

            # add :new: messages of the user :chan: to the list :messages:
            async for message in channel.history(limit=new).filter(
                lambda m: m.author == chan
            ):
                messages.append(str(message.clean_content))

    else:
        # add :old: messages :chan: to the list :messages:
        async for message in chan.history(limit=old, oldest_first=True):
            messages.append(str(message.clean_content))
        # add :new: messages :chan: to the list :messages:
        async for message in chan.history(limit=new):
            messages.append(str(message.clean_content))
    await bot.change_presence(
        status=discord.Status.dnd,
        activity=discord.Game("fetching done, processing . . ."),
    )
    # generate a model based on the messages in :messages:
    model = markovify.NewlineText("\n".join(messages))
    generated_list = []
    # generate :leng: sentences
    for i in range(leng):
        if mode == "long":
            generated = model.make_sentence()
        else:
            generated = model.make_short_sentence(leng2)
        # only add sentences that are not None to :generated_list:
        if generated is not None:
            generated_list.append(generated)
    await bot.change_presence(status=discord.Status.online, activity=None)
    return generated_list, chan


class fun_stuff(commands.Cog):
    def __init__(self, bot, dirname):
        self.bot = bot
        self._last_member = None
        self.dirname = dirname
        # Variables for markov game

    @commands.command()
    async def inspirobot(self, ctx):
        await ctx.send(
            embed=await backend.url.inspirourl(session=self.bot.aiohttp_session)
        )

    @commands.command(aliases=["mark", "m"])
    async def markov(self, ctx, user="", *, args="-tts False"):
        parser = NoExitParser()
        try:
            parser.add_argument("-old", type=int, nargs="?", default=100)
            parser.add_argument("-new", type=int, nargs="?", default=100)
            parser.add_argument("-leng", type=int, nargs="?", default=5)
            parser.add_argument("-tts", type=str, nargs="?", default="en")
            parser.add_argument("-lang", type=str, nargs="?", default="en")
            parsed_args = parser.parse_args(args.split(" "))
            use_tts = backend.util.bool_parse(parsed_args.tts)
        except Exception as exc:
            print(exc)

        author: discord.User = ctx.message.author
        try:
            with ctx.channel.typing():
                generated_list, chan = await mark(
                    self.bot,
                    ctx,
                    user,
                    parsed_args.old,
                    parsed_args.new,
                    parsed_args.leng,
                )

                embed = discord.Embed(
                    title="**Markov Chain Output: **",
                    description=f"*{'. '.join(generated_list)}*",
                )
                embed.color = 0x6E3513
                embed.set_footer(
                    icon_url=author.avatar_url,
                    text=f"generated by {author} the target was: {chan}",
                )
                if use_tts:
                    text = ". ".join(generated_list)
                    tts = gTTS(text=text, lang=parsed_args.lang)
                    tts.save(os.path.join(self.dirname, "data/tts.mp3"))
                    file_attachment = discord.File(
                        os.path.join(self.dirname, "data/tts.mp3"),
                        filename="tts.mp3",
                    )
                    await ctx.send(embed=embed)
                    await ctx.send(file=file_attachment)
                else:
                    await ctx.send(embed=embed)
        except Exception as exc:
            await backend.util.errormsg(ctx, str(exc))
            raise exc
        finally:
            await self.bot.change_presence(status=discord.Status.online, activity=None)

    @commands.command()
    async def fakeword(self, ctx):
        with ctx.channel.typing():
            embed = await backend.url.word(self.bot.aiohttp_session, embedmode=True)
            await ctx.send(embed=embed)

    @commands.command()
    async def vision(self, ctx):
        await ctx.send("https://media.discordapp.net/attachments/401372087349936139/566665541465669642/vision.gif")
