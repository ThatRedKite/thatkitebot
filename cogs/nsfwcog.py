import discord
from discord.ext import commands
from bf import url
import random
import typing
from bf.util import errormsg
class NSFW(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.yanurl = "https://yande.re/post.xml"
        self.r34url = "https://rule34.xxx/index.php"

    @commands.is_nsfw() # only proceed when in an nsfw channel
    @commands.command()
    async def r34(self, ctx, *, tags):
        if self.bot.settings[str(ctx.message.guild.id)]["nsfw"]:
            #  only proceed if nsfw is enabled in the bot's settings
            payload={ "page": "dapi","tags": tags,"s": "post","q": "index"}
            with ctx.channel.typing():
                myurl=await url.xml_sequence_parse(payload, self.r34url, "sample_url", "pid") #  get a sample_url
                embed=discord.Embed(title="Link To picture", url=myurl)
                embed.color=0xff00cc #  change color to magenta
                embed.set_image(url=myurl) 
                await ctx.send(embed=embed) 
        else:
            embed=discord.Embed(title="ERROR!", description="nsfw content is disabled")
            #  send error message when nsfw is not enabled in the bot's settings
            embed.color=0xC1121C #  change color to red
            await ctx.send(embed=embed)

    @commands.is_nsfw() # only proceed when in an nsfw channel
    @commands.command()
    async def yan(self, ctx, *, tags):
        if self.bot.settings[str(ctx.message.guild.id)]["nsfw"]:
            #  only proceed if nsfw is enabled in the bot's settings
            payload={"limit": 100,"tags": tags}
            with ctx.channel.typing():
                myurl=await url.xml_sequence_parse(payload, self.yanurl, "sample_url", "page", False) #  get a sample_url
                embed=discord.Embed(title="Link To picture", url=myurl)
                embed.color=0xff00cc
                #  change color to magenta
                embed.set_image(url=myurl) 
                await ctx.send(embed=embed) 
        else:
            errormsg(ctx,"nsfw content is disabled")

    @commands.is_nsfw() # only proceed when in an nsfw channel
    @commands.command()
    async def e621(self, ctx, *,tags):
        if self.bot.settings[str(ctx.message.guild.id)]["nsfw"]:
            #  only proceed if nsfw is enabled in the bot's settings
            payload={"tags": tags, "limit": 320}
            await ctx.trigger_typing()
            urllist=await url.monosodiumglutamate(payload, "page")
            with ctx.channel.typing():
                for x in range(0, 10):
                    try:
                        myurl=random.choice(urllist)
                        embed=discord.Embed(title="Link To picture", url=myurl)
                        embed.color=0xff00cc
                        #  change color to magenta
                        embed.set_image(url=myurl) 
                        await ctx.send(embed=embed)
                    except Exception:
                        continue
        else:
            embed=discord.Embed(title="ERROR!", description="nsfw content is disabled")
            #  send error message when nsfw is not enabled in the bot's settings
            embed.color=0xC1121C #  change color to red
            await ctx.send(embed=embed)

    @commands.is_nsfw() # only proceed when in an nsfw channel
    @commands.command()
    async def yanspam(self, ctx, count:typing.Optional[int]=10, *, tags):
        #  only proceed if nsfw is enabled in the bot's settings
        if self.bot.settings[str(ctx.message.guild.id)]["nsfw"]:
            #  only proceed if count is below 10, otherwise send an error message
            if 0 < count <= 10:
                payload={"limit": 100,"tags": tags}
                await ctx.trigger_typing()
                urllist=await url.xml_sequence_parse(payload, self.yanurl, "sample_url", "page", True)
                with ctx.channel.typing():
                    for x in range(0, count):
                        choice=random.choice(urllist)
                        embed=discord.Embed(title="Link To picture", url=choice)
                        embed.color=0xff00cc#  change color to magenta
                        embed.set_image(url=choice) 
                        await ctx.send(embed=embed)                
            else:
                embed=discord.Embed(title="ERROR!", description="enter a number between 0 and 10")
                # send error message when count is too high
                embed.color=0xC1121C # change color to red
                await ctx.send(embed=embed)
        else:
            embed=discord.Embed(title="ERROR!", description="nsfw content is disabled")
            # send error message when nsfw is not enabled in the bot's settings
            embed.color=0xC1121C # change color to red
            await ctx.send(embed=embed)
    
    @commands.is_nsfw() # only proceed when in an nsfw channel
    @commands.command()
    async def r34spam(self, ctx, count:typing.Optional[int]=10, *, tags):
            if self.bot.settings[str(ctx.message.guild.id)]["nsfw"]:
                #  only proceed if nsfw is enabled in the bot's settings
                if 1 < count <= 10:
                #  only proceed if count is below 10
                    payload={ "page": "dapi","tags": tags,"s": "post","q": "index"}
                    await ctx.trigger_typing()
                    urllist=await url.xml_sequence_parse(payload, self.r34url, "sample_url", "pid", True)
                    with ctx.channel.typing():
                        for x in range(0, count):
                            myurl=random.choice(urllist) 
                            embed=discord.Embed(title="Link To picture", url=myurl)
                            embed.color=0xff00cc#  change color to magenta
                            embed.set_image(url=myurl) 
                            await ctx.send(embed=embed)                
                else:
                    embed=discord.Embed(title="ERROR!", description="enter a number between 1 and 10")
                    #  send error message when count is too high
                    embed.color=0xC1121C #  change color to red
                    await ctx.send(embed=embed)
            else:
                embed=discord.Embed(title="ERROR!", description="nsfw content is disabled")
                #  send error message when nsfw is not enabled in the bot's settings
                embed.color=0xC1121C #  change color to red
                await ctx.send(embed=embed)