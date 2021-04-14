# ------------------------------------------------------------------------------
#  MIT License
#
#  Copyright (c) 2019-2021 ThatRedKite
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
#  documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
#  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
#  and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all copies or substantial portions of
#  the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
#  THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
#  TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
# ------------------------------------------------------------------------------


import gc
import os
from datetime import datetime
from pathlib import Path
import aiohttp
import psutil
import discord
from discord.ext import commands
from backend.util import colors, clear_temp_folder
from backend.settings import BotSettings

intents = discord.Intents.default()
intents.typing = False
intents.members = True
intents.invites = False
intents.presences = False
intents.reactions = False


dirname = Path(os.path.dirname(os.path.realpath(__file__)))
colors = colors()
if not dirname.joinpath("data", "temp").exists():
    print(colors.red + f"    temp directory not found,creating temp directory")
    os.mkdir(dirname.joinpath("data", "temp"))

tempdir = dirname.joinpath("data", "temp")
tom = BotSettings(dirname)
prefix = tom.prefix
discordtoken = tom.token
tenortoken = tom.tenortoken

if tenortoken is None or tenortoken == "":
    print(
        colors.red + colors.bold + colors.underlined + f"*** tenor token not found! Cannot use features that use tenor! ***{colors.clear}")

# clean up some shit
clear_temp_folder(dirname)

enabled_ext = [
    "cogs.funstuffcog",
    "cogs.imagecog",
    "cogs.nsfwcog",
    "cogs.listenercog",
    "cogs.sudocog",
    "cogs.utilitiescog"
]


class ThatKiteBot(commands.Bot):
    def __init__(self, command_prefix, dirname, help_command=None, description=None, **options):
        super().__init__(command_prefix, help_command=help_command, description=description, **options)
        # ---static values---
        self.prefix = command_prefix
        # paths
        self.dirname = dirname
        self.datadir = self.dirname.joinpath("data")
        self.tempdir = self.datadir.joinpath("temp")

        # info
        self.version = "2.7.0.0"
        self.tom = BotSettings(dirname)
        self.starttime = datetime.now()
        self.pid = os.getpid()
        self.process = psutil.Process(os.getpid())

        # ---dynamic values---

        # settings
        self.settings = tom.settings_all
        self.debugmode = False

        # sessions
        self.loop.run_until_complete(self.aiohttp_start())

        # bot status info
        self.cpu_usage = 0
        self.command_invokes_hour = 0
        self.command_invokes_total = 0

    async def aiohttp_start(self):
        self.aiohttp_session = aiohttp.ClientSession()


print("initilizing bot . . .")
bot = ThatKiteBot(prefix, dirname,intents=intents)
for ext in enabled_ext:
    try:
        bot.load_extension(ext)
    except Exception as exc:
        print(f"error loading {ext}")
        raise exc

# cogs
gc.enable()
bot.case_insensitive = True
bot.run(discordtoken)
