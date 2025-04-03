#region License
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
import asyncio
from collections.abc import MutableMapping
from datetime import timedelta
from typing import Optional, Union
from threading import Lock

import discord.state
import discord
from discord import MessageType
from redis import asyncio as aioredis
import redis as syncredis

from thatkitebot.base.channels import get_channel

from .exceptions import *
from .util import compress_data, decompress_data
from .serialization import channel_to_dict, guild_to_dict, user_to_dict, message_to_dict
#endregion

class LUT_Keys(discord.Enum):
    AUTHOR = "id_to_author"
    CHANNEL = "id_to_channel"
    GUILD = "id_to_guild"
    CHANNEL_TO_GUILD = "channel_to_guild"


#region async class
class RedisCacheAsync:
    def __init__(self,bot: discord.Bot,auto_exec=False):
        
        self.bot = bot
        self.auto_exec = auto_exec

        self.autoexpire: timedelta = timedelta(weeks=2)
        
        self.lut            =   aioredis.Redis(host="redis", db=15, decode_responses=False)
        self.guild_cache    =   aioredis.Redis(host="redis_cache", db=1, decode_responses=False)
        self.channel_cache  =   aioredis.Redis(host="redis_cache", db=2, decode_responses=False)
        self.user_cache     =   aioredis.Redis(host="redis_cache", db=3, decode_responses=False)
        self.message_cache  =   aioredis.Redis(host="redis_cache", db=4, decode_responses=False)

        self.id_pipeline        =   self.lut.pipeline(transaction=True)
        self.message_pipeline   =   self.message_cache.pipeline(transaction=False)
        self.channel_pipeline   =   self.channel_cache.pipeline(transaction=True)
        self.guild_pipeline     =   self.guild_cache.pipeline(transaction=True)
        self.user_pipeline      =   self.user_cache.pipeline(transaction=True)

        self.lock = asyncio.Lock()


    @property
    def _pipelines(self):
        return [self.id_pipeline, self.message_pipeline, self.channel_pipeline, self.guild_pipeline, self.user_pipeline]
    
    @property
    def _connections(self):
        return [self.lut, self.guild_cache, self.channel_cache, self.guild_cache, self.user_cache]
    

    def _clear_all_pipelines(self):
        for pipeline in self._pipelines:
            pipeline.command_stack.clear()

    async def exec(self):
        for pipeline in self._pipelines:
            await pipeline.execute()

    async def compressed_write_hash(self, pipeline, name: str, key: str, dict_data:dict):
        return await pipeline.hset(name, key, compress_data(dict_data))
    
    async def compressed_read_hash(self, redis: aioredis.Redis, name: str, key: str) -> dict:
        if data_compressed := await redis.hget(name, key):
            return decompress_data(data_compressed)
    
    async def compressed_write_key(self, pipeline, key: str, dict_data:dict):
        return await pipeline.set(key, compress_data(dict_data))
    
    async def compressed_read_key(self, redis: aioredis.Redis, key: str) -> dict:
        if data_compressed := await redis.get(key):
            return decompress_data(data_compressed)
    
    async def add_user(self, user: discord.User):
        await self.compressed_write_key(self.user_cache, str(user.id), user_to_dict(user))
        
    async def clear_users(self):
        await self.user_cache.delete("users")

    async def get_user_object(self, user_id: int):
        # exectue the write pipeline to commit any pending changes before reading 
        # User Pipeline
        await self.user_pipeline.execute()

        if data := await self.compressed_read_key(self.user_cache, str(user_id)):
            # reconstruct the color thingy
            return self.state.create_user(data)
        else:
            # on cache miss, get the user from the API and add it to the cache
            new_user = self.state.create_user(await self.state.http.get_user(user_id))
            # add user to the cache
            await self.add_user(new_user)
            return new_user

    async def get_user_dict(self, user_id: int):
        # exectue the write pipeline to commit any pending changes before reading 
        # User Pipeline 
        await self.user_pipeline.execute()

        if data := await self.compressed_read_key(self.channel_cache, str(user_id)):
            return data
        else:
            data = await self.state.http.get_user(user_id)
            await self.compressed_write_key(self.channel_cache, str(user_id), data)
            return data

    async def update_message_raw(self, payload: discord.RawMessageUpdateEvent):
        await self.add_message_dict(payload.data)

    async def add_message_object(self, message: discord.Message):
        await self.add_message_dict(message_to_dict(message))

    async def add_message_dict(self, message_data: dict):
        message_id = message_data.get("id")
        author_id = message_data.get("author").get("id")
        guild_id = message_data.get("guild_id", 0)
        channel_id = message_data.get("channel_id", 0)

        assert None not in (message_id, guild_id, channel_id, author_id)

        entry_name = f"{guild_id}:{author_id}:{channel_id}:{message_id}"
        await self.compressed_write_key(self.message_pipeline, entry_name, message_data)
        await self.message_pipeline.expire(entry_name, self.autoexpire)
                                           
        await self.id_pipeline.hset(LUT_Keys.AUTHOR.value, mapping={str(message_id): str(author_id)})
        await self.id_pipeline.hset(LUT_Keys.CHANNEL.value, mapping={str(message_id): str(channel_id)})
        await self.id_pipeline.hset(LUT_Keys.GUILD.value, mapping={str(message_id): str(guild_id)})
        await self.id_pipeline.hset(LUT_Keys.CHANNEL_TO_GUILD.value, mapping={str(channel_id): str(guild_id)})

    async def get_author_id(self, message_id: Union[int, str]):
        # exectue the write pipeline to commit any pending changes before reading
        # ID pipeline
        await self.id_pipeline.execute()

        raw = await self.lut.hget(LUT_Keys.AUTHOR.value, str(message_id))
        if raw is not None:
            return int(raw.decode("ASCII"))
        else:
            return None

    async def _get_ids(self, message_id, guild_id, channel_id, author_id) -> tuple[int]:
        if not guild_id:
            guild_id = await self.get_guild_id(message_id)

        if not author_id:
            author_id = await self.get_author_id(message_id)

        if not channel_id:
            channel_id = await self.get_channel_id(message_id)

        return (guild_id, author_id, channel_id)

    async def get_channel_id(self, message_id: Union[int, str]):
        # exectue the write pipeline to commit any pending changes before reading
        # ID pipeline
        await self.id_pipeline.execute()

        raw = await self.lut.hget(LUT_Keys.CHANNEL.value, str(message_id))
        if raw is not None:
            return int(raw.decode("ASCII"))
        else:
            return None

    async def get_guild_id(self, message_id: Union[int, str]):
        # exectue the write pipeline to commit any pending changes before reading 
        # uses ID pipeline
        await self.id_pipeline.execute()

        raw = await self.lut.hget(LUT_Keys.GUILD.value, str(message_id))
        if raw is not None:
            return int(raw.decode("ASCII"))
        else:
            return None

    async def get_guild_id_from_channel_id(self, channel_id):
        # exectue the write pipeline to commit any pending changes before reading 
        # uses ID pipeline

        await self.id_pipeline.execute()
        raw = await self.lut.hget(LUT_Keys.CHANNEL_TO_GUILD.value, str(channel_id))
        if raw is not None:
            return int(raw.decode("ASCII"))
        else:
            return None

    async def channel_history_iter(self, channel_id, user_id: Optional[int] = None, guild_id: Optional[int] = None, limit=30):
        
        # exectue the write pipeline to commit any pending changes before reading 
        # ID pipeline, Message pipeline, Channel Pipeline, User Pipeline

        await self.id_pipeline.execute()
        await self.message_pipeline.execute()
        await self.channel_pipeline.execute()
        await self.user_pipeline.execute()

        if not guild_id:
            guild_id = await self.get_guild_id_from_channel_id(channel_id)
                
        if user_id:
            scan_pattern = f"{guild_id}:{user_id}:{channel_id}:*"
        else:
            scan_pattern = f"{guild_id}:*:{channel_id}:*"

        counter = 0
        channel = await self.get_channel_object(channel_id)
        async for key, raw_data in self.message_cache.scan_iter(str(guild_id), scan_pattern):
            if counter < limit:
                message_data = decompress_data(raw_data)
                ids: str = key.decode("ASCII")
                ids = ids.split(":")
                author = await self.get_user_dict(ids[0])
                message_data.update({"id": ids[2], "author": author})
                yield discord.Message(state=self.state, data=message_data, channel=channel)

            counter += 1

    async def get_message_dict(self, message_id: int, guild_id: Optional[int]=None, channel_id: Optional[int]=None, author_id: Optional[int]=None, fetch=True) -> Optional[dict]:
        await self.id_pipeline.execute()
        await self.message_pipeline.execute()
        await self.channel_pipeline.execute()
        await self.user_pipeline.execute()

        guild_id, author_id, channel_id = await self._get_ids(message_id, guild_id, channel_id, author_id)
                
        if guild_id and author_id and channel_id and message_id:
            # if we got the message data from the cache, cool
            if (message_data := await self.compressed_read_key(self.message_cache, f"{guild_id}:{author_id}:{channel_id}:{message_id}")) is not None:
                author = await self.get_user_dict(author_id)
                message_data.update({"id": message_id, "author": author})
                return message_data
        
        if message_id and channel_id and fetch:
            # if we didn't, we need to try to get it from the API
            message_data = await self.state.http.get_message(channel_id, message_id)
            # add it to the cache pipeline
            await self.add_message_dict(message_data)
            return message_data

        return None

    async def get_message_object(self, message_id: int, guild_id: Optional[int]=None, channel_id: Optional[int]=None, author_id: Optional[int]=None, fetch=True) -> Optional[discord.Message]:
        # exectue the write pipeline to commit any pending changes before reading 
        # ID pipeline, Message pipeline, Channel Pipeline, User Pipeline
        
        if message_data := await self.get_message_dict(message_id, guild_id, channel_id, author_id, fetch):
            if channel := await self.get_channel_object(channel_id, guild_id, fetch):
                return self.state.create_message(channel=channel, data=message_data)

        return None
    
    async def expire_message_now(self, message_id: int, guild_id: Optional[int]=None, channel_id: Optional[int]=None, author_id: Optional[int]=None):
        guild_id, author_id, channel_id = await self._get_ids(message_id, guild_id, channel_id, author_id)

        if guild_id and author_id and channel_id:
            entry_name = f"{guild_id}:{author_id}:{channel_id}:{message_id}"

            # expire message in 
            await self.message_cache.expire(entry_name, timedelta(seconds=15), lt=True)

            # clean up the LUT
            await self.id_pipeline.hdel(LUT_Keys.AUTHOR.value, str(message_id))
            await self.id_pipeline.hdel(LUT_Keys.CHANNEL.value, str(message_id))
            await self.id_pipeline.hdel(LUT_Keys.GUILD.value, str(message_id))

            await self.message_pipeline.execute()
            await self.id_pipeline.execute()

    async def mass_expire_messages(self, message_ids: list[int], guild_id: int, channel_id: int):
        names = []

        for message_id in message_ids:
            if author_id := await self.get_author_id(message_id):
                names.append(f"{guild_id}:{author_id}:{channel_id}:{message_id}")
                await self.id_pipeline.hdel(LUT_Keys.AUTHOR.value, str(message_id))
                await self.id_pipeline.hdel(LUT_Keys.CHANNEL.value, str(message_id))
                await self.id_pipeline.hdel(LUT_Keys.GUILD.value, str(message_id))

            else:
                continue

        await self.message_pipeline.delete(*names)
        await self.message_pipeline.execute()
        await self.id_pipeline.execute()

    async def add_channel_object(self, channel: discord.abc.GuildChannel):
        channel_data = channel_to_dict(channel)

        # Channel Pipeline & ID Pipeline
        await self.compressed_write_key(self.channel_pipeline, str(channel.id), channel_data)

        # update the look up table
        await self.id_pipeline.hset("channel_to_guild", str(channel.id), channel_data["guild"]["id"])

    async def get_channel_object(self, channel_id: int, guild_id: int, fetch=True):
        # exectue the write pipeline to commit any pending changes before reading 

        # ID Pipeline, Channel Pipeline, Guild Pipeline
        await self.channel_pipeline.execute()
        await self.id_pipeline.execute()
        await self.guild_pipeline.execute()
        
        if channel_data := await self.get_channel_dict(channel_id, fetch):
            if guild := await self.get_guild_object(guild_id, fetch):
                return get_channel(self.bot, channel_data, guild)

        return None

    async def get_channel_dict(self, channel_id: int, fetch=True) -> dict:
        # exectue the write pipeline to commit any pending changes before reading 
        # Channel Pipeline
        await self.channel_pipeline.execute()
        if channel_data := await self.compressed_read_key(self.channel_cache, str(channel_id)):
            return channel_data
        
        if fetch:
            # add it to the cache
            channel_data = await self.state.http.get_channel(channel_id)
            # add it to the cache
            await self.compressed_write_key(self.channel_pipeline, str(channel_id), channel_data)
            await self.id_pipeline.hset("channel_to_guild", str(channel_id), str(channel_data.get("guild_id", 0)))
            return channel_data

    async def add_guild_by_id(self, guild_id: int, sync_channels=False) -> discord.Guild:
        # get the guild data from the API
        guild_data = await self.state.http.get_guild(guild_id)

        # Guild Pipeline
        await self.guild_pipeline.execute()
        await self.compressed_write_key(self.guild_pipeline, str(guild_id), guild_data)

        # return the guild object for good measure as well
        return discord.Guild(data=guild_data, state=self.state)
    
    async def add_guild_object(self, guild: discord.Guild, sync_channels=False, sync_members=False):

        # Guild Pipeline
        await self.compressed_write_key(self.guild_pipeline, str(guild.id), guild_to_dict(guild))
        
        if sync_channels:
            for channel in guild.channels:
                await self.add_channel_object(channel)
                
        if sync_members:
            for member in guild.members:
                await self.add_user(member._user)

    async def get_guild_dict(self, guild_id: int, with_counts=False, fetch=True) -> dict:
        # exectue the write pipeline to commit any pending changes before reading 
        # Guild Pipeline
        await self.guild_pipeline.execute()

        if data := await self.compressed_read_key(self.guild_cache, str(guild_id)):
            return data
        
        if fetch:
            try:
                guild_data = await self.state.http.get_guild(guild_id, with_counts=with_counts)
                await self.compressed_write_key(self.guild_cache, str(guild_id), guild_data)
                return guild_data
                
            except:
                return None
            
        return None

    async def get_guild_object(self, guild_id: int, with_counts=False, fetch=True):
        guild_data = await self.get_guild_dict(guild_id, with_counts, fetch)
        return discord.Guild(data=guild_data,state=self.state)
    
    async def add_reaction(self, payload: discord.RawReactionActionEvent):
        # get cached message from the cache
        if cached_message := await self.get_message_dict(payload.message_id, payload.guild_id, payload.channel_id):
            old_reactions = cached_message.get("reactions", [])
        
    def get_pipeline_stats(self):
        return dict(
            id_pipeline=len(self.id_pipeline.command_stack),
            message_pipeline=len(self.message_pipeline.command_stack),
            channel_pipeline=len(self.channel_pipeline.command_stack),
            user_pipeline=len(self.user_pipeline.command_stack),
            guild_pipeline=len(self.guild_pipeline.command_stack),
        )

