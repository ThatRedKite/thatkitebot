from discord.ext import commands
from bf.yamler import Yamler
import psutil
import discord
import logging
import string
import os
logging.basicConfig(filename="test.log", level=logging.WARNING, format="%(levelname)s|%(message)s| @ %(asctime)s")

class Sudostuff(commands.Cog):
    def __init__(self, bot):
      self.bot = bot
      self._last_member = None
      yam = Yamler("data/banlist.yml")
      self.banlist = yam.load()
      

    @commands.group()
    @commands.is_owner()
    async def sudo(self,ctx):
        """
        only for ThatRedKite
        """
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(title="ERROR!", description="Please enter a valid Command")
            embed.color = 0xff0000
            await ctx.trigger_typing()
            await ctx.send(embed=embed)

    @sudo.error
    async def sudo_error(self, ctx, error):
        if isinstance(error, commands.errors.NotOwner):
            embed = discord.Embed(title="ERROR!", description="__*only ThatRedKite can do this*__")
            embed.color = 0xff0000
            logging.info(error)
            await ctx.trigger_typing()
            await ctx.send(embed=embed)

    @sudo.command()
    async def signal(self, ctx, signal:str):
        """
        returns: sends a signal to the process
        """
        signals = {
            "TERM": psutil.signal.SIGTERM,
            "KILL": psutil.signal.SIGKILL,
            "QUIT": psutil.signal.SIGQUIT,
            "HUP": psutil.signal.SIGHUP
        }

        process = psutil.Process(os.getpid())
        logging.warning("bot is shutting down")
        process.send_signal(signals[(signal.upper())])

    @signal.error
    async def signal_error(self, ctx, error):
        if isinstance(error, commands.errors.CommandInvokeError):
            embed = discord.Embed(title="ERROR!", description="Please enter a valid signal!")
            embed.color = 0xff0000
            await ctx.trigger_typing()
            await ctx.send(embed=embed)
        logging.error(msg=error)

    @sudo.command()
    async def ban(self,ctx,*,banned:str):
        if banned not in self.banlist:
            yam = Yamler("data/banlist.yml")
            embed = discord.Embed(title="Success!", description="Banned `{0}`".format(banned))
            embed.color = 0x00ff00
            self.banlist.append(banned)
            yam.write(self.banlist)

        elif banned in banned in self.banlist:
            embed = discord.Embed(title="ERROR!", description="`{0}` is already banned!".format(banned))
            embed.color = 0xff0000
        await ctx.trigger_typing()
        await ctx.send(embed=embed)

    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            embed = discord.Embed(title="ERROR!", description="You gave the command no arguments!")
            embed.color = 0xff0000
            await ctx.trigger_typing()
            await ctx.send(embed=embed)

    @sudo.command()
    async def listbans(self,ctx):
        output = ""
        for ban in self.banlist:
            output += "{0}\n".format(ban)
        embed = discord.Embed(title="list of banned *things*", description=output)
        embed.set_footer(text="Total bans: {}".format(len(self.banlist)))
        embed.color = 0x00ff00
        await ctx.trigger_typing()
        await ctx.send(embed=embed)

    @sudo.command()
    async def unban(self,ctx,*,banned:str):
        if banned in self.banlist:
            yam = Yamler("data/banlist.yml")
            embed = discord.Embed(title="Success!", description="unbanned `{0}`".format(banned))
            embed.color = 0x00ff00
            self.banlist.remove(banned)
            yam.write(self.banlist)

        elif banned not in self.banlist:
            embed = discord.Embed(title="ERROR!", description="`{0}` is not banned!".format(banned))
            embed.color = 0xff0000

        await ctx.trigger_typing()
        await ctx.send(embed=embed)

    @unban.error
    async def unban_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            embed = discord.Embed(title="ERROR!", description="You gave the command no arguments!")
            embed.color = 0xff0000
            await ctx.trigger_typing()
            await ctx.send(embed=embed)
