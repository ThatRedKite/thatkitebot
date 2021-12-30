from discord import Message
from aioredis import Redis
from datetime import timedelta
import base64


async def add_message_to_cache(redis: Redis, message: Message):
    key = f"{hex(message.guild.id)}:{hex(message.channel.id)}:{hex(message.author.id)}:{hex(message.id)}"
    msgdict = dict(
        content=base64.b64encode(message.clean_content.encode("UTF-8")),
        created_at=hex(int(message.created_at.timestamp()))
    )
    await redis.hmset(key, msgdict)
    await redis.expire(key, timedelta(weeks=1))
    return message


async def get_contents(redis: Redis, gid, cid, uid):
    key = f"{hex(gid)}:{hex(cid)}:{hex(uid)}:*"
    a = list()
    async for mkey in redis.scan_iter(key):
        c = await redis.hget(mkey, "content")
        a.append(base64.b64decode(c).decode("UTF-8"))
    return a
