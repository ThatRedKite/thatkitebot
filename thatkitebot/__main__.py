#  Copyright (c) 2019-2023 ThatRedKite and contributors

import os
import logging
import json
from abc import ABC
from datetime import datetime
from pathlib import Path

import aiohttp
from redis import asyncio as aioredis
import psutil
import discord
import wavelink

from discord.ext import bridge
from dulwich.repo import Repo

from .extensions import ENABLED_EXTENSIONS

__name__ = "ThatKiteBot"
__version__ = "4.0"
__author__ = "ThatRedKite and contributors"

tempdir = "/tmp/tkb/"
data_dir = "/app/data"
dir_name = "/app/thatkitebot"

# this is a pretty dumb way of doing things, but it works
intents = discord.Intents.all()

logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename="/app/data/discord.log", encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
logger.addHandler(handler)

# check if the init_settings.json file exists and if not, create it
if not Path(os.path.join(data_dir, "init_settings.json")).exists():
    print("No init_settings.json file found. Creating one now.")
    settings_dict_empty = {
        "discord token": "",
        "tenor api key": "",
        "prefix": "+",
        "wavelink_pw": "",
    }
    # write the dict as json to the init_settings.json file with the json library
    with open(os.path.join(data_dir, "init_settings.json"), "w") as f:
        # dump the dict as json to the file with an indent of 4 and support for utf-8
        json.dump(settings_dict_empty, f, indent=4, ensure_ascii=False)
    # make the user 1000 the owner of the file, so they can edit it
    os.chown(os.path.join(data_dir, "init_settings.json"), 1000, 1000)

    # exit the program
    exit(1)

# load the init_settings.json file with the json library
with open(os.path.join(data_dir, "init_settings.json"), "r") as f:
    try:
        settings_dict = json.load(f)
        # get the discord token, the tenor api key, and the prefix from the dict
        discord_token = settings_dict["discord token"]
        tenor_token = settings_dict["tenor api key"]
        prefix = settings_dict["prefix"]
        wavelink_pw = settings_dict["wavelink_pw"]

    except json.decoder.JSONDecodeError:
        print("init_settings.json is not valid json. Please fix it.")
        exit(1)


# define the bot class
class ThatKiteBot(bridge.Bot, ABC):
    def __init__(self, command_prefix, dir_name, tt, help_command=None, description=None, **options):
        super().__init__(command_prefix, help_command=help_command, description=description, **options)
        # ---static values---
        self.prefix = command_prefix
        # paths
        self.dir_name = dir_name
        self.data_dir = "/app/data/"
        self.temp_dir = "/tmp/"

        # info
        self.version = __version__
        self.start_time = datetime.now()
        self.pid = os.getpid()
        self.process = psutil.Process(os.getpid())
        r = Repo('.')
        self.git_hash = r.head().decode("utf-8")
        r.close()
        print(f"Running on commit: {self.git_hash}")

        # ---dynamic values---

        # settings
        self.debug_mode = False
        self.tenor_token = tt
        self.enable_voice = False  # global override for deactivating voice commands
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
            self.redis_bookmarks = aioredis.Redis(host="redis", db=4, decode_responses=True)

            self.redis_cache = aioredis.Redis(host="redis_cache", db=0)
            self.redis_queue = aioredis.Redis(host="redis_cache", db=1, decode_responses=True)
            print("Connection successful.")
        except aioredis.ConnectionError:
            print("Redis connection failed. Check if redis is running.")
            exit(1)
        # bot status info
        self.cpu_usage = 0

        self.events_hour = 0
        self.events_total = 0

        self.command_invokes_hour = 0
        self.command_invokes_total = 0

    async def aiohttp_start(self):
        self.aiohttp_session = aiohttp.ClientSession()


# create the bot instance
print(f"Starting ThatKiteBot v {__version__} ...")
bot = ThatKiteBot(prefix, dir_name, tt=tenor_token, intents=intents)
print(f"Loading {len(ENABLED_EXTENSIONS)} extensions:")
for extension in ENABLED_EXTENSIONS:
    print(extension.split(".")[-1])


#@bot.event
#async def on_ready():
#    print("Connecting to lavalink ...\n")
#    try:
#        await wavelink.NodePool.create_node(
#            bot=bot,
#            host="lavalink",
#            port=2333,
#            password=wavelink_pw
#        )
#        print("Sucessfully connected to lavalink!")
#        bot.enable_voice = True
#    except:
#        print("Could not connect to lavalink, voice functionality will be disabled. Please check your settings!\n")


# load the cogs aka extensions

bot.load_extensions(*ENABLED_EXTENSIONS, store=False)

# try to start the bot with the token from the init_settings.json file catch any login errors
try:
    bot.run(discord_token)
except discord.LoginFailure:
    print("Login failed. Check your token. If you don't have a token, get one from https://discordapp.com/developers/applications/me")
    exit(1)
