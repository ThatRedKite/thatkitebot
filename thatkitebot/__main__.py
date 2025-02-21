#region license
"""
MIT License

Copyright (c) 2019-present The Kitebot Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
#endregion

#region imports
import os
import logging
import json
import sys
import asyncio
from discord.abc import GuildChannel, PrivateChannel
from abc import ABC
from datetime import datetime
from pathlib import Path

import aiohttp
import psutil
import discord

from redis import asyncio as aioredis
from discord.ext import bridge
from dulwich.repo import Repo

from .extensions import ENABLED_EXTENSIONS
from .tkb_redis.cache import RedisCache
#endregion

__name__ = "ThatKiteBot"
__version__ = "4.0.5"
__author__ = "ThatRedKite and contributors"

tempdir = "/tmp/tkb/"
data_dir = "/app/data"
dir_name = "/app/thatkitebot"
log_dir = "/var/log/thatkitebot"


# this is a pretty dumb way of doing things, but it works
intents = discord.Intents.all()

# set up logging

#region Logging
logger = logging.getLogger("global")
discord_logger = logging.getLogger("discord")

if int(os.getenv("KITEBOT_DEBUG")) == 1:
    logger.setLevel(logging.DEBUG)
else:    
    logger.setLevel(logging.INFO)

if int(os.getenv("DISCORD_DEBUG")) == 1:
    discord_logger.setLevel(logging.DEBUG)
else:    
    discord_logger.setLevel(logging.INFO)

discord_handler = logging.FileHandler(filename="/app/data/discord.log", encoding="utf-8", mode="w")
global_handler = logging.StreamHandler(sys.stdout)

discord_handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
global_handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))

discord_logger.addHandler(discord_handler)
logger.addHandler(global_handler)
#endregion

# region settings
# check if the init_settings.json file exists and if not, create it
if not Path(os.path.join(data_dir, "init_settings.json")).exists():
    print("No init_settings.json file found. Creating one now.")
    settings_dict_empty = {
        "discord token": "",
        "tenor api key": "",
        "prefix": "+",
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

    except json.decoder.JSONDecodeError:
        print("init_settings.json is not valid json. Please fix it.")
        exit(1)

#endregion

# define the bot class
# region bot class
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

        # ---dynamic values---

        # settings
        self.debug_mode = int(os.getenv("KITEBOT_DEBUG")) == 1
        self.tenor_token = tt
        self.enable_voice = False  # global override for deactivating voice commands
        # sessions
        self.aiohttp_session = None  # give the aiohttp session an initial value
        self.logger = logger
        self.process_pool = None
        self.last_online = 0
        
        # redis databases:


        # 0: initial settings, not accessed while the bot is running
        # 1: guild settings
        # 2: reposts
        # 3: welcome leaderboards
        # 4: bookmarks
        # 5: starboard

        self.logger.info("Redis: Trying to connect")
        try:
            self.redis = aioredis.Redis(host="redis", db=1, decode_responses=True)
            self.redis_repost = aioredis.Redis(host="redis", db=2, decode_responses=True)
            self.redis_welcomes = aioredis.Redis(host="redis", db=3, decode_responses=True)
            self.redis_bookmarks = aioredis.Redis(host="redis", db=4, decode_responses=True)
            self.redis_starboard = aioredis.Redis(host="redis", db=5, decode_responses=True)

            self.redis_cache = aioredis.Redis(host="redis_cache", db=0, decode_responses=False)
            self.redis_queue = aioredis.Redis(host="redis_cache", db=1, decode_responses=True)
            self.r_cache = RedisCache(self.redis_cache, self, auto_exec=False)

            self.logger.info("Redis: Connection successful")

        except aioredis.ConnectionError:
            self.logger.critical("Redis: connection failed")
            exit(1)

        
        # bot status info
        self.cpu_usage = 0

        self.events_hour = 0
        self.events_total = 0

        self.command_invokes_hour = 0
        self.command_invokes_total = 0
        
    # let's use this to set up some stuff that requires asyncio stuff to work
    async def start(self, token: str, *, reconnect: bool = True) -> None:
        # set up the aiohttp client
        self.logger.info("Starting aiohttp client…")
        self.aiohttp_session = aiohttp.ClientSession()

        # try to get and set the last online thingies
        self.last_online = int(await self.redis.get("last") or 0)
        if self.last_online > 0:
            self.logger.info(f"{__name__} was last online at {datetime.fromtimestamp(float(self.last_online))} UTC")

        await self.redis.set("last", int(datetime.now().timestamp()))

        self.logger.info("Trying to connect to discord…")
        
        # call the "real" start method to actually start the bot
        return await super().start(token, reconnect=reconnect)
    
    # TODO
    async def fetch_channel(self, channel_id: int) -> GuildChannel | PrivateChannel | discord.Thread:
        return await super().fetch_channel(channel_id)

#endregion
# create the bot instance

#region init
bot = ThatKiteBot(prefix, dir_name, tt=tenor_token, intents=intents)
logger.info(f"Starting {__name__} version {__version__} ({bot.git_hash})")

# load the cogs aka extensions
bot.load_extensions(*ENABLED_EXTENSIONS, store=False)

extensions = [extension.split(".")[-1] for extension in ENABLED_EXTENSIONS]

logger.info(f"Loaded {len(ENABLED_EXTENSIONS)} extensions: [{','.join(extensions)}]")

loop = asyncio.new_event_loop()
# try to start the bot with the token from the init_settings.json file catch any login errors
try:
    loop.create_task(bot.start(discord_token))
    loop.run_forever()
except discord.LoginFailure:
    logger.critical("Login failed. Check your token. If you don't have a token, get one from https://discordapp.com/developers/applications/me")
    exit(1)
#endregion
