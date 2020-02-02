import discord
from bf.yamler import Yamler
from discord.ext import commands
import cogs
import os 

dirname = os.path.dirname(os.path.realpath(__file__))

tokens = Yamler("{0}/data/tokens.yml".format(dirname))

prefix = tokens.load()["prefix"]
bot = commands.Bot(command_prefix=prefix)

bot.add_cog(cogs.funstuffcog.FunStuff(bot, dirname))
bot.add_cog(cogs.utilitiescog.Utilities(bot, dirname))
bot.add_cog(cogs.listenercog.Listeners(bot, dirname))
bot.add_cog(cogs.sudocog.Sudostuff(bot, dirname))
bot.run(tokens.load()["discordtoken"])
