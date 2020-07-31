import typing
import discord
from bf import url
from random import choice
from bf.util import errormsg
from discord.ext import commands
from concurrent.futures import ThreadPoolExecutor

class NSFW(commands.Cog):
    def __init__(self,bot):
        self.bot=bot
        self.yanurl="https://yande.re/post.xml"
        self.r34url="https://rule34.xxx/index.php"

    @commands.is_nsfw() # only proceed when in an nsfw channel
    @commands.command()
    async def r34(self, ctx, *, tags):
        if self.bot.settings[str(ctx.message.guild.id)]["bnsfw"]:
            #  only proceed if nsfw is enabled in the bot's settings
            payload={ "page": "dapi","tags": tags,"s": "post","q": "index"}
            with ctx.channel.typing():
                myurl=url.xml_sequence_parse(session=self.bot.aiohttp_session,
                                      payload=payload,
                                      sourceurl=self.r34url,
                                      attr="sample_url",
                                      updatevalue="pid")

                embed=discord.Embed(title="Link To picture", url=myurl)
                embed.color=0xff00cc
                embed.set_image(url=myurl) 
                await ctx.send(embed=embed) 
        else:
            await errormsg(ctx,"nsfw content is disabled")

    @commands.is_nsfw() # only proceed when in an nsfw channel
    @commands.command()
    async def yan(self, ctx, *, tags):
        if self.bot.settings[str(ctx.message.guild.id)]["bnsfw"]:
            #  only proceed if nsfw is enabled in the bot's settings
            payload={"limit": 100,"tags": tags}
            with ctx.channel.typing():
                myurl=await url.xml_sequence_parse(session=self.bot.aiohttp_session,
                                            payload=payload,
                                            sourceurl=self.yanurl,
                                            attr="jpeg_url",
                                            updatevalue="pid")
                embed=discord.Embed(title="Link To picture", url=myurl)
                embed.color=0xff00cc
                embed.set_image(url=myurl) 
                await ctx.send(embed=embed) 
        else:
            await errormsg(ctx,"nsfw content is disabled")

    @commands.is_nsfw() # only proceed when in an nsfw channel
    @commands.command()
    async def yanspam(self, ctx, count:typing.Optional[int]=10, *, tags):
        #  only proceed if nsfw is enabled in the bot's settings
        if self.bot.settings[str(ctx.message.guild.id)]["bnsfw"]:
            maxlength=self.bot.settings
            #  only proceed if count is below 10, otherwise send an error message
            if count in range(1,20):
                payload={"limit": 100,"tags": tags}
                with ctx.channel.typing():
                    urllist = await url.xml_sequence_parse(session=self.bot.aiohttp_session,
                                                payload=payload,
                                                sourceurl=self.yanurl,
                                                attr="jpeg_url",
                                                updatevalue="page",
                                                islist=True)

                    with ctx.channel.typing():
                        for x in range(0, count):
                            myurl=choice(urllist)
                            embed=discord.Embed(title="Link To picture", url=myurl)
                            embed.color=0xff00cc#  change color to magenta
                            embed.set_image(url=myurl) 
                            await ctx.send(embed=embed)                
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
                    payload={ "page": "dapi","tags": tags,"s": "post","q": "index"}
                    with ctx.channel.typing():
                        with ThreadPoolExecutor() as executor:
                            future=executor.submit(url.xml_sequence_parse,
                                                    payload=payload,
                                                    sourceurl=self.yanurl,
                                                    attr="jpeg_url",
                                                    updatevalue="page",
                                                    islist=True)
                        urllist=future.result()
                        with ctx.channel.typing():
                            for x in range(0, count):
                                myurl=choice(urllist) 
                                embed=discord.Embed(title="Link To picture", url=myurl)
                                embed.color=0xff00cc#  change color to magenta
                                embed.set_image(url=myurl) 
                                await ctx.send(embed=embed)                
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
