import discord
from bf.yamler import Yamler
from discord.ext import commands
import cogs

tokens = Yamler("data/tokens.yml")the
prefix = tokens.load()["prefix"]
bot = commands.Bot(command_prefix=prefix)

bot.add_cog(cogs.funstuffcog.FunStuff(bot))
bot.add_cog(cogs.utilitiescog.Utilities(bot))
bot.add_cog(cogs.listenercog.Listeners(bot))
bot.add_cog(cogs.sudocog.Sudostuff(bot))
bot.run(tokens.load()["discordtoken"])
