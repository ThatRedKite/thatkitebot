import discord
import bottyfuncs as bf
from discord.ext import commands
import Cogs

version = "0.3.1"
tokens = bf.yamler.yamlhandle()
bot = commands.Bot(command_prefix=tokens["prefix"])


bot.add_cog(Cogs.funstuffcog.FunStuff(bot))
bot.add_cog(Cogs.utilitiescog.Utilities(bot))
bot.add_cog(Cogs.listenercog.Listeners(bot))
bot.add_cog(Cogs.sudocog.Sudostuff(bot))

bot.run(tokens["discordtoken"])
