import os
import re
import psutil
import discord
import logging
from bf import util
from bf.yamler import Tomler
from discord.ext import commands
from concurrent.futures import  ThreadPoolExecutor
class sudo_commands(commands.Cog):
    def __init__(self, bot, dirname):
        self.bot=bot
        self.dirname=dirname
        self._last_member=None
        self.tom = Tomler(dirname)
        self.settings=self.bot.settings
        logging.basicConfig(filename="{0}/test.log".format(self.dirname), level=logging.WARNING, format="%(levelname)s|%(message)s| @ %(asctime)s")

    @commands.group()
    @commands.is_owner()
    async def sudo(self,ctx):
        """
        only for ThatRedKite#0815
        """
        if ctx.invoked_subcommand is None:
            embed=discord.Embed(title="ERROR!", description="Please enter a valid Command")
            embed.color=0xC1121C
            await ctx.trigger_typing()
            await ctx.send(embed=embed)

    @sudo.error
    async def sudo_error(self, ctx, error):
        if isinstance(error, commands.errors.NotOwner):
            embed=discord.Embed(title="ERROR!", description="__*only ThatRedKite can do this*__")
            embed.color=0xC1121C
            logging.info(error)
            await ctx.trigger_typing()
            await ctx.send(embed=embed)

    @sudo.command()
    async def signal(self, ctx, signal:str):
        """
        returns: sends a signal to the process
        """
        signals={
            "TERM": psutil.signal.SIGTERM,
            "KILL": psutil.signal.SIGKILL,
            "QUIT": psutil.signal.SIGQUIT,
            "HUP": psutil.signal.SIGHUP
        }

        process=psutil.Process(os.getpid())
        logging.warning("bot is shutting down")
        process.send_signal(signals[(signal.upper())])

    @signal.error
    async def signal_error(self, ctx, error):
        if isinstance(error, commands.errors.CommandInvokeError):
            embed=discord.Embed(title="ERROR!", description="Please enter a valid signal!")
            embed.color=0xC1121C
            await ctx.trigger_typing()
            await ctx.send(embed=embed)
        logging.error(msg=error)

    @sudo.command()
    async def setting(self,ctx, setting, parameter):
        with ThreadPoolExecutor(2) as executor:
            executor.submit(self.bot.tom.update,{setting:util.typeguesser(setting,parameter)},ctx.guild.id)
            self.bot.settings[str(ctx.guild.id)].update({setting:util.typeguesser(setting,parameter)})
            
        embed=discord.Embed(title="Success!", description=f"set `{setting}` to `{parameter}`")
        embed.color=0xC1121C
        await ctx.send(embed=embed)
        
    @sudo.command()
    async def purgeme(self,ctx,count:int=10):
        await ctx.channel.purge(limit=count, check=lambda m: m.author == self.bot.user, bulk=True)

    @sudo.command()
    async def purge(self,ctx,count:int=10, user=None):
        if user != None:
            rest=re.findall("<#(\d+)>", user)
            chan=ctx.guild.get_user(int(rest[0]))
        else:
            chan=ctx.channel
