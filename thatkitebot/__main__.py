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
from discord.ext import commands
from dulwich.repo import Repo
from thatkitebot.types.state import PartiallyCachedState

from .extensions import ENABLED_EXTENSIONS
from .tkb_redis.cache import RedisCacheAsync, RedisCacheSync
#endregion

__name__ = "ThatKiteBot"
__version__ = "4.1"
__author__ = "ThatRedKite and contributors"

tempdir = "/tmp/tkb/"
data_dir = "/app/data"
dir_name = "/app/thatkitebot"
log_dir = "/var/log/thatkitebot"

EXTENSIONS = [extension.split(".")[-1] for extension in ENABLED_EXTENSIONS]

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

#region state class
#endregion


# region bot class
class ThatKiteBot(commands.Bot, ABC):
    
    def _get_state(self, **options: discord.Any) -> PartiallyCachedState:
        return PartiallyCachedState(
            dispatch=self.dispatch,
            handlers=self._handlers,
            hooks=self._hooks,
            http=self.http,
            loop=self.loop,
            cache=self.sync_cache,
            **options,
    )
    
    def __init__(self, command_prefix, dir_name, tt, help_command=None, description=None, **options):
        self.logger = logger
        self._connection = None

        self.logger.info("Redis: Trying to connect")
        try:
            # db 0 is free at the moment as it formerly contained the auth stuff
            self.redis = aioredis.Redis(host="redis", db=1, decode_responses=True)
            self.redis_repost = aioredis.Redis(host="redis", db=2, decode_responses=True)
            self.redis_welcomes = aioredis.Redis(host="redis", db=3, decode_responses=True)
            self.redis_bookmarks = aioredis.Redis(host="redis", db=4, decode_responses=True)
            self.redis_starboard = aioredis.Redis(host="redis", db=5, decode_responses=True)
            self.persistent_cache = aioredis.Redis(host="redis", db=6, decode_responses=False)

            self.redis_cache = aioredis.Redis(host="redis_cache", db=0, decode_responses=False)
            self.redis_queue = aioredis.Redis(host="redis_cache", db=1, decode_responses=True)

            self.r_cache = RedisCacheAsync(self, auto_exec=False)
            self.sync_cache = RedisCacheSync(self, auto_exec=False)

            self.settings_lock = asyncio.Lock()
            self.cache_lock = self.r_cache.lock

            self.logger.info("Redis: Connection successful")

        except aioredis.ConnectionError:
            self.logger.critical("Redis: connection failed. Exiting.")
            exit(1)

        # do all the original init stuff
        super().__init__(command_prefix, help_command=help_command, description=description, **options)

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

        del r

        # settings
        self.debug_mode = int(os.getenv("KITEBOT_DEBUG")) == 1
        self.tenor_token = tt
        self.enable_voice = False  # global override for deactivating voice commands
        
        # sessions
        self.aiohttp_session = None  # give the aiohttp session an initial value
        self.process_pool = None
        self.last_online = 0
        
        # bot status info
        self.cpu_usage = 0

        self.events_hour = 0
        self.events_total = 0

        self.command_invokes_hour = 0
        self.command_invokes_total = 0
        

    async def get_or_fetch_channel(self, channel_id: int) -> GuildChannel | PrivateChannel | discord.Thread:
        if (channel := self.get_channel(channel_id)) is not None:
            return channel
        
        if (channel := await super().fetch_channel(channel_id)) is not None:
            return channel
        
        return None
    

    async def get_or_fetch_message(self, message_id: int, channel_id: int=None) -> discord.Message:
        if (message := self.get_message(message_id)) is not None:
            return message
        
        if channel_id and (channel := await self.get_or_fetch_channel(channel_id)) is not None:
            if (message := await channel.fetch_message(message_id)) is not None:
                return message
        
        return None

    async def fetch_channel(self, channel_id: int, /) -> GuildChannel | PrivateChannel | discord.Thread:
        return await self.get_or_fetch_channel(channel_id)
    
#    async def add_message(self, message: discord.Message):
#        async with self.cache_lock:
#            await self.r_cache.add_message_object(message)

#    async def add_reaction(self, payload: discord.RawReactionActionEvent):
#        async with self.cache_lock:
#            pass
        
#    async def get_message(self, message_id: int, guild_id = None, channel_id=None, author_id=None) -> discord.Message | None:
#        async with self.cache_lock:
#            return await self.r_cache.get_message_object(message_id,guild_id,channel_id, author_id, fetch=True)

#    async def fetch_user(self, user_id: int) -> discord.User:
#        async with self.cache_lock:
#            return await self.r_cache.get_user_object(user_id)
    
#    async def add_user(self, user: discord.User):
#        async with self.cache_lock:
#            await self.r_cache.add_user(user)

    async def mass_delete_raw(self, payload: discord.RawBulkMessageDeleteEvent):
        async with self.cache_lock:
            await self.r_cache.mass_expire_messages(payload.message_ids, payload.guild_id, payload.channel_id)

    async def delete_message_raw(self, payload: discord.RawMessageDeleteEvent):
        async with self.cache_lock:
            await self.r_cache.expire_message_now(payload.message_id, payload.guild_id, payload.channel_id)

#    async def get_user(self, id: int) -> discord.User | None:
#        async with self.cache_lock:
#            return await self.r_cache.get_user_object(id)
#        
#    async def get_guild(self, id: int) -> discord.Guild | None:
#        async with self.cache_lock:
#            return await self.r_cache.get_guild_object(id)
#    
#    async def fetch_guild(self, guild_id: int, /, *, with_counts=True) -> discord.Guild:
#        async with self.cache_lock:
#            return await self.r_cache.get_guild_object(guild_id,with_counts)
        
           
    # let's use this to set up some stuff that requires asyncio stuff to work
    async def start(self, token: str, *, reconnect: bool = True) -> None:
        # set up the aiohttp client
        self.logger.info("Starting aiohttp client…")
        headers = {"User-Agent": f"ThatKiteBot/{__version__}"}
        self.aiohttp_session = aiohttp.ClientSession(headers=headers)

        # try to get and set the last online thingies
        self.last_online = int(await self.redis.get("last") or 0)
        if self.last_online > 0:
            self.logger.info(f"{__name__} was last online at {datetime.fromtimestamp(float(self.last_online))} UTC")

        await self.redis.set("last", int(datetime.now().timestamp()))
        # load the cogs aka extensions
        self.load_extensions(*ENABLED_EXTENSIONS, store=False)
        self.logger.info(f"Loaded {len(ENABLED_EXTENSIONS)} extensions: [{','.join(EXTENSIONS)}]")

        self.logger.info("Logging into Discord…")
        await self.login(token)

        self.logger.info("Trying to connect to Discord…")
        await self.connect(reconnect=reconnect)
    

#endregion


#region init

bot = ThatKiteBot(prefix, dir_name, tt=tenor_token, intents=intents, max_messages=None)
logger.info(f"Starting {__name__} version {__version__} ({bot.git_hash})")


# try to start the bot with the token from the init_settings.json file and catch any login errors
try:
    bot.run(discord_token)

except discord.LoginFailure:
    logger.critical("Login failed. Check your token. If you don't have a token, get one from https://discordapp.com/developers/applications/me")
    exit(1)

#endregion
