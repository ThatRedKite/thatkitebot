import discord
from bf.yamler import Yamler
from discord.ext import commands
import cogs
import os
import pathlib
empty = {
    "discordtoken": "",
    "prefix": ""
}
dirname = os.path.dirname(os.path.realpath(__file__))
path = pathlib.Path(f"{dirname}/data/tokens.yml")
tokens = Yamler(path)

if not path.exists():
    tokens.initialize(empty)
prefix = tokens.load()["prefix"]
settings = Yamler(f"{dirname}/data/settings.yml").load()

bot = commands.Bot(command_prefix=prefix)
bot.remove_command("help")
bot.add_cog(cogs.funstuffcog.FunStuff(bot, dirname, settings))
bot.add_cog(cogs.utilitiescog.Utilities(bot, dirname))
bot.add_cog(cogs.listenercog.Listeners(bot, dirname))
bot.add_cog(cogs.sudocog.Sudostuff(bot, dirname))
bot.run(tokens.load()["discordtoken"])
