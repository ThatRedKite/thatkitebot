from logging import error
import re
import random
import discord
from bf import url
from bf.util import  errormsg
from discord.ext import commands
from asyncio import sleep as asleep

class listeners(commands.Cog):
    def __init__(self, bot, dirname,):
        self.dirname=dirname
        self.bot:discord.Client=bot
        
    @commands.Cog.listener()
    async def on_command_error(self,ctx,error):
        print("whoops")
        