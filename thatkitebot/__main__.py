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


import os
from abc import ABC

import redis
from datetime import datetime
from pathlib import Path
import aiohttp
import psutil
import discord
from discord.ext import commands
import aioredis

import thatkitebot.tkb_first_setup

tempdir = "/tmp/tkb/"
datadir = "/app/data"

intents = discord.Intents.default()
intents.typing = True
intents.members = True
intents.invites = False
intents.presences = True
intents.reactions = True

dirname = Path(os.path.dirname(os.path.realpath(__file__)))

with redis.Redis(host="redis", db=0, charset="utf-8", decode_responses=True) as tr:
    print("Loading tokens from redis")
    tokens = tr.mget(["DISCORDTOKEN", "TENORTOKEN", "PREFIX"])
    if None in tokens:
        print("Trying to initialize tokens from settings.json ...")
        thatkitebot.tkb_first_setup.initial()
        tokens = tr.mget(["DISCORDTOKEN", "TENORTOKEN", "PREFIX"])
    discord_token, tenor_token, prefix = tokens

enabled_ext = [
    "thatkitebot.cogs.funstuffcog",
    "thatkitebot.cogs.imagecog",
    "thatkitebot.cogs.nsfwcog",
    "thatkitebot.cogs.listenercog",
    "thatkitebot.cogs.sudocog",
    "thatkitebot.cogs.utilitiescog",
    "thatkitebot.cogs.settings",
    "thatkitebot.cogs.help",
    "thatkitebot.cogs.chemistry",
    "thatkitebot.cogs.electronics",
    "thatkitebot.cogs.electroslash",
    "thatkitebot.cogs.laser"
]


class ThatKiteBot(commands.Bot, ABC):
    def __init__(self, command_prefix, dirname, tt, help_command=None, description=None, **options):
        super().__init__(command_prefix, help_command=help_command, description=description, **options)
        # ---static values---
        self.prefix = command_prefix
        # paths
        self.dirname = dirname
        self.datadir = "/app/data/"
        self.tempdir = "/tmp/"

        # info
        self.version = "3.3"
        self.starttime = datetime.now()
        self.pid = os.getpid()
        self.process = psutil.Process(os.getpid())

        # ---dynamic values---

        # settings
        self.debugmode = False
        self.tenortoken = tt
        # sessions
        self.loop.run_until_complete(self.aiohttp_start())
        self.redis = aioredis.Redis(host="redis", db=1, decode_responses=True)
        self.redis_cache = aioredis.Redis(host="redis_cache", db=0, decode_responses=True)

        # bot status info
        self.cpu_usage = 0
        self.command_invokes_hour = 0
        self.command_invokes_total = 0

    async def aiohttp_start(self):
        self.aiohttp_session = aiohttp.ClientSession()


bot = ThatKiteBot(prefix, dirname, tt=tenor_token, intents=intents)
print(f"Loading extensions: \n")
for ext in enabled_ext:
    try:
        print(f"   loading {ext}")
        bot.load_extension(ext)
    except Exception as exc:
        print(f"error loading {ext}")
        raise exc

# cogs
try:
    bot.run(discord_token)

except discord.errors.LoginFailure:
    with redis.Redis(host="redis", db=0, charset="utf-8", decode_responses=True) as tr:
        tr.delete("DISCORDTOKEN")
        print("Improper token in your settings. Please re-enter your token in init_settings.yml!")