#endregion

class RedisCacheSyncPartial:
    def __init__(self, bot, auto_exec=False):
        self.bot = bot
        self.auto_exec = auto_exec
        self.autoexpire: timedelta = timedelta(weeks=2)
        
        self.lut            =   syncredis.Redis(host="redis", db=15, decode_responses=False)
        self.message_cache  =   syncredis.Redis(host="redis_cache", db=4, decode_responses=False)

        self.id_pipeline        =   self.lut.pipeline(transaction=True)
        self.message_pipeline   =   self.message_cache.pipeline(transaction=False)

        self.lock = Lock()

    @property
    def _pipelines(self):
        return [self.id_pipeline, self.message_pipeline]

    def exec(self):
        for pipeline in self._pipelines():
            pipeline.execute()

    def update_message(self, data_new: dict) -> None:
        message_id = int(data_new.get("id"))
        author_id = int(data_new.get("author").get("id"))
        guild_id = int(data_new.get("guild_id", 0))
        channel_id = int(data_new.get("channel_id", 0))

        guild_id, author_id, channel_id = self._get_ids(message_id, guild_id, channel_id, author_id)
        name = f"{guild_id}:{author_id}:{channel_id}:{message_id}"

        data_old = self.compressed_read_key(self.message_cache, name)
        data_old.update(data_new)
        self.compressed_write_key(self.message_pipeline, name, data_old)

    def compressed_write_hash(self, pipeline, name: str, key: str, dict_data:dict):
        return pipeline.hset(name, key, compress_data(dict_data))
    
    def compressed_read_hash(self, redis: aioredis.Redis, name: str, key: str) -> dict:
        if data_compressed := redis.hget(name, key):
            return decompress_data(data_compressed)
    
    def compressed_write_key(self, pipeline, key: str, dict_data:dict):
        return pipeline.set(key, compress_data(dict_data))
    
    def compressed_read_key(self, redis: aioredis.Redis, key: str) -> dict:
        if data_compressed := redis.get(key):
            return decompress_data(data_compressed)

        return None

    def expire_message_now(self, message_id: int, guild_id: Optional[int]=None, channel_id: Optional[int]=None, author_id: Optional[int]=None):
        guild_id, author_id, channel_id = self._get_ids(message_id, guild_id, channel_id, author_id)

        if guild_id and author_id and channel_id:
            entry_name = f"{guild_id}:{author_id}:{channel_id}:{message_id}"

            # expire message in 
            self.message_cache.expire(entry_name, timedelta(seconds=15), lt=True)

            # clean up the LUT
            self.id_pipeline.hdel(LUT_Keys.AUTHOR.value, str(message_id))
            self.id_pipeline.hdel(LUT_Keys.CHANNEL.value, str(message_id))
            self.id_pipeline.hdel(LUT_Keys.GUILD.value, str(message_id))

            self.message_pipeline.execute()
            self.id_pipeline.execute()
    
    def _get_ids(self, message_id, guild_id, channel_id, author_id) -> tuple[int]:
        if not guild_id:
            guild_id = self.get_guild_id(message_id)

        if not author_id:
            author_id = self.get_author_id(message_id)

        if not channel_id:
            channel_id = self.get_channel_id(message_id)

        return (guild_id, author_id, channel_id)

    def get_author_id(self, message_id: Union[int, str]):
        # exectue the write pipeline to commit any pending changes before reading
        # ID pipeline
        self.id_pipeline.execute()

        raw = self.lut.hget(LUT_Keys.AUTHOR.value, str(message_id))
        if raw is not None:
            return int(raw.decode("ASCII"))
        else:
            return None

    def get_channel_id(self, message_id: Union[int, str]):
        # exectue the write pipeline to commit any pending changes before reading
        # ID pipeline
        self.id_pipeline.execute()

        raw = self.lut.hget(LUT_Keys.CHANNEL.value, str(message_id))
        if raw is not None:
            return int(raw.decode("ASCII"))
        else:
            return None

    def get_guild_id(self, message_id: Union[int, str]):
        # exectue the write pipeline to commit any pending changes before reading 
        # uses ID pipeline
        self.id_pipeline.execute()

        raw = self.lut.hget(LUT_Keys.GUILD.value, str(message_id))
        if raw is not None:
            return int(raw.decode("ASCII"))
        else:
            return None

    def get_guild_id_from_channel_id(self, channel_id):
        # exectue the write pipeline to commit any pending changes before reading 
        # uses ID pipeline

        self.id_pipeline.execute()
        raw = self.lut.hget(LUT_Keys.CHANNEL_TO_GUILD.value, str(channel_id))
        if raw is not None:
            return int(raw.decode("ASCII"))
        else:
            return None

    def get_message_dict(self, message_id: int, guild_id: Optional[int]=None, channel_id: Optional[int]=None, author_id: Optional[int]=None, fetch=True) -> Optional[dict]:
        self.id_pipeline.execute()
        self.message_pipeline.execute()

        guild_id, author_id, channel_id = self._get_ids(message_id, guild_id, channel_id, author_id)
                
        if guild_id and author_id and channel_id and message_id:
            # if we got the message data from the cache, cool
            if (message_data := self.compressed_read_key(self.message_cache, f"{guild_id}:{author_id}:{channel_id}:{message_id}")) is not None:
                message_data.update({"channel_id": int(channel_id)})
                return message_data

        return None
    
    def add_message_dict(self, message_data: dict):
        if message_data["type"] not in (0, 19, 20, 21, 23):
            return
        
        message_id = int(message_data.get("id"))
        author_id = int(message_data.get("author").get("id"))
        guild_id = int(message_data.get("guild_id", 0))
        channel_id = int(message_data.get("channel_id", 0))

        assert None not in (message_id, guild_id, channel_id, author_id)

        entry_name = f"{guild_id}:{author_id}:{channel_id}:{message_id}"
        
        # fix the missing channel_id in message references
        # if we have a forwarded message, don't even bother trying to get the ids, 
        if (ref_data := message_data.get("message_reference")) is not None:
            ref_data.update({"channel_id":str(self.get_channel_id(ref_data["message_id"])) or str(channel_id)})
            # try to remove referenced message to avoid storing messages twice
            try:
                message_data.pop("referenced_message")
            except KeyError:
                pass

        self.compressed_write_key(self.message_pipeline, entry_name, message_data)
    
        self.message_pipeline.expire(entry_name, self.autoexpire)
                                           
        self.id_pipeline.hset(LUT_Keys.AUTHOR.value, mapping={str(message_id): str(author_id)})
        self.id_pipeline.hset(LUT_Keys.CHANNEL.value, mapping={str(message_id): str(channel_id)})
        self.id_pipeline.hset(LUT_Keys.GUILD.value, mapping={str(message_id): str(guild_id)})
        self.id_pipeline.hset(LUT_Keys.CHANNEL_TO_GUILD.value, mapping={str(channel_id): str(guild_id)})

    def add_message_object(self, message: discord.Message):
        self.add_message_dict(message_to_dict(message))
        del message
    
