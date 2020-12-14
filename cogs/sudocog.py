#  MIT License
#
#  Copyright (c) 2020 ThatRedKite
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from backend import util
import discord
import asyncio
from discord.ext import commands


class sudo_commands(commands.Cog):
    def __init__(self, bot, dirname):
        self.bot: commands.Bot = bot
        self.dirname = dirname

    @commands.is_owner()
    @commands.command()
    async def kill(self, ctx):
        await self.bot.change_presence(status=discord.Status.offline)
        # clear the temp file folder
        util.clear_temp_folder(self.dirname)
        # close the aiohttp session
        await self.bot.aiohttp_session.close()
        # close the discord session
        await self.bot.close()
        # close the tom session

    @commands.is_owner()
    @commands.command()
    async def botpurge(self,ctx,count:int=100):
        me=self.bot.user
        messages=list()
        channel:discord.TextChannel=ctx.channel
        msgcounter=0
        async for message in channel.history(limit=5000).filter(lambda x: x.author == me):
            msgcounter += 1
            if msgcounter < count:
                await message.delete()
            else:
                break
    
    @commands.is_owner()
    @commands.command()
    async def debug(self,ctx,state:str):
        self.bot.debugmode=util.bool_parse(state)
        msg=await ctx.send(f"set debug to {self.bot.debugmode}")
        await asyncio.sleep(2)
        await msg.delete()
