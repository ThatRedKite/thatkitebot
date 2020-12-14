#  MIT License
#
#  Copyright (c) 2020 ThatRedKite
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

#  MIT License
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#
#

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


async def mark(bot, ctx: commands.Context, user, old: int = 200, new: int = 200, leng: int = 5, leng2: int = 20,
               mode: str = "long"):
    # some general variables
    guild = ctx.guild
    author: discord.User = ctx.message.author
    message: discord.Message = ctx.message
    # change the bot's status to "do not disturb" and set its game
    await bot.change_presence(status=discord.Status.dnd, activity=discord.Game("fetching . . ."))
    chan, is_user, is_channel = backend.util.mentioner(bot, ctx, message, user, True)
    messages = []
    if is_user and not is_channel:
        for channel in guild.text_channels:
            # add :old: messages of the user :chan: to the list :messages: (from every channel of the guild)
            async for message in channel.history(limit=old, oldest_first=True).filter(lambda m: m.author == chan):
                messages.append(str(message.clean_content))

            # add :new: messages of the user :chan: to the list :messages:
            async for message in channel.history(limit=new).filter(lambda m: m.author == chan):
                messages.append(str(message.clean_content))

    else:
        # add :old: messages :chan: to the list :messages:           
        async for message in chan.history(limit=old, oldest_first=True):
            messages.append(str(message.clean_content))
        # add :new: messages :chan: to the list :messages: 
        async for message in chan.history(limit=new):
            messages.append(str(message.clean_content))
    await bot.change_presence(status=discord.Status.dnd, activity=discord.Game("fetching done, processing . . ."))
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
        if generated is not None: generated_list.append(generated)
    await bot.change_presence(status=discord.Status.online, activity=None)
    return generated_list, chan


class fun_stuff(commands.Cog):
    def __init__(self, bot, dirname):
        self.bot = bot
        self._last_member = None
        self.dirname = dirname
        # Variables for markov game
        self.mgame_id = None
        self.mgame_tries = None
        self.mgame_name = None

    @commands.command()
    async def inspirobot(self, ctx):
        payload = {"generate": "true"}
        r = get("http://inspirobot.me/api", params=payload)
        embed = discord.Embed(title="A motivating quote from InspiroBot")
        embed.color = 0x33cc33
        embed.set_image(url=r.text)
        await ctx.send(embed=embed)

    @commands.command(aliases=["mark", "m"])
    async def markov(self, ctx, user="keiner", *, args="-tts False"):
        parser = NoExitParser()
        try:
            parser.add_argument("-old", type=int, nargs="?", default=100)
            parser.add_argument("-new", type=int, nargs="?", default=100)
            parser.add_argument("-leng", type=int, nargs="?", default=5)
            parser.add_argument("-tts", type=str, nargs="?", default="False")
            parser.add_argument("-lang", type=str, nargs="?", default="en")
            parsed_args = parser.parse_args(args.split(" "))
            use_tts = backend.util.bool_parse(parsed_args.tts)
        except Exception as exc:
            print(exc)

        author: discord.User = ctx.message.author
        try:
            with ctx.channel.typing():
                generated_list, chan = await mark(self.bot, ctx,
                                                  user,
                                                  parsed_args.old,
                                                  parsed_args.new,
                                                  parsed_args.leng)
                if len(generated_list) > 0:
                    embed = discord.Embed(title="**Markov Chain Output: **",
                                          description=f"*{'. '.join(generated_list)}*")
                    embed.color = 0x6E3513
                    embed.set_footer(icon_url=author.avatar_url, text=f"generated by {author} the target was: {chan}")
                    if use_tts:
                        text = ". ".join(generated_list)
                        tts = gTTS(text=text, lang=parsed_args.lang)
                        tts.save(os.path.join(self.dirname, "data/tts.mp3"))
                        file_attachment = discord.File(os.path.join(self.dirname, "data/tts.mp3"), filename="tts.mp3")
                        await ctx.send(embed=embed)
                        await ctx.send(file=file_attachment)
                    else:
                        await ctx.send(embed=embed)
                else:
                    await ctx.send("an error has occured. I could not fetch enough messages!")
        except Exception as exc:
            await backend.util.errormsg(ctx, str(exc))
            raise exc
        finally:
            await self.bot.change_presence(status=discord.Status.online, activity=None)

    def markov_clear(self):
        self.mgame_id = None
        self.mgame_tries = None
        self.mgame_name = None

    @commands.group()
    async def mgame(self, ctx):
        pass

    @mgame.command()
    async def start(self, ctx, tries: int):
        guild: discord.Guild = ctx.guild
        memberlist = []
        async for member in guild.fetch_members():
            memberlist.append(member)
        the_chosen_one = choice(memberlist)
        print(the_chosen_one.id)
        self.mgame_id = the_chosen_one.id
        self.mgame_tries = tries
        self.mgame_name = the_chosen_one.name
        messages = []
        try:
            generated_list, chan = await mark(self.bot, ctx, str(the_chosen_one.id), 1000, 1000)
            if len(generated_list) > 0:
                embed = discord.Embed(title="**Who could have said this?**",
                                      description=f"*{'. '.join(generated_list)}*")
                await ctx.send(embed=embed)

        except Exception as exc:
            print(exc)
            await backend.util.errormsg(ctx,
                                        "Could not fetch enough messages! Please change the parameters and try again!")
            self.markov_clear()

        finally:
            await self.bot.change_presence(status=discord.Status.online, activity=None)

    @mgame.command()
    async def guess(self, ctx, user):
        rest = re.findall("(\d+)", user)
        guild: discord.Guild = ctx.guild
        if len(rest) > 0:
            chan = int(rest[0])
        else:
            chan = 0
        chun = re.findall(f"{user.lower()}", self.mgame_name.lower())
        if self.mgame_id is not None and self.mgame_tries is not None:
            if chan == self.mgame_id or len(chun) != 0 and self.mgame_tries != 0:
                await ctx.send("YOU ARE RIGHT! Here's a cookie for you: 🍪")
                self.markov_clear()
            else:
                self.mgame_tries -= 1
                if self.mgame_tries == 0 or self.mgame_tries < 0:
                    await backend.util.errormsg(ctx,
                                                f"Sorry but that was the wrong answer. You have lost. The right answer would have been: {self.mgame_name}")
                    self.markov_clear()
                else:
                    await ctx.send(f"Sorry, that was wrong, you now have only {self.mgame_tries} tries left ")
        else:
            await backend.util.errormsg(ctx, "You cannot guess, if you havn't started a game")

    @mgame.command()
    async def stop(self, ctx):
        self.markov_clear()

    @commands.command()
    async def fakeword(self, ctx):
        with ctx.channel.typing():
            embed = await backend.url.word(self.bot.aiohttp_session, embedmode=True)
            await ctx.send(embed=embed)

    @commands.command()
    async def vision(self, ctx):
        await ctx.send("https://media.discordapp.net/attachments/401372087349936139/566665541465669642/vision.gif")
