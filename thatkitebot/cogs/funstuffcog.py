#  Copyright (c) 2019-2022 ThatRedKite and contributors

import discord
import markovify
from discord.ext import commands
import typing
import glob
from random import choice, Random
from thatkitebot.backend import url, util, cache
from datetime import datetime
from uwuipy import uwuipy
import textwrap
from unidecode import unidecode


async def is_trainpost_channel(ctx):
    if ctx.guild.id == 424394851170385921:
        return ctx.channel.id in [864194488797102091, 424397590214344704]
    else:
        return True


def can_send_image(ctx):
    can_attach = ctx.channel.permissions_for(ctx.author).attach_files
    can_embed = ctx.channel.permissions_for(ctx.author).embed_links
    return can_attach and can_embed


class FunStuff(commands.Cog, name="fun commands"):
    """
    Miscellaneous 'fun' commands that don't fit anywhere else.
    """
    def __init__(self, bot):
        self.bot: discord.Client = bot
        self._last_member = None
        self.dirname = bot.dirname
        self.redis = bot.redis_cache

    @commands.command()
    @commands.check(can_send_image)
    async def inspirobot(self, ctx):
        """Sends a motivational quote from inspirobot.me."""
        await ctx.send(embed=await url.inspirourl(session=self.bot.aiohttp_session))

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(name="markov", aliases=["mark", "m"])
    async def _markov(self, ctx, user: typing.Optional[discord.User], channel: typing.Optional[discord.TextChannel]):
        """
        This command generates a bunch of nonsense text by feeding your messages to a markov chain.
        Optional Arguments: `user` and `channel` (they default to yourself and the current channel)
        """
        if self.bot.debugmode:
            try:
                print("Markov debug")
                print("user", user.name)
                print("channel", channel.name)
            except:
                pass
            
        if not user:
            user = ctx.message.author  # default to message author
        if not channel:
            channel = ctx.channel  # default to current channel
            
        guild = channel.guild
        
        if self.bot.debugmode:
            print("username 2:", user.name)
            print("user id 2:", user.id)
            print("channel name: 2", channel.name)
            print("channel id 2:", channel.id)
            print("guild:", guild.name)

        async with ctx.channel.typing():
            try:
                # try to get the messages from the cache
                messagelist = await cache.get_contents(self.redis, guild.id, channel.id, user.id)
                if not len(messagelist) > 300:
                    # populate the cache if there are less than 300 messages
                    async for message in channel.history(limit=2500).filter(lambda m: m.author is user):
                        await cache.add_message_to_cache(self.redis, message)  # add the message to the cache
                        messagelist.append(str(message.clean_content))  # add the message to the messagelist
            except discord.Forbidden:
                await util.errormsg(ctx, "I don't have access to that channel <:molvus:798286553553436702>")
                return
            try:
                gen1 = markovify.NewlineText("\n".join(messagelist))  # generate the model from the messages
            except KeyError:
                await util.errormsg(ctx, "You don't appear to have enough messages for me to generate sentences!")
                return

            genlist = set()  # create a set to avoid duplicate messages (only works sometimes)
            for i in range(10):
                a = gen1.make_sentence(tries=30)
                if a:
                    genlist.add(a)  # add the string a to the genlist
                else:
                    a = gen1.make_short_sentence(5)  # try to make a short sentence instead
                    genlist.add(a)  # add the string to the genlist

            if len(genlist) > 0:
                out = ". ".join([a for a in genlist if a])  # join the strings together with periods
                embed = discord.Embed(title=f"Markov chain output for {user.display_name}:", description=f"*{out}*")
                embed.set_footer(text=f"User: {str(user)}, channel: {str(channel)}")
                embed.color = 0x6E3513
                embed.set_thumbnail(url=user.avatar.url)
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
        if user == 454210418592841740 and args.lower() == "my ass":
            await ctx.send("🍑")
            return
        elif "ferracult" in args.lower():
            await ctx.send("cringe")
            return
        elif "geckult" in args.lower():
            await ctx.send("cringe")
            return
        elif "piss" in args.lower():
            await ctx.send("cringe")
            return
        elif "femboy" in args.lower():
            await ctx.send("femboy cult best cult")
            return
        elif "furri" in args.lower():
            await ctx.send("cringe")
            return
            
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
            "Yes definately.",
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
        await ctx.send(choice(resp_list)) # Not seeded random due to there being non-committal answers

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

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.check(can_send_image)
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
        '''UwUify your text (now even more cursed'''
        # fetch the message from the reference
        if ctx.message.reference:
            seed = ctx.message.reference.message_id
            message = await ctx.fetch_message(seed)
            msg = message.content
        # if not, grab the seed by using the original message id
        else:
            seed = ctx.message.id
        # if the message content is empty, return
        if not msg:
            return
        async with ctx.channel.typing():
            # declare a new uwu object using the message id as seed
            uwu = uwuipy(seed)
            # convert the input string to ascii
            msg = uwu.uwuify(unidecode(msg))
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

def setup(bot):
    bot.add_cog(FunStuff(bot))
