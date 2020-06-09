import discord
from bf.yamler import Tomler
from discord.ext import commands
import cogs
import os
import pathlib
empty=dict(discordtoken="", prefix="")
dirname=os.path.dirname(os.path.realpath(__file__))
tom = Tomler(dirname)
prefix=tom.prefix
token = tom.token
class ThatKiteBot(commands.Bot):
    def __init__(self, command_prefix, dirname, help_command=None, description=None, **options):
        super().__init__(command_prefix, help_command=help_command, description=description, **options)
        self.tom = Tomler(dirname)
        self.parsed = tom.parsed
        self.settings = tom.settings
        self.dirname = dirname

bot=ThatKiteBot(prefix, dirname)
bot.add_cog(cogs.funstuffcog.FunStuff(bot, dirname))
bot.add_cog(cogs.utilitiescog.Utilities(bot, dirname))
bot.add_cog(cogs.listenercog.Listeners(bot, dirname))
bot.add_cog(cogs.sudocog.Sudostuff(bot, dirname))
bot.add_cog(cogs.musiccog.Music(bot,dirname))
bot.remove_command("help")
bot.run(token)

