import os
import psutil
import discord
from discord.ext import commands, tasks
import gc


class utility_commands(commands.Cog):
    def __init__(self, bot:commands.Bot, dirname):
        self.dirname=dirname
        self.process=psutil.Process(os.getpid())
        self.bot=bot
        self.garbage.start()

    @tasks.loop(minutes=2.0)
    async def garbage(self):
        gc.collect()

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

