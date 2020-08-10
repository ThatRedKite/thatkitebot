import asyncio
import typing
import discord
from bf import url
from random import choice,choices
from bf.util import errormsg
from discord.ext import commands
from concurrent.futures import ThreadPoolExecutor

class NSFW(commands.Cog):
    def __init__(self,bot):
        self.bot=bot
        self.r34url="https://rule34.xxx/index.php"

    @commands.is_nsfw() # only proceed when in an nsfw channel
    @commands.command()
    async def r34(self, ctx, *, tags):
        if self.bot.settings[str(ctx.message.guild.id)]["bnsfw"]:
            #  only proceed if nsfw is enabled in the bot's settings
            with ctx.channel.typing():
                myurl=await url.r34url(session=self.bot.aiohttp_session,tags=tags)
                if len(myurl) == 0:
                    await errormsg(ctx,"__Nothing Found! Please check your tags and try again!__")
                else:
                    await ctx.send(myurl)
        else:
            await errormsg(ctx,"nsfw content is disabled")

    @commands.is_nsfw() # only proceed when in an nsfw channel
    @commands.command()
    async def yan(self, ctx, *, tags):
        if self.bot.settings[str(ctx.message.guild.id)]["bnsfw"]:
            #  only proceed if nsfw is enabled in the bot's settings
            with ctx.channel.typing():
                myurl=await url.yanurlget(
                                    session=self.bot.aiohttp_session,
                                    tags=tags
                                    )
                embed=discord.Embed(title="Link To picture", url=myurl)
                embed.color=0xff00cc
                embed.set_image(url=myurl) 
                await ctx.send(embed=embed) 
        else:
            await errormsg(ctx,"nsfw content is disabled")

    @commands.is_nsfw() # only proceed when in an nsfw channel
    @commands.command()
    async def yanspam(self,ctx,count:typing.Optional[int]=5,*,tags):
        #  only proceed if nsfw is enabled in the bot's settings
        if self.bot.settings[str(ctx.message.guild.id)]["bnsfw"]:
            #  only proceed if count is below 10, otherwise send an error message
            if count in range(1,11):
                with ctx.channel.typing():
                    urllist=await url.yanurlget(
                                        session=self.bot.aiohttp_session,
                                        islist=True,
                                        tags=tags
                                        )
                    with ctx.channel.typing():
                        outlist=set(choices(urllist,k=count+2))
                        for x in outlist:
                            await ctx.send(x)
                            await asyncio.sleep(0.2)         
            else:
                await errormsg(ctx,"please use a number between 1 and 20")
        else:
            await errormsg(ctx,"nsfw content is disabled")
    
    @commands.is_nsfw() # only proceed when in an nsfw channel
    @commands.command()
    async def r34spam(self, ctx, count:typing.Optional[int]=10, *, tags):
            if self.bot.settings[str(ctx.message.guild.id)]["bnsfw"]:
                #  only proceed if nsfw is enabled in the bot's settings
                if 1 < count <= 10:
                #  only proceed if count is below 10
                    with ctx.channel.typing():
                        urllist=await url.r34url(session=self.bot.aiohttp_session,tags=tags,islist=True,count=count)
                        if urllist ==  ["__Nothing Found! Please check your tags and try again!__"]:
                            await errormsg(ctx,"__Nothing Found! Please check your tags and try again!__")
                        else:
                            for x in urllist:
                                await ctx.send(x)
                                await asyncio.sleep(0.2)      
                else:
                    await errormsg(ctx,"please use a number between 1 and 20")
            else:
                await errormsg(ctx,"nsfw content is disabled")

    @commands.is_nsfw() # only proceed when in an nsfw channel
    @commands.command()
    async def e621(self, ctx, *,tags):
        if self.bot.settings[str(ctx.message.guild.id)]["bnsfw"]:
            #  only proceed if nsfw is enabled in the bot's settings
            payload={"tags": tags, "limit": 320}
            await ctx.trigger_typing()
            with ThreadPoolExecutor() as executor:
                future=executor.submit(url.monosodiumglutamate,payload,"page")
            urllist=future.result()
            with ctx.channel.typing():
                for x in range(0, 10):
                    try:
                        myurl=choice(urllist)
                        embed=discord.Embed(title="Link To picture", url=myurl)
                        embed.color=0xff00cc
                        #  change color to magenta
                        embed.set_image(url=myurl) 
                        await ctx.send(embed=embed)
                    except Exception:
                        continue
        else:
            await errormsg(ctx,"nsfw content is disabled")
