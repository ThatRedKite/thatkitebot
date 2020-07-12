import discord
from bf.yamler import Tomler
from discord.ext import commands
from bf.util import colors
import cogs
import os
import sys
import psutil
import glob
from pathlib import Path
colors=colors()

print (colors.red+
"""
████████ ██   ██  █████  ████████ ██   ██ ██ ████████ ███████ ██████   ██████  ████████ 
   ██    ██   ██ ██   ██    ██    ██  ██  ██    ██    ██      ██   ██ ██    ██    ██    
   ██    ███████ ███████    ██    █████   ██    ██    █████   ██████  ██    ██    ██    
   ██    ██   ██ ██   ██    ██    ██  ██  ██    ██    ██      ██   ██ ██    ██    ██    
   ██    ██   ██ ██   ██    ██    ██   ██ ██    ██    ███████ ██████   ██████     ██                                                                                                                                                                      
""" +colors.clear)
dirname=Path(os.path.dirname(os.path.realpath(__file__)))
print(f"setting working directory to {colors.blue} '{dirname} {colors.clear}")
print(f"checking data folder: {colors.clear}")

if dirname.joinpath("data","temp").exists():
    print("    temp directory found")
else:
    print(colors.red+f"    temp directory not found, creating temp directory{colors.clear}")
    os.mkdir(dirname.joinpath("data","temp"))

if dirname.joinpath("data","settings.json").exists():
    print("    config file found")
else:
    print(colors.red+f"    ***CRITICAL*** CONFIG FILE NOT FOUND IN {colors.blue}{dirname.joinpath('data','settings.json')}{colors.red} ,EXITING")
    quit()

tempdir=dirname.joinpath("data","temp")
print(f"config successfully loaded")
tom = Tomler(dirname)
prefix=tom.prefix
print(f"setting prefix to {colors.blue} '{prefix}'")
discordtoken = tom.token
tenortoken = tom.tenortoken
if tenortoken is None or tenortoken == "":
    print(colors.red+colors.bold+colors.underlined+f"*** tenor token not found! Cannot use features that use tenor! ***{colors.clear}")



# clean up some shit
cleanupfiles=glob.glob(os.path.join(dirname,"data","temp","*.png"))
cleanupfiles += glob.glob(os.path.join(dirname,"data","temp","*.webp"))
cleanupfiles += glob.glob(os.path.join(dirname,"data","temp","*.gif"))
cleanupfiles += glob.glob(os.path.join(dirname,"data","temp","*.mp3"))

print(f"cleaning data directory, removing{colors.blue} {len(cleanupfiles)} files{colors.clear}")
for file in cleanupfiles:
    os.remove(file)
class ThatKiteBot(commands.Bot):
    def __init__(self, command_prefix, dirname,tempdir, help_command=None, description=None, **options):
        super().__init__(command_prefix, help_command=help_command, description=description, **options)
        self.tom = Tomler(dirname)
        self.parsed = tom.parsed
        self.settings = tom.settings_all
        self.version = "b16"
        self.dirname = dirname
        self.tempdir=self.dirname.joinpath("data","temp")
        self.pid=os.getpid()
        self.file = os.path.realpath(__file__)
        self.exe = os.path.realpath(sys.executable)
        self.process = psutil.Process(self.pid)

print(f"initilizing bot:{colors.clear}")        
bot=ThatKiteBot(prefix,dirname,tempdir)
bot.remove_command("help")
"""
bot.add_cog(cogs.funstuffcog.fun_stuff(bot, dirname))
bot.add_cog(cogs.utilitiescog.utility_commands(bot, dirname))
bot.add_cog(cogs.listenercog.listeners(bot, dirname))
bot.add_cog(cogs.sudocog.sudo_commands(bot, dirname))
bot.add_cog(cogs.musiccog.music(bot,dirname))
bot.add_cog(cogs.imagecog.image_stuff(bot))
bot.add_cog(cogs.nsfwcog.NSFW(bot))
"""
@bot.command()
async def help(ctx):
    await ctx.send("this bot has no features")
    
for cog in bot.cogs:
    print(colors.red+f"    added cog {colors.blue}'{cog}'{colors.clear}")

@bot.event
async def on_ready():
    print(f"\n\nbot successfully started!")  
    print(f"running on shard {bot.shard_id}/{bot.shard_count}")
    print("\nhave fun!"+colors.clear)
bot.run(discordtoken)
