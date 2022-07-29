#  Copyright (c) 2019-2022 ThatRedKite and contributors

import os
from abc import ABC
from datetime import datetime
from pathlib import Path

import aiohttp
import psutil
import discord
import aioredis
import json
from discord.ext import commands, bridge

__name__ = "ThatKiteBot"
__version__ = "3.9"
__author__ = "ThatRedKite and contributors"

enabled_ext = [
    "thatkitebot.cogs.funstuffcog",
    "thatkitebot.cogs.imagecog",
    "thatkitebot.cogs.nsfwcog",
    "thatkitebot.cogs.listenercog",
    "thatkitebot.cogs.uwucog",
    "thatkitebot.cogs.sudocog",
    "thatkitebot.cogs.utilitiescog",
    "thatkitebot.cogs.settings",
    "thatkitebot.cogs.help",
    "thatkitebot.cogs.chemistry",
    "thatkitebot.cogs.electronics",
    "thatkitebot.cogs.electroslash",
    "thatkitebot.cogs.laser",
    "thatkitebot.cogs.welcomecog",
    "thatkitebot.cogs.repost",
    "thatkitebot.cogs.starboard",
]

tempdir = "/tmp/tkb/"
datadir = "/app/data"
dirname = "/app/thatkitebot"

# this is a pretty dumb way of doing things, but it works
intents = discord.Intents.all()

# check if the init_settings.json file exists and if not, create it
if not Path(os.path.join(datadir, "init_settings.json")).exists():
    print("No init_settings.json file found. Creating one now.")
    settings_dict_empty = {
        "discord token": "",
        "tenor api key": "",
        "prefix": "+",
    }
    # write the dict as json to the init_settings.json file with the json library
    with open(os.path.join(datadir, "init_settings.json"), "w") as f:
        # dump the dict as json to the file with an indent of 4 and support for utf-8
        json.dump(settings_dict_empty, f, indent=4, ensure_ascii=False)
    # make the user 1000 the owner of the file, so they can edit it
    os.chown(os.path.join(datadir, "init_settings.json"), 1000, 1000)

    # exit the program
    exit(1)

# load the init_settings.json file with the json library
with open(os.path.join(datadir, "init_settings.json"), "r") as f:
    try:
        settings_dict = json.load(f)
        # get the discord token, the tenor api key, and the prefix from the dict
        discord_token = settings_dict["discord token"]
        tenor_token = settings_dict["tenor api key"]
        prefix = settings_dict["prefix"]

    except json.decoder.JSONDecodeError:
        print("init_settings.json is not valid json. Please fix it.")
        exit(1)


# define the bot class
class ThatKiteBot(bridge.Bot, ABC):
    def __init__(self, command_prefix, dirname, tt, help_command=None, description=None, **options):
        super().__init__(command_prefix, help_command=help_command, description=description, **options)
        # ---static values---
        self.prefix = command_prefix
        # paths
        self.dirname = dirname
        self.datadir = "/app/data/"
        self.tempdir = "/tmp/"

        # info
        self.version = __version__
        self.starttime = datetime.now()
        self.pid = os.getpid()
        self.process = psutil.Process(os.getpid())

        # ---dynamic values---

        # settings
        self.debugmode = False
        self.tenortoken = tt
        # sessions
        self.aiohttp_session = None  # give the aiohttp session an initial value
        self.loop.run_until_complete(self.aiohttp_start())

        # redis databases:

        # 0: initial settings, not accessed while the bot is running
        # 1: guild settings
        # 2: reposts
        # 3: welcome leaderboards

        print("Connecting to redis...")
        try:
            self.redis = aioredis.Redis(host="redis", db=1, decode_responses=True)
            self.redis_repost = aioredis.Redis(host="redis", db=2, decode_responses=True)
            self.redis_welcomes = aioredis.Redis(host="redis", db=3, decode_responses=True)
            self.redis_cache = aioredis.Redis(host="redis_cache", db=0, decode_responses=True)
            print("Connection successful.")
        except aioredis.ConnectionError:
            print("Redis connection failed. Check if redis is running.")
            exit(1)
        # bot status info
        self.cpu_usage = 0
        self.command_invokes_hour = 0
        self.command_invokes_total = 0

    async def aiohttp_start(self):
        self.aiohttp_session = aiohttp.ClientSession()


# create the bot instance
print(f"Starting ThatKiteBot v {__version__} ...")
bot = ThatKiteBot(prefix, dirname, tt=tenor_token, intents=intents)
print(f"Loading {len(enabled_ext)} extensions: \n")

# load the cogs aka extensions
for ext in enabled_ext:
    try:
        print(f"   loading {ext}")
        bot.load_extension(ext)
    except Exception as exc:
        print(f"error loading {ext}")
        raise exc

# try to start the bot with the token from the init_settings.json file catch any login errors
try:
    bot.run(discord_token)
except discord.LoginFailure:
    print("Login failed. Check your token. If you don't have a token, get one from https://discordapp.com/developers/applications/me")
    exit(1)


