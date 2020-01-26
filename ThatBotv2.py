import discord
import bf
from discord.ext import commands
import cogs

version = "0.3.1"
tokens = bf.yamler.yamlhandle()
bot = commands.Bot(command_prefix=tokens["prefix"])


bot.add_cog(cogs.funstuffcog.FunStuff(bot))
bot.add_cog(cogs.utilitiescog.Utilities(bot))
bot.add_cog(cogs.listenercog.Listeners(bot))
bot.add_cog(cogs.sudocog.Sudostuff(bot))


bot.run(tokens["discordtoken"])
