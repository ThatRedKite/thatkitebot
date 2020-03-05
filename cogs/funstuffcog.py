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

    @commands.is_nsfw()
    @commands.command()
    async def r34(self, ctx, tag1, tag2=""):
        await ctx.trigger_typing()
        myurl = await url.urlgetter([tag1, tag2])
        embed = discord.Embed(title="here's a naughty pic for you")
        embed.color = 0xff00cc
        embed.set_image(url=myurl)
        await ctx.send(embed=embed)

    @commands.is_nsfw()
    @commands.command()
    async def yan(self, ctx,*, tags):
        self.yam = Yamler(f"{self.dirname}/data/settings.yml")
        self.settings = self.yam.load()
        if self.settings["nsfw"]:
            taglist = []
            for tag in tags.split(" "):
                taglist.append(tag)

            myurl = await url.yandere(taglist)
            embed = discord.Embed(title="here's a naughty pic for you")
            embed.color = 0xff00cc
            embed.set_image(url=myurl)
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="ERROR!", description="nsfw content is disabled")
            embed.color = 0xff0000
            await ctx.send(embed=embed)

