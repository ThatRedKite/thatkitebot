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
import asyncio
import typing
from random import choice, choices

import discord
from discord.ext import commands

from thatkitebot.base import url
from thatkitebot.base.util import errormsg
from thatkitebot.base.util import EmbedColors as ec
from thatkitebot.tkb_redis.settings import RedisFlags
#endregion

#region Cog
class NSFW(commands.Cog, name="NSFW commands"):
    """
    NSFW commands. Only usable in NSFW channels and disabled by default.
    """
    def __init__(self, bot):
        self.bot = bot
        self.redis = bot.redis
        self.bl = [424394851170385921]  # hardcoded guild blacklist, for my own sanity

    async def cog_check(self, ctx):
        return await RedisFlags.get_guild_flag(self.redis, ctx.guild, RedisFlags.FlagEnum.NSFW)

    @commands.is_nsfw()  # only proceed when in an NSFW channel
    @commands.command(hidden=True, aliases=["rule34"])
    async def r34(self, ctx, *, tags):
        with ctx.channel.typing():
            chosen_url = await url.r34url(session=self.bot.aiohttp_session, tags=tags)
            if chosen_url:
                await ctx.send(embed=chosen_url)
            else:
                await errormsg(ctx, "__Nothing Found! Please check your tags and try again!__")

    @commands.is_nsfw()  # only proceed when in an NSFW channel
    @commands.command(hidden=True, aliases=["yande.re", "yandere"])
    async def yan(self, ctx, *, tags):
        #  only proceed if nsfw is enabled in the bot's settings
        with ctx.channel.typing():
            chosen_url = await url.get_yan_url(session=self.bot.aiohttp_session, tags=tags)
            embed = discord.Embed(title="Link To picture", url=chosen_url)
            embed.color = ec.telemagenta
            embed.set_image(url=chosen_url)
            await ctx.send(embed=embed)

    @commands.is_nsfw()  # only proceed when in an NSFW channel
    @commands.command(hidden=True)
    async def yanspam(self, ctx, count: typing.Optional[int] = 5, *, tags):
        if count not in range(1, 11):
            await errormsg(ctx, "please use a number between 1 and 20")
        #  only proceed if count is below 10, otherwise send an error message
        else:
            with ctx.channel.typing():
                url_list = await url.get_yan_url(session=self.bot.aiohttp_session, islist=True, tags=tags)
                output_list = set(choices(url_list, k=count + 2))
                for x in output_list:
                    await ctx.send(x)
                    await asyncio.sleep(0.2)

    @commands.is_nsfw()  # only proceed when in an NSFW channel
    @commands.command(hidden=True)
    async def r34spam(self, ctx: commands.Context, count: typing.Optional[int] = 10, *, tags):
        if 1 >= count or count > 10:
            await errormsg(ctx, "please use a number between 1 and 10")
        else:
            #  only proceed if count is below 10
            with ctx.channel.typing():
                url_list = await url.r34url(session=self.bot.aiohttp_session, tags=tags, islist=True, count=count)
                if url_list == ["__Nothing Found! Please check your tags and try again!__"]:
                    await errormsg(ctx, url_list[0])
                else:
                    for embed in url_list:
                        await ctx.send(embed=embed)

    @commands.is_nsfw()  # only proceed when in an NSFW channel
    @commands.command(hidden=True)
    async def e621(self, ctx, *, tags):
        async with ctx.channel.typing():
            url_list = await url.monosodiumglutamate(self.bot.aiohttp_session, tags)
            try:
                post_id, chosen_id = choice(url_list)
                embed = discord.Embed(title="link to original post", url=f"https://e621.net/posts/{post_id}")
                embed.color = ec.telemagenta
                embed.set_image(url=chosen_id)
            except IndexError:
                embed = await errormsg(ctx, "__Nothing Found! Please check your tags and try again!__", embed_only=True)
            finally:
                await ctx.send(embed=embed)

    @commands.is_nsfw()  # only proceed when in an NSFW channel
    @commands.command(hidden=True)
    async def e621spam(self, ctx, *, tags):
        async with ctx.channel.typing():
            url_list = await url.monosodiumglutamate(self.bot.aiohttp_session, tags)
            for x in range(5):
                try:
                    post_id, chosen_url = choice(url_list)
                    embed = discord.Embed(title="link to original post", url=f"https://e621.net/posts/{post_id}")
                    embed.color = ec.telemagenta
                    embed.set_image(url=chosen_url)
                except IndexError:
                    embed = await errormsg(ctx, "__Nothing Found! Please check your tags and try again!__", embed_only=True)
                finally:
                    await ctx.send(embed=embed)
#endregion

def setup(bot):
    bot.add_cog(NSFW(bot))

