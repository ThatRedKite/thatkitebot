#  Copyright (c) 2019-2022 ThatRedKite and contributors

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

intents = discord.Intents.all()

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
    "thatkitebot.cogs.laser",
    "thatkitebot.cogs.welcomecog",
    "thatkitebot.cogs.repost"
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
        self.version = "3.5"
        self.starttime = datetime.now()
        self.pid = os.getpid()
        self.process = psutil.Process(os.getpid())

        # ---dynamic values---

        # settings
        self.debugmode = True
        self.tenortoken = tt
        # sessions
        self.loop.run_until_complete(self.aiohttp_start())
        # redis databases:
        # 0: initial settings, not accessed while the bot is running
        # 1: guild settings
        # 2: reposts
        self.redis = aioredis.Redis(host="redis", db=1, decode_responses=True)
        self.redis_repost = aioredis.Redis(host="redis", db=2, decode_responses=True)
        self.redis_welcomes = aioredis.Redis(host="redis", db=3, decode_responses=True)
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
