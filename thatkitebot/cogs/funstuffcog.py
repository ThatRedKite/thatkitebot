#  Copyright (c) 2019-2023 ThatRedKite and contributors

import textwrap
import re
import typing
import asyncio
from unidecode import unidecode
from random import choice, Random
from datetime import datetime

import discord
import markovify
from discord.ext import commands
from uwuipy import uwuipy

from thatkitebot.base import url, util
from thatkitebot.base.util import PermissonChecks as pc
from thatkitebot.base.exceptions import NotEnoughMessagesException
from thatkitebot.tkb_redis.cache import RedisCache, CacheInvalidMessageException


class FunStuff(commands.Cog, name="fun commands"):
    """
    Miscellaneous 'fun' commands that don't fit anywhere else.
    """
    def __init__(self, bot):
        self.bot: discord.Client = bot
        self._last_member = None
        self.dirname = bot.dir_name
        self.redis = bot.redis_cache
        self.cache: RedisCache = bot.r_cache

        self.history_semaphore = asyncio.Semaphore(2)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        # only listen for commands associated with this cog
        if ctx.cog is not self:
            return

        if isinstance(error, NotEnoughMessagesException):
            await util.errormsg(ctx, "You don't appear to have enough messages for me to generate sentences!")

    @commands.command()
    @commands.check(pc.can_send_image)
    async def inspirobot(self, ctx):
        """Sends a motivational quote from inspirobot.me."""
        await ctx.send(embed=await url.inspirourl(session=self.bot.aiohttp_session))

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(name="markov", aliases=["mark", "m"])
    async def _markov(self, ctx: commands.Context, user: typing.Optional[discord.User], channel: typing.Optional[discord.TextChannel]):
        """
        This command generates a bunch of nonsense text by feeding your messages to a markov chain.
        Optional Arguments: `user` and `channel` (they default to yourself and if no channel is provided,
        it will use messages from every channel instead)
        """
        if not user:
            user = ctx.message.author  # default to message author

        if not channel:
            channel = ctx.channel # default to current channel

        async with ctx.channel.typing(), self.history_semaphore:
            try:
                # try to get the messages from the cache
                message_list = await self.cache.get_messages(ctx.guild.id, channel.id, user.id)
                # populate the cache if there are less than 300 messages
                if not len(message_list) > 300:
                    # we have a channel but not enough messages, so we iterate over the user history in this channel
                    async for message in channel.history(limit=5000).filter(lambda m: m.author is user):
                        try:
                            await self.cache.add_message(message)  # add the message to the cache
                        except CacheInvalidMessageException:
                            pass
                        message_list.append(str(message.clean_content))  # add the message to the message_list
            except discord.Forbidden:
                await util.errormsg(ctx, "I don't have access to that channel <:molvus:798286553553436702>")
                return

            try:
                # since people often don't use punctuation, we just use newline-separated text.
                model = markovify.NewlineText("\n".join(message_list))  # generate the model from the messages
            except KeyError:
                raise NotEnoughMessagesException

            sentences = set()  # create a set to avoid duplicate messages (only works sometimes)
            for _ in range(10):
                if sentence := model.make_sentence(tries=30):
                    sentences.add(sentence)  # add the sentence to the set
                else:
                    sentence = model.make_short_sentence(5)  # try to make a short sentence instead
                    if sentence:
                        sentences.add(sentence)  # and add it to the set

            if sentences:
                out = ". ".join(sentences)  # join the strings together with periods
                embed = discord.Embed(title=f"Markov chain output for {user.display_name}:", description=f"*{out}*")
                embed.set_footer(text=f"User: {str(user)}, channel: {str(channel)}")
                embed.color = 0x6E3513
                embed.set_thumbnail(url=user.avatar.url)
                await ctx.send(embed=embed)

            else:
                raise NotEnoughMessagesException

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.check(pc.can_send_image)
    @commands.command(name="1984")
    async def _1984(self, ctx):
        """
        Literally 1984
        """
        await ctx.send("https://cdn.discordapp.com/attachments/759419756620546080/911279036146258000/unknown.png")

    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command(name="eval", aliases=["evaluate", "opinion"])
    async def _eval(self, ctx, *, args=None):
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
    async def _8ball(self, ctx, *, args=None):
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

    # RIP thispersondoesnotexist.com

    # @commands.cooldown(1, 10, commands.BucketType.user)
    # @commands.check(pc.can_send_image)
    # @commands.command(name="fakecat")
    # async def _tcdne(self, ctx):
    #     """Send an image from thiscatdoesnotexist.com"""
    #     file, embed = await url.tcdne(self.bot.aiohttp_session)
    #     async with ctx.typing():
    #         await ctx.send(file=file, embed=embed)

    # @commands.cooldown(1, 10, commands.BucketType.user)
    # @commands.check(pc.can_send_image)
    # @commands.command(name="fakeart")
    # async def _tadne(self, ctx):
    #     """Send an image from thisartworkdoesnotexist.com"""
    #     file, embed = await url.tadne(self.bot.aiohttp_session)
    #     async with ctx.typing():
    #         await ctx.send(file=file, embed=embed)

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.check(pc.can_send_image)
    @commands.command(name="fakewaifu")
    async def _twdne(self, ctx):
        """Send an image from thiswaifudoesnotexist.net"""
        file, embed = await url.twdne(self.bot.aiohttp_session)
        async with ctx.typing():
            await ctx.send(file=file, embed=embed)

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.check(pc.can_send_image)
    @commands.command(name="fakefur", hidden=True)
    async def _tfdne(self, ctx):
        """Send an image from thisfursonadoesnotexist.com <:amsmiles:910537357613228072>"""
        file, embed = await url.tfdne(self.bot.aiohttp_session)
        async with ctx.typing():
            await ctx.send(file=file, embed=embed)

    # rest in peace,
    # thisvesseldoesnotexist.com,
    # thispersondoesnotexist.com,
    # thiscatdoesnotexist.com
    # and thisartworkdoesnotexist.com

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.check(pc.can_send_image)
    @commands.command(name="xkcd", aliases=["comic", "xkcdcomic"])
    async def _xkcd(self, ctx, *, args=None):
        """Send a random or specific xkcd comic"""
        embed = await url._xkcd(args)
        if embed is None:
            await util.errormsg(ctx, "Invalid arguments")
            return
        await ctx.send(embed=embed)

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(name="uwuify", aliases=["uwu"])
    async def _uwuify(self, ctx: commands.Context, *, msg: str = None):
        """
        UwUify your text (now even more cursed)
        """
        # if not, grab the seed by using the original message id
        if not ctx.message.reference:
            seed = ctx.message.id

        # fetch the message from the reference
        else:
            seed = ctx.message.reference.message_id
            message = await ctx.fetch_message(seed)
            msg = message.content

        # if the message content is empty, return
        if not msg:
            return

        async with ctx.channel.typing():
            # declare a new uwu object using the message id as seed
            uwu = uwuipy(seed)
            # convert the input string to ascii
            msg = unidecode(msg)

            # if the user cant send images, make links not embed by surrounding them with <>
            if not pc.can_send_image(ctx):
                links = r"(https?:\/\/[A-Za-z0-9\-._~!$&'()*+,;=:@\/?]+)"
                msg = re.sub(links, r"<\1>" , msg)

            # do the deed
            msg = uwu.uwuify(msg)

            # if the message is longer than 2 000 characters
            if len(msg) > 2000:
                # split it up while maintaining whole words
                output = textwrap.wrap(msg, 2000)
                # for each new "message" send it in the channel
                for _msg in output:
                    await ctx.send(_msg)
            # if the message is under the limit, just send it as usual
            else:
                await ctx.send(msg)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, exception):
        if isinstance(exception.original, NotEnoughMessagesException):
            await ctx.send("Failed to generate a markov output. Please try another user or channel.")

def setup(bot):
    bot.add_cog(FunStuff(bot))
