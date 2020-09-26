import os
from discord.ext.commands.core import Command
import psutil
import discord
from discord.ext import commands, tasks
from datetime import datetime
class utility_commands(commands.Cog):
    def __init__(self, bot:commands.Bot, dirname):
        self.dirname=dirname
        self.process=psutil.Process(os.getpid())
        self.bot=bot
    
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
                embed.add_field(name=f"**{cog}**", value=f"\n{commandstring}",inline=True) 
        embed.set_footer(text=f"\nThatKiteBot² version {self.bot.version}", icon_url=self.bot.user.avatar_url)
        await ctx.send(embed=embed)
    
    @commands.cooldown(1,5,commands.BucketType.user)
    @commands.command(pass_context=True,aliases=["uptime", "load"])
    async def status(self,ctx):
        """
        show the bot's load
        """
        uptime=str(datetime.now() - self.bot.starttime).split(".")[0]
        message = await ctx.send(f"uptime: {uptime}")
    
        

