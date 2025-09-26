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
import textwrap
import re
from unidecode import unidecode
from random import choice, Random
from datetime import datetime

import discord
import markovify
from discord.ext import commands
from discord import ChannelType
from uwuipy import uwuipy

from thatkitebot.base import url, util
from thatkitebot.base.util import PermissonChecks as pc
from thatkitebot.base.util import ChannelTypeLists as CTL
from thatkitebot.base.exceptions import NotEnoughMessagesException
from thatkitebot.tkb_redis.cache import RedisCacheAsync
from thatkitebot.types.message import Message
#endregion



#region Cog
class FunStuff(commands.Cog, name="fun commands"):
    """
    Miscellaneous 'fun' commands that don't fit anywhere else.
    """
    def __init__(self, bot):
        self.bot: discord.Bot = bot
        self.dirname = bot.dir_name
        self.cache: RedisCacheAsync = bot.r_cache

    @staticmethod
    def _last_time(messages: list[Message]) -> datetime | None:
        if (l := len(messages)) == 0:
            return None
        elif l == 1:
            return messages[0].created_at
        elif l > 1:
            # sort messages by time
            a: list[Message] = sorted(messages, key=lambda m: m.created_at.timestamp(), reverse=True)
            return a[0].created_at
        
    async def _generate_markov(self, member: discord.Member = None, channel: discord.TextChannel = None, include_threads: bool = False, length: int = 4) -> discord.Embed:
        messages = []
        api_counter = 0
        cache_counter = 0

        if channel and member:
            async for message in self.cache.channel_history_iter(channel, member.id, limit=None):
                messages.append(message)
                cache_counter += 1
        
            if len(messages) < 200:
                async for message in channel.history(limit=1000, before=self._last_time(messages)).filter(lambda m: m not in messages and m.author.id == member.id):
                    messages.append(message)
                    await self.cache.add_message_object(message)
                    api_counter += 1

        elif channel and not member:
            async for message in self.cache.channel_history_iter(channel, limit=None):
                messages.append(message)
                cache_counter += 1

            if len(messages) < 200:
                async for message in channel.history(limit=1000, before=self._last_time(messages)).filter(lambda m: m not in messages):
                    messages.append(message)
                    await self.cache.add_message_object(message)
                    api_counter += 1


        output = set()
        model = markovify.NewlineText("\n".join([m.clean_content for m in messages]))

        for _ in range(length):
            if sentence := model.make_sentence(tries=100):
                output.add(sentence)
        
        embed = discord.Embed(description=". ".join(output))

        if len(output) < 1:
            embed.description = "Failed to generate output. Probably not enough messages from this user / channel"

        if member and channel:
            embed.title = f"Output for {member.nick if member.nick else member.name} in {channel.mention}"
            embed.color = member.color or member.accent_color
            embed.set_thumbnail(url=url.get_avatar_url(member))
        elif channel and not member:
            embed.title = f"Output for {channel.mention}"
        else:
            embed.title = f"Output ..."            
        embed.set_footer(text=f"Channel: #{message.channel.name} | Messages: {cache_counter + api_counter} (Cache: {cache_counter}, API: {api_counter})")

        return embed

    @discord.command(name="markov", description="Get markov chain output for a specified channel (all users)", guild_ids=[759419755253465188])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _markov_slash(
        self,
        ctx: discord.ApplicationContext,
        channel: discord.Option(discord.TextChannel, required=True, channel_types=CTL.DEFAULT_CHANNEL_TYPES), # type: ignore
        user: discord.Option(discord.Member,"When set, only messages from this user will be used", required=False), # type: ignore
        length: discord.Option(int, "Number of sentences to generate", min_value=1, max_value=10, default=4, required=False), # type: ignore
    ):
        await ctx.defer()
        await ctx.respond(embed=await self._generate_markov(member=user, channel=channel, length=length))

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        # only listen for commands associated with this cog
        if ctx.cog is not self:
            return

        if isinstance(error, NotEnoughMessagesException):
            await util.errormsg(ctx, "You don't appear to have enough messages for me to generate sentences!")

    @commands.command()
    @commands.check(pc.can_send_image)
    async def inspirobot(self, ctx) -> None:
        """Sends a motivational quote from inspirobot.me."""
        await ctx.send(embed=await url.get_inspirobot_url(session=self.bot.aiohttp_session))
    
    @commands.command(name="markov")
    async def _markov(self, ctx) -> None:
       await ctx.reply(f"This command has been replaced by {self._markov_slash.mention}.")

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.check(pc.can_send_image)
    @commands.command(name="1984")
    async def _1984(self, ctx) -> None:
        """
        Literally 1984
        """
        await ctx.send("https://cdn.discordapp.com/attachments/759419756620546080/911279036146258000/unknown.png")

    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command(name="eval", aliases=["evaluate", "opinion"])
    async def _eval(self, ctx, *, args=None) -> None:
        resp_list = [
            "Get real. <:troll:910540961958989934>", "Nice", "Based", "Cringe",
            "<:schmuck:900445607888551947>", "Ok, and?", "yeah...", "perhaps",
            "cry about it", "unfunny", "funny", ":eggplant:", "NO!", "flawless",
            "amazing", "splendid", "don't...", "gecko is fuming", "ok", "lol",
            ":star:", "sucks", "stop", "whatever", "I am a bot I don't have opinions, all of this is just RNG...",
            "was it worth it?", "Thanks I hate it.", "actually stop", "not funny",
            "furry <:troll:910540961958989934>", "you wish", "pff", "DO\nNOT\nDISTURB",
            "busy", "sucks so bad", "soon", "no?", "👀", "in your dreams", "smh",
            "well DO IT", "oh?", "of course not 😎", "🙄", "🥺", "never\nunless...? 😳"
            "mm", "ehhh", "uhh", "<:zycosmoke:821821351576338534>", "🥵",
            "hot", "Kite sounds", "uh huh", "no idea",
            "almost nice", "scary", "negative", "mm?", "has a good ring", "why?", "iconic",
            "epic", "rad", "neat", "acceptable", "superb", "awful", "not good", "sad", "beastly",
            "wild", "meh...", "I am fuming", "What is that supposed to mean?", "are you trying to cancel me?",
            "cool", "not cool", "try harder", "idk", "exceptional", "big", "massive", "I am not sure",
            "why not?", "my ass", "worthy", "hahaha", "good one", "not great not, terrible", "is it legal?",
            "can't", "top notch", "eval that yourself", "sounds interesting",
            "baller", "chad", "I don't think so"
        ]
        user = ctx.message.author.id
        if ctx.message.reference is not None:
            str_seed = ctx.message.reference.message_id
        else:
            str_seed = abs(hash(str(user) + str(args) + str(datetime.today().strftime('%Y-%m-%d')))) % (10 ** 8)
        eval_random = Random()
        eval_random.seed(str_seed)
        result = resp_list[eval_random.randint(0, len(resp_list) - 1 )]
        await ctx.send(result)

    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command(name="8ball")
    async def _8ball(self, ctx, *, args=None) -> None:
        resp_list = [
            "It is certain.",
            "It is decidedly so.",
            "Without a doubt.",
            "Yes definitely.",
            "You may rely on it.",
            "As I see it, yes.",
            "Most likely.",
            "Outlook good.",
            "Yes.",
            "Signs point to yes.",
            "Reply hazy, try again.",
            "Ask again later.",
            "Better not tell you now.",
            "Cannot predict now.",
            "Concentrate and ask again.",
            "Don't count on it.",
            "My reply is no.",
            "My sources say no.",
            "Outlook not so good.",
            "Very doubtful."
        ]
        await ctx.send(choice(resp_list))  # Not seeded random due to there being non-committal answers

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.check(pc.can_send_image)
    @commands.command(name="xkcd", aliases=["comic", "xkcdcomic"])
    async def _xkcd(self, ctx, *, args=None) -> None:
        """Send a random or specific xkcd comic"""
        embed = await url.get_xkcd(args)
        if embed is None:
            await util.errormsg(ctx, "Invalid arguments")
            return
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, exception) -> None:
        if ctx.cog is not self:
            return
        
#endregion

def setup(bot) -> None:
    bot.add_cog(FunStuff(bot))
