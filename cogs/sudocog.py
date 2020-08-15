from bf import util
import discord
import logging
from bf.yamler import Tomler
from discord.ext import commands
from concurrent.futures import  ThreadPoolExecutor
class sudo_commands(commands.Cog):
    def __init__(self, bot, dirname):
        self.bot=bot
        self.dirname=dirname

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

