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
        self.settings = tom.settings_all
        self.dirname = dirname
        self.version = "b11"

bot=ThatKiteBot(prefix, dirname)
bot.remove_command("help")
bot.add_cog(cogs.funstuffcog.fun_stuff(bot, dirname))
bot.add_cog(cogs.utilitiescog.utility_commands(bot, dirname))
bot.add_cog(cogs.listenercog.Listeners(bot, dirname))
bot.add_cog(cogs.sudocog.sudo_commands(bot, dirname))
bot.add_cog(cogs.musiccog.music(bot,dirname))
bot.add_cog(cogs.imagecog.image_stuff(bot))
bot.add_cog(cogs.nsfwcog.NSFW(bot))
bot.run(token)

