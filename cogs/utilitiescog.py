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
    async def status(self, ctx):
        """
        Bot's Current Status
        """
        process = psutil.Process(self.bot.pid)
        mem = int(round((process.memory_info()[0] / 1000000)))
        cpu = process.cpu_percent(interval=1)
        cores_used = len(process.cpu_affinity())
        cores_total = psutil.cpu_count()
        ping = round(self.bot.latency * 1000, 1)
        uptime = str(datetime.now() - self.bot.starttime).split(".")[0]

        embed = discord.Embed(title="__Status of {0}__".format(self.bot.user.name, description=" "))
        embed.add_field(name="**RAM usage 🖪**", value=f"`{mem} MB`", inline=True)
        embed.add_field(name="**CPU usage 💻**",value=f"`{cpu}%`")
        embed.add_field(name="**Cores**", value=f"`{cores_used} / {cores_total}`")
        embed.add_field(name="**Ping 🏓**", value=f"`{ping} ms`")
        embed.add_field(name="**Debug Mode 🐛**", value=f"`{self.bot.debugmode}`")
        embed.color = 0x00ff00
        embed.add_field(name="**Uptime ⏲**", value=f"`{uptime}`")
        embed.set_footer(text="version: {}".format(self.bot.version))
        embed.set_thumbnail(url=str(self.bot.user.avatar_url))
        await ctx.trigger_typing()
        await ctx.send(embed=embed)

        

