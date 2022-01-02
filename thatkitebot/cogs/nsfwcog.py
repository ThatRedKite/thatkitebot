#  Copyright (c) 2019-2022 ThatRedKite and contributors

import asyncio
import typing
from random import choice, choices
import discord
from discord.ext import commands
from thatkitebot.backend import url
from thatkitebot.backend.util import errormsg
from thatkitebot.backend.util import EmbedColors as ec


class NSFW(commands.Cog, name="NSFW commands"):
    def __init__(self, bot):
        self.bot = bot
        self.redis = bot.redis
        self.bl = [424394851170385921]  # guild blacklist

    async def cog_check(self, ctx):
        return await self.redis.hget(ctx.guild.id, "NSFW") == "TRUE" and ctx.guild.id not in self.bl

    @commands.is_nsfw()  # only proceed when in an nsfw channel
    @commands.command(hidden=True, aliases=["rule34"])
    async def r34(self, ctx, *, tags):
        with ctx.channel.typing():
            myurl = await url.r34url(session=self.bot.aiohttp_session, tags=tags)
            if myurl:
                await ctx.send(embed=myurl)
            else:
                await errormsg(ctx, "__Nothing Found! Please check your tags and try again!__")

    @commands.is_nsfw()  # only proceed when in an nsfw channel
    @commands.command(hidden=True, aliases=["yande.re", "yandere"])
    async def yan(self, ctx, *, tags):
        #  only proceed if nsfw is enabled in the bot's settings
        with ctx.channel.typing():
            myurl = await url.yanurlget(session=self.bot.aiohttp_session, tags=tags)
            embed = discord.Embed(title="Link To picture", url=myurl)
            embed.color = ec.telemagenta
            embed.set_image(url=myurl)
            await ctx.send(embed=embed)

    @commands.is_nsfw()  # only proceed when in an nsfw channel
    @commands.command(hidden=True)
    async def yanspam(self, ctx, count: typing.Optional[int] = 5, *, tags):
        if count not in range(1, 11):
            await errormsg(ctx, "please use a number between 1 and 20")
        #  only proceed if count is below 10, otherwise send an error message
        else:
            with ctx.channel.typing():
                urllist = await url.yanurlget(session=self.bot.aiohttp_session, islist=True, tags=tags )
                outlist = set(choices(urllist, k=count + 2))
                for x in outlist:
                    await ctx.send(x)
                    await asyncio.sleep(0.2)

    @commands.is_nsfw()  # only proceed when in an nsfw channel
    @commands.command(hidden=True)
    async def r34spam(self, ctx: commands.Context, count: typing.Optional[int] = 10, *, tags):
        if 1 >= count or count > 10:
            await errormsg(ctx, "please use a number between 1 and 10")
        else:
            #  only proceed if count is below 10
            with ctx.channel.typing():
                urllist = await url.r34url(session=self.bot.aiohttp_session, tags=tags, islist=True, count=count)
                if urllist == ["__Nothing Found! Please check your tags and try again!__"]:
                    await errormsg(ctx, urllist[0])
                else:
                    for embed in urllist:
                        await ctx.send(embed=embed)

    @commands.is_nsfw()  # only proceed when in an nsfw channel
    @commands.command(hidden=True)
    async def e621(self, ctx, *, tags):
        async with ctx.channel.typing():
            urllist = await url.monosodiumglutamate(self.bot.aiohttp_session, tags)
            try:
                id, myurl = choice(urllist)
                embed = discord.Embed(title="link to original post", url=f"https://e621.net/posts/{id}")
                embed.color = ec.telemagenta
                embed.set_image(url=myurl)
            except IndexError:
                embed = await errormsg(ctx, "__Nothing Found! Please check your tags and try again!__", embed_only=True)
            finally:
                await ctx.send(embed=embed)

    @commands.is_nsfw()  # only proceed when in an nsfw channel
    @commands.command(hidden=True)
    async def e621spam(self, ctx, *, tags):
        async with ctx.channel.typing():
            urllist = await url.monosodiumglutamate(self.bot.aiohttp_session, tags)
            for x in range(5):
                try:
                    id, myurl = choice(urllist)
                    embed = discord.Embed(title="link to original post", url=f"https://e621.net/posts/{id}")
                    embed.color = ec.telemagenta
                    embed.set_image(url=myurl)
                except IndexError:
                    embed = await errormsg(ctx, "__Nothing Found! Please check your tags and try again!__", embed_only=True)
                finally:
                    await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(NSFW(bot))

