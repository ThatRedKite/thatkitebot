from discord.ext import commands
import discord
import requests
import asyncio
from bf import url
from bf.yamler import Yamler
class FunStuff(commands.Cog):
    def __init__(self, bot, dirname, settings):
        self.bot = bot
        self._last_member = None
        self.settings = settings
        self.dirname = dirname
        print(self.settings)

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
            myurl = await url.urlgetter(payload,"https://rule34.xxx/index.php","sample_url","pid") # get a sample_url
            embed = discord.Embed(title="Link To picture", url=myurl)
            embed.color = 0xff00cc # change color to magenta
            embed.set_image(url=myurl) 
            await ctx.send(embed=embed) 
        else:
            embed = discord.Embed(title="ERROR!", description="nsfw content is disabled")
            # send error message when nsfw is not enabled in the bot's settings
            embed.color = 0xff0000 # change color to red
            await ctx.send(embed=embed)

    @commands.is_nsfw() #only proceed when in an nsfw channel
    @commands.command()
    async def yan(self, ctx,*, tags):
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
            myurl = await url.urlgetter(payload,"https://yande.re/post.xml","sample_url","page") # get a sample_url
            embed = discord.Embed(title="Link To picture", url=myurl)
            embed.color = 0xff00cc
            # change color to magenta
            embed.set_image(url=myurl) 
            await ctx.send(embed=embed) 
        else:
            embed = discord.Embed(title="ERROR!", description="nsfw content is disabled")
            # send error message when nsfw is not enabled in the bot's settings
            embed.color = 0xff0000 # change color to red
            await ctx.send(embed=embed)

    @commands.is_nsfw() #only proceed when in an nsfw channel
    @commands.command()
    async def yanspam(self, ctx,count:int,*, tags):
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
                urllist = await url.urlgetter(payload,"https://yande.re/post.xml","sample_url","page",True, count)
                for myurl in urllist:
                    embed = discord.Embed(title="Link To picture", url=myurl)
                    embed.color = 0xff00cc# change color to magenta
                    embed.set_image(url=myurl) 
                    await ctx.send(embed=embed)                
            else:
                embed = discord.Embed(title="ERROR!", description="enter a number between 0 and 10")
                # send error message when count is too high
                embed.color = 0xff0000 # change color to red
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="ERROR!", description="nsfw content is disabled")
            # send error message when nsfw is not enabled in the bot's settings
            embed.color = 0xff0000 # change color to red
            await ctx.send(embed=embed)
            