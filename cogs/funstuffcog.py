import discord, asyncio
import  random
import os, re
import requests
import markovify
from bf.util import errormsg
from bf.yamler import Yamler
from bf import url
from discord.ext import commands

class FunStuff(commands.Cog):
    def __init__(self, bot, dirname, settings):
        self.bot = bot
        self._last_member = None
        self.settings = settings
        # Variables for markov game
        self.mgame_id = None
        self.mgame_tries = None
        self.mgame_name = None

    @commands.command()
    async def inspirobot(self, ctx):
        payload = {"generate": "true"}
        r = requests.get("http://inspirobot.me/api", params=payload)
        embed = discord.Embed(title="A motivating quote from InspiroBot")
        embed.color = 0x33cc33
        embed.set_image(url=r.text)
        await ctx.send(embed=embed)

    @commands.is_nsfw() #only proceed when in an nsfw channel
    @commands.command()
    async def r34(self, ctx,*, tags):
        def is_author(m):
            return not m.content.startswith("[KEEP]")
        await ctx.channel.purge(limit=1, check=is_author, bulk=False)  
        self.yam = Yamler(f"{self.dirname}/data/settings.yml")
        self.settings = self.yam.load()# load the bot's settings
        if self.settings["nsfw"]:
            # only proceed if nsfw is enabled in the bot's settings
            payload = { 
            "page": "dapi",
            "tags": tags,
            "s": "post",
            "q": "index"
            }
            await ctx.trigger_typing()
            myurl = await url.xml_sequence_parse(payload,"https://rule34.xxx/index.php","sample_url","pid") # get a sample_url
            embed = discord.Embed(title="Link To picture", url=myurl)
            embed.color = 0xff00cc # change color to magenta
            embed.set_image(url=myurl) 
            await ctx.send(embed=embed) 
        else:
            embed = discord.Embed(title="ERROR!", description="nsfw content is disabled")
            # send error message when nsfw is not enabled in the bot's settings
            embed.color = 0xC1121C # change color to red
            await ctx.send(embed=embed)

    @commands.is_nsfw() #only proceed when in an nsfw channel
    @commands.command()
    async def yan(self, ctx,*, tags):
        def is_author(m):
            return not m.content.startswith("[KEEP]")
        await ctx.channel.purge(limit=1, check=is_author, bulk=False)  
        self.yam = Yamler(f"{self.dirname}/data/settings.yml")
        self.settings = self.yam.load()
        # load the bot's settings
        if self.settings["nsfw"]:
            # only proceed if nsfw is enabled in the bot's settings
            payload = {
            "limit": 100,
            "tags": tags
            }
            await ctx.trigger_typing()
            myurl = await url.xml_sequence_parse(payload,"https://yande.re/post.xml","sample_url", "page",False) # get a sample_url
            embed = discord.Embed(title="Link To picture", url=myurl)
            embed.color = 0xff00cc
            # change color to magenta
            embed.set_image(url=myurl) 
            await ctx.send(embed=embed) 
        else:
            embed = discord.Embed(title="ERROR!", description="nsfw content is disabled")
            # send error message when nsfw is not enabled in the bot's settings
            embed.color = 0xC1121C # change color to red
            await ctx.send(embed=embed)

    @commands.is_owner()
    @commands.is_nsfw() #only proceed when in an nsfw channel
    @commands.command()
    async def testcommand(self, ctx,*, tags):
        def is_author(m):
            return not m.content.startswith("[KEEP]")
        await ctx.channel.purge(limit=1, check=is_author, bulk=False)  
        self.yam = Yamler(f"{self.dirname}/data/settings.yml")
        self.settings = self.yam.load()
        # load the bot's settings
        if self.settings["nsfw"]:
            # only proceed if nsfw is enabled in the bot's settings
            payload = {"tags": tags, "limit": 320}
            await ctx.trigger_typing()
            urllist = await url.monosodiumcarbonate(payload, "page")
            for x in range(0,10):
                try:
                    myurl = random.choice(urllist)
                    embed = discord.Embed(title="Link To picture", url=myurl)
                    embed.color = 0xff00cc
                    # change color to magenta
                    embed.set_image(url=myurl) 
                    await ctx.send(embed=embed)
                except Exception:
                    continue
        else:
            embed = discord.Embed(title="ERROR!", description="nsfw content is disabled")
            # send error message when nsfw is not enabled in the bot's settings
            embed.color = 0xC1121C # change color to red
            await ctx.send(embed=embed)

    @commands.is_nsfw() #only proceed when in an nsfw channel
    @commands.command()
    async def yanspam(self, ctx,count:int,*, tags):
        def is_author(m):
            return not m.content.startswith("[KEEP]")
        await ctx.channel.purge(limit=1, check=is_author, bulk=False)  
        self.yam = Yamler(f"{self.dirname}/data/settings.yml")
        self.settings = self.yam.load() # load the bot's settings
        if self.settings["nsfw"]:
            # only proceed if nsfw is enabled in the bot's settings
            if 0 < count <= 10:
            # only proceed if count is below 10
                payload = {
                "limit": 100,
                "tags": tags
                }
                await ctx.trigger_typing()
                urllist = await url.xml_sequence_parse(payload,"https://yande.re/post.xml","sample_url","page",True)
                for x in range(0,count):
                    choice = random.choice(urllist)
                    embed = discord.Embed(title="Link To picture", url=choice)
                    embed.color = 0xff00cc# change color to magenta
                    embed.set_image(url=choice) 
                    await ctx.send(embed=embed)                
            else:
                embed = discord.Embed(title="ERROR!", description="enter a number between 0 and 10")
                # send error message when count is too high
                embed.color = 0xC1121C # change color to red
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="ERROR!", description="nsfw content is disabled")
            # send error message when nsfw is not enabled in the bot's settings
            embed.color = 0xC1121C # change color to red
            await ctx.send(embed=embed)
    
    @commands.is_nsfw() #only proceed when in an nsfw channel
    @commands.command()
    async def r34spam(self, ctx,count:int,*, tags):
            def is_author(m):
                return not m.content.startswith("[KEEP]")
            await ctx.channel.purge(limit=1, check=is_author, bulk=False)            
            self.yam = Yamler(f"{self.dirname}/data/settings.yml")
            self.settings = self.yam.load() # load the bot's settings
            if self.settings["nsfw"]:
                # only proceed if nsfw is enabled in the bot's settings
                if 0 < count <= 10:
                # only proceed if count is below 10
                    payload = { 
                    "page": "dapi",
                    "tags": tags,
                    "s": "post",
                    "q": "index"
                    }
                    await ctx.trigger_typing()
                    urllist = await url.xml_sequence_parse(payload,"https://rule34.xxx/index.php","sample_url","pid",True)
                    for x in range(0, count):
                        myurl = random.choice(urllist) 
                        embed = discord.Embed(title="Link To picture", url=myurl)
                        embed.color = 0xff00cc# change color to magenta
                        embed.set_image(url=myurl) 
                        await ctx.send(embed=embed)                
                else:
                    embed = discord.Embed(title="ERROR!", description="enter a number between 0 and 10")
                    # send error message when count is too high
                    embed.color = 0xC1121C # change color to red
                    await ctx.send(embed=embed)
            else:
                embed = discord.Embed(title="ERROR!", description="nsfw content is disabled")
                # send error message when nsfw is not enabled in the bot's settings
                embed.color = 0xC1121C # change color to red
                await ctx.send(embed=embed)

    @commands.command()
    async def markov(self, ctx, user, old:int=100, new:int=100):
        guild = ctx.guild
        author:discord.User = ctx.message.author

        is_user = True
        is_channel = False

        rest = re.findall("<#(\d+)>", user)
        if len(rest) > 0:
            is_user = False
            is_channel = True
            chan = ctx.guild.get_channel(int(rest[0]))
        if not is_channel:
            rest = re.findall("<@!(\d+)>$", user)
            if len(rest) > 0:
                is_user = True
                chan = self.bot.get_user(int(rest[0]))
            else:
                rest = re.findall("(\d+)", user)
                if len(rest) > 0 and not is_channel: 
                    is_user = True
                    chan = self.bot.get_user(int(rest[0]))
        try:
            await ctx.send("fetching messages ...")
            game = discord.Game("processing . . .")
            await self.bot.change_presence(status=discord.Status.do_not_disturb, activity=game)
            messages = []
            with ctx.channel.typing():
                if is_user and not is_channel:
                    for channel in guild.text_channels:
                        async for message in channel.history(limit=old, oldest_first=True):
                            if message.author == chan:
                                messages.append(str(message.content + "\n"))
                        async for message in channel.history(limit=new):
                            if message.author == chan:
                                messages.append(str(message.content + "\n"))     
                else:
                    async for message in chan.history(limit=old, oldest_first=True):
                        messages.append(str(message.content + "\n"))
                    async for message in chan.history(limit=new):
                        messages.append(str(message.content + "\n"))
                model = markovify.NewlineText("".join(messages))
                generated_list = []
                for i in range (5):
                    generated = model.make_sentence()
                    if generated != None: generated_list.append(generated)
                if len(generated_list) > 0:
                    def is_author(m):
                        return m.content == "fetching messages ..." and m.author.id == self.bot.user.id
                    await ctx.channel.purge(limit=10, check=is_author)
                    await asyncio.sleep(0.5)
                    embed = discord.Embed(title="**Markov Chain Output:**", description=f"*{'. '.join(generated_list)}*")
                    embed.color = 0x6E3513
                    embed.set_footer(icon_url=author.avatar_url, text=f"generated by {author}  the target was: {chan} settings: {old}o, {new}n")
                    await ctx.send(embed=embed)
                else:
                    await ctx.send(ctx, "an error has occured. I could not fetch enough messages!")
        except Exception as exc:
            print(exc)
            await errormsg(ctx, "Could not fetch enough messages! Please change the parameters and try again!")
        finally:
            await self.bot.change_presence(status=discord.Status.online, activity=None)

    def markov_clear(self):
        self.mgame_id = None
        self.mgame_tries = None
        self.mgame_name = None   

    @commands.group()
    async def mgame(self,ctx):
        pass

    @mgame.command()
    async def start(self,ctx,tries:int):
        guild:discord.Guild = ctx.guild
        memberlist = []
        async for member in guild.fetch_members():
            memberlist.append(member)
        the_chosen_one = random.choice(memberlist)
        print(the_chosen_one.id)
        self.mgame_id = the_chosen_one.id
        self.mgame_tries = tries
        self.mgame_name = the_chosen_one.name
        messages = []
        try:
            await ctx.send("fetching messages ...")
            game = discord.Game("processing . . .")
            await self.bot.change_presence(status=discord.Status.do_not_disturb, activity=game)
            messages = []
            with ctx.channel.typing():
                for channel in guild.text_channels:
                    async for message in channel.history(limit=random.randint(200, 666), oldest_first=True):
                        if message.author.id == the_chosen_one.id:
                            messages.append(str(message.content + "\n"))
                    async for message in channel.history(limit=random.randint(200, 666)):   
                        if message.author.id == the_chosen_one.id:
                            messages.append(str(message.content + "\n"))     
                model = markovify.NewlineText("".join(messages))
                generated_list = []
                random.shuffle(generated_list)
                for i in range (5):
                    generated = model.make_sentence()
                    if generated != None: generated_list.append(generated)
                if len(generated_list) > 0:
                    def is_author(m):
                        return m.content == "fetching messages ..." and m.author.id == self.bot.user.id
                    await ctx.channel.purge(limit=10, check=is_author)
                    await asyncio.sleep(0.5)
                    embed = discord.Embed(title="**Who could have said this?**", description=f"*{'. '.join(generated_list)}*")
                    await ctx.send(embed=embed)
                else:
                    await errormsg(ctx,"I could not fetch enough messages, please try again")
                    self.markov_clear()

        except Exception as exc:
            print(exc)
            await errormsg(ctx, "Could not fetch enough messages! Please change the parameters and try again!")
            self.markov_clear()

        finally:
            await self.bot.change_presence(status=discord.Status.online, activity=None)

    @mgame.command()
    async def guess(self,ctx,user):
        rest = re.findall("(\d+)", user)
        guild:discord.Guild = ctx.guild
        if len(rest) > 0:
            chan = int(rest[0])
        else: chan = 0
        chun = re.findall(f"{user.lower()}", self.mgame_name.lower())
        if self.mgame_id != None and self.mgame_tries != None:
            if chan == self.mgame_id or len(chun) != 0 and self.mgame_tries != 0:
                await ctx.send("YOU ARE RIGHT! Here's a cookie for you: 🍪")
                self.markov_clear()
            else:
                self.mgame_tries -= 1
                if self.mgame_tries == 0 or self.mgame_tries < 0:
                    await errormsg(ctx,f"Sorry but that was the wrong answer. You have lost. The right answer would have been: {self.mgame_name}")
                    self.markov_clear()
                else:
                    await ctx.send(f"Sorry, that was wrong, you now have only {self.mgame_tries} tries left ")
        else:
            await errormsg(ctx, "You cannot guess, if you you havn't started a game")

    @mgame.command()
    async def stop(self,ctx):
        self.markov_clear()
