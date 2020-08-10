
import os
import re
import psutil
import discord
import logging
import subprocess
from PIL import Image
from bf.util import errormsg
from datetime import datetime
from discord.ext import commands

class utility_commands(commands.Cog):
    def __init__(self, bot:commands.Bot, dirname):
        self.dirname=dirname
        self.bot=bot
        self.version=self.bot.version
        self._last_member=None

    @commands.cooldown(1,5,commands.BucketType.user)
    @commands.command()
    async def help(self,ctx):
        embed = discord.Embed(title="**a list of the bot's commands**")
        for cog in self.bot.cogs:
            commandstring = "" 
            for command in self.bot.get_cog(cog).walk_commands():
                if cog != "NSFW":
                    commandstring += f"{command}\n"
            if len(commandstring) > 1:
                embed.add_field(name=f"__**[{cog}]**__", value=f"```fix\n{commandstring}```",inline=False) 
        embed.set_footer(text=f"\nThatKiteBot² version {self.bot.version}", icon_url=self.bot.user.avatar_url)
        await ctx.send(embed=embed)
