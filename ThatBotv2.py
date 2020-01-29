import discord
import bf
from discord.ext import commands
import cogs

version = "0.3.2"
tokens = bf.yamler.Yamler("data/tokens.yml")
prefix = tokens.load()["prefix"]
bot = commands.Bot(command_prefix=prefix)


bot.add_cog(cogs.funstuffcog.FunStuff(bot))
bot.add_cog(cogs.utilitiescog.Utilities(bot))
bot.add_cog(cogs.listenercog.Listeners(bot))
bot.add_cog(cogs.sudocog.Sudostuff(bot))

cmdlist = ""
for command in bot.commands:
    commmand.
    cmdlist += "{0}{1}\n".format(prefix,command)
    
print("``` \n{} ```".format(cmdlist))

bot.run(tokens.load()["discordtoken"])
