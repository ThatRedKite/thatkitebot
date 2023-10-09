#  Copyright (c) 2019-2023 ThatRedKite and contributors

from datetime import timedelta
from typing import Union

import orjson
import brotli
import discord
from redis import asyncio as aioredis


from thatkitebot.base.image_stuff import get_image_urls, NoImageFoundException
from .exceptions import *


class RedisCache:
    def __init__(self, redis: aioredis.Redis, bot: discord.Bot, auto_exec=False):
        self.redis: aioredis.Redis = redis
        self.bot: discord.Bot = bot

        self.auto_exec = auto_exec

        self.pipeline = redis.pipeline()

    def _sanity_check(self, message: discord.Message):
        # things we do not want to cache
        is_dm = isinstance(message.channel, discord.DMChannel)
        is_system = message.is_system()
        is_me = message.author is self.bot.user
        return any((is_me, is_system, is_dm))

    async def add_message(self, message: discord.Message):
        """
        Adds a message to the cache. The message is stored in the following format: guild_id:channel_id:user_id:message_id
        """
        urls = []
        try:
            urls = await get_image_urls(message)
        except NoImageFoundException:
            pass

        if not message or self._sanity_check(message):
            raise CacheInvalidMessageException

        hash_key = str(message.author.id)
        entry_key = f"{message.guild.id}:{message.channel.id}:{message.id}"

        dict_fun = dict(
            clean_content=message.clean_content,
            reference=message.reference.to_message_reference_dict() if message.reference else None,
            urls=urls,
            reactions=[]
        )

        butt = orjson.dumps(dict_fun)
        data_compressed = brotli.compress(butt, quality=11)
        await self.pipeline.hset(hash_key, entry_key, data_compressed)
        await self.pipeline.hset("id_to_author", mapping={str(message.id): str(message.author.id)})
        await self.pipeline.hset("id_to_channel", mapping={str(message.id): str(message.channel.id)})
        await self.pipeline.expire(hash_key, timedelta(days=7))

        if self.auto_exec:
            await self.pipeline.execute()

    async def update_message(self, key: str, author_id: int, data_new: dict):
        if not data_new:
            raise NoDataException

        try:
            dumped = orjson.dumps(data_new)
            compressed_data = brotli.compress(dumped, quality=11)
            await self.pipeline.hset(name=str(author_id), key=key, value=compressed_data)

        except Exception:
            raise NoDataException

    async def get_author_id(self, message_id: Union[int, str]):
        return int((await self.redis.hget("id_to_author", str(message_id))).decode("ASCII"))

    async def get_channel_id(self, message_id: Union[int, str]):
        return int((await self.redis.hget("id_to_channel", str(message_id))).decode("ASCII"))

    async def get_message(self, message_id: int, guild_id: int, channel_id: int | None = None, author_id: int | None = None):
        # get the message from the message_id
        # pretty stupid, but it works
        try:
            if not author_id:
                author_id = await self.get_author_id(message_id)

            if not channel_id:
                channel_id = await self.get_channel_id(message_id)
        except AttributeError:
            raise CacheInvalidMessageException

        key = str(author_id)
        hash_key = f"{guild_id}:{channel_id}:{message_id}"


        # make sure we actually got a key

        raw = await self.redis.hget(key, hash_key)

        if not raw:
            raise CacheInvalidMessageException


        # decompress the data
        data_uncompressed = brotli.decompress(raw)

        # decode the json and turn it into a python dict
        data_decoded = orjson.loads(data_uncompressed)
        return hash_key, data_decoded

    async def get_messages(self, guild_id: int, channel_id: int | None = None, author_id: int | None = None) -> list[str]:
        # get the message from the message_id
        # pretty stupid, but it works
        try:
            if not author_id:
                raise CacheException("An author ID is required")
            if not channel_id:
                hash_key = f"{guild_id}:*"
            else:
                hash_key = f"{guild_id}:{channel_id}:*"

        except AttributeError:
            raise CacheInvalidMessageException

        key = str(author_id)

        # make sure we actually got a key

        contents = [] # create empty list to hold the message contents

        async for key, data in self.redis.hscan_iter(key, match=hash_key):
            data_uncompressed = brotli.decompress(data)
            data_decoded = orjson.loads(data_uncompressed)
            contents.append(data_decoded["clean_content"])

        return contents

    async def exec(self):
        await self.pipeline.execute()






