import base64
from typing import Union

from discord import Message
from redis import asyncio as aioredis


class RedisFlags:
    NSFW = 0
    IMAGE = 1
    REPOST = 2
    WELCOME = 3
    UWU = 4
    DETRACK = 5
    MUSIC = 6
    CACHING = 7
    WELCOME_MESSAGE = 8

    @staticmethod
    async def set_guild_flag(redis: aioredis.Redis, gid, flag_offset: int, value: bool) -> None:
        """
        Sets flags for a guild. They are stored as Bitfields. The flags are stored at the following offsets:
        0: NSFW (nsfwcog.py) - NSFW commands
        1: IMAGES (imagecog.py) - Image commands
        3: WELCOME COUNTING (welcomecog.py) - Welcome Counting
        4: UWUIFICATION (uwucog.py) - uwuify
        5: LINK DETRACKING (detrack.py) - detracking
        6: MUSIC (musiccog.py) - music commands
        7: CACHING
        8: WELCOME MESSAGE
        """
        key = f"flags:{gid}"
        #await redis.execute_command("BITFIELD", key, "SET", "u1", flag_offset, int(value))
        await redis.setbit(key, flag_offset, int(value))

    @staticmethod
    async def get_guild_flag(redis: aioredis.Redis, gid: Union[str, int], flag_offset: int) -> bool:
        """
        Gets a flag from a guild. See set_guild_flag() for more info.
        """
        key = f"flags:{gid}"
        flag_value = await redis.getbit(key, flag_offset)
        return bool(flag_value)

    @staticmethod
    async def get_guild_flags(redis: aioredis.Redis, gid: Union[str, int], *flag_offsets):
        """
        Checks multiple flags at once, useful for checking multiple flags at once
        """

        key = f"flags:{gid}"
        items = [("u1", offset) for offset in flag_offsets]

        values = await redis.bitfield_ro(key, "u1", 0, items=items)
        print(values)

    @staticmethod
    async def toggle_guild_flag(redis: aioredis.Redis, gid, flag_offset: int) -> bool:
        """
        Sets flags for a guild. They are stored as Bitfields. The flags are stored in the following order:
        0: NSFW (nsfwcog.py)
        1: IMAGES (imagecog.py)
        3: WELCOME COUNTING (welcomecog.py)
        4: UWUIFICATION (uwucog.py)
        5: LINK DETRACKING (detrack.py)
        6: MUSIC (musiccog.py)
        """
        key = f"flags:{gid}"
        current = await RedisFlags.get_guild_flag(redis, gid, flag_offset)
        print(current)
        #await redis.execute_command("BITFIELD", key, "SET", "u1", flag_offset, int(not current))
        await redis.setbit(key, flag_offset, int(not current))
        return not current