#region sync class
class RedisCacheSync(RedisCacheSyncPartial):
    def __init__(self, bot, auto_exec=False):
        self.state: discord.state.ConnectionState = bot._connection
        self.bot = bot

        self.auto_exec = auto_exec

        self.autoexpire: timedelta = timedelta(weeks=2)
        
        self.lut            =   syncredis.Redis(host="redis", db=15, decode_responses=False)
        self.guild_cache    =   syncredis.Redis(host="redis_cache", db=1, decode_responses=False)
        self.channel_cache  =   syncredis.Redis(host="redis_cache", db=2, decode_responses=False)
        self.user_cache     =   syncredis.Redis(host="redis_cache", db=3, decode_responses=False)
        self.message_cache  =   syncredis.Redis(host="redis_cache", db=4, decode_responses=False)

        self.id_pipeline        =   self.lut.pipeline(transaction=True)
        self.message_pipeline   =   self.message_cache.pipeline(transaction=False)
        self.channel_pipeline   =   self.channel_cache.pipeline(transaction=True)
        self.guild_pipeline     =   self.guild_cache.pipeline(transaction=True)
        self.user_pipeline      =   self.user_cache.pipeline(transaction=True)

        self.lock = Lock()
    
    @property
    def _pipelines(self):
        return [self.id_pipeline, self.message_pipeline, self.user_pipeline, self.guild_pipeline, self.channel_pipeline]

    def add_user(self, user: discord.User):
        self.compressed_write_key(self.user_cache, str(user.id), user_to_dict(user))       

    def get_user_object(self, user_id: int):
        # exectue the write pipeline to commit any pending changes before reading 
        # User Pipeline
        self.user_pipeline.execute()

        if data := self.compressed_read_key(self.user_cache, str(user_id)):
            # reconstruct the color thingy
            return discord.User(state=self.state, data=data)
        
        return None

    def get_user_dict(self, user_id: int):
        # exectue the write pipeline to commit any pending changes before reading 
        # User Pipeline 
        self.user_pipeline.execute()

        if data := self.compressed_read_key(self.channel_cache, str(user_id)):
            return data
        
        return None

    def add_channel_object(self, channel: discord.abc.GuildChannel):
        channel_data = channel_to_dict(channel)

        # Channel Pipeline & ID Pipeline
        self.compressed_write_key(self.channel_pipeline, str(channel.id), channel_data)

        # update the look up table
        self.id_pipeline.hset(LUT_Keys.CHANNEL_TO_GUILD.value, str(channel.id), channel_data["guild"]["id"])

    def get_channel_object(self, channel_id: int, guild_id: Optional[int]):
        # exectue the write pipeline to commit any pending changes before reading 

        # ID Pipeline, Channel Pipeline, Guild Pipeline

        self.channel_pipeline.execute()
        self.id_pipeline.execute()
        self.guild_pipeline.execute()
        
        if (channel_data := self.get_channel_dict(channel_id)):
            if guild := self.get_guild_object(guild_id):
                return get_channel(self.bot, channel_data, guild)
    
        return None
    
    def get_channel_dict(self, channel_id: int) -> dict:
        # exectue the write pipeline to commit any pending changes before reading 
        # Channel Pipeline
        self.channel_pipeline.execute()

        if channel_data := self.compressed_read_key(self.channel_cache, str(channel_id)):
            return channel_data
        
    def get_guild_dict(self, guild_id: int, with_counts=False) -> dict:
        # exectue the write pipeline to commit any pending changes before reading 
        # Guild Pipeline
        self.guild_pipeline.execute()

        if data := self.compressed_read_key(self.guild_cache, str(guild_id)):
            return data
        
        return None

    def get_guild_object(self, guild_id: int, with_counts=False, fetch=True):
        guild_data = self.get_guild_dict(guild_id)
        return discord.Guild(data=guild_data,state=self.state)
    
    def add_guild_object(self, guild: discord.Guild, sync_channels=False, sync_members=False):

        # Guild Pipeline
        self.compressed_write_key(self.guild_pipeline, str(guild.id), guild_to_dict(guild))
        
        if sync_channels:
            for channel in guild.channels:
                self.add_channel_object(channel)
                
        if sync_members:
            for member in guild.members:
                self.add_user(member._user)

    def get_guild_dict(self, guild_id: int) -> dict:
        # exectue the write pipeline to commit any pending changes before reading 
        # Guild Pipeline
        self.guild_pipeline.execute()

        if data := self.compressed_read_key(self.guild_cache, str(guild_id)):
            return data
        
        return None
    
    def mass_expire_messages(self, message_ids: list[int], guild_id: int, channel_id: int):
        names = []

        for message_id in message_ids:
            if author_id := self.get_author_id(message_id):
                names.append(f"{guild_id}:{author_id}:{channel_id}:{message_id}")
                self.id_pipeline.hdel(LUT_Keys.AUTHOR.value, str(message_id))
                self.id_pipeline.hdel(LUT_Keys.CHANNEL.value, str(message_id))
                self.id_pipeline.hdel(LUT_Keys.GUILD.value, str(message_id))

            else:
                continue

        self.message_pipeline.delete(*names)
        self.message_pipeline.execute()
        self.id_pipeline.execute()
#endregion
