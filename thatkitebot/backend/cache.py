#  Copyright (c) 2019-2022 ThatRedKite and contributors

from discord import Message
from aioredis import Redis
import base64


async def add_message_to_cache(redis: Redis, message: Message):
    key = f"{message.guild.id}:{message.channel.id}:{message.author.id}:{message.id}"
    msgdict = dict(
        content=base64.b64encode(message.clean_content.encode("UTF-8")),
        created_at=int(message.created_at.timestamp())
    )
    await redis.hmset(key, msgdict)
    # set the expiration time of the message in the cache to 1 week
    await redis.expire(key, 604800)
    return message


async def get_contents(redis: Redis, gid, cid, uid):
    key = f"{gid}:{cid}:{uid}:*"
    a = list()
    async for mkey in redis.scan_iter(key):
        c = await redis.hget(mkey, "content")
        # decode the content from base64 to UTF-8 and add it to the list a
        a.append(base64.b64decode(c).decode("UTF-8"))
    return a

