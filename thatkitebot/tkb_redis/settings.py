#  Copyright (c) 2019-2023 ThatRedKite and contributors
import enum
from typing import Union


from discord import Guild
from redis import asyncio as aioredis


class RedisFlags:
    class FlagEnum(enum.Enum):
        NSFW = 0
        IMAGE = 1
        REPOST = 2
        WELCOME = 3
        UWU = 4
        DETRACK = 5
        MUSIC = 6
        CACHING = 7
        WELCOME_MESSAGE = 8
        MODERATION = 9
        STARBOARD = 10


    @staticmethod
    async def set_guild_flag(redis: aioredis.Redis, guild: Union[Guild, None], flag_offset: int, value: bool) -> None:
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
        9: MODERATION
        10: STARBOARD (Disable-Flag, 1 = Disabled 0 = Enabled)
        """
        key = f"flags:{guild.id}"
        await redis.setbit(key, flag_offset, int(value))

    @staticmethod
    async def get_guild_flag(redis: aioredis.Redis, guild: Union[Guild, None], flag_offset: int) -> bool:
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
        9: MODERATION
        10: STARBOARD (Disable-Flag, 1 = Disabled 0 = Enabled)
        """
        if guild is not None:
            key = f"flags:{guild.id}"
            return await redis.getbit(key, flag_offset)
        else:
            return True
        
    @staticmethod
    async def get_guild_flag_by_id(redis: aioredis.Redis, guild_id: int, flag_offset: int) -> bool:
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
        9: MODERATION
        10: STARBOARD (Disable-Flag, 1 = Disabled 0 = Enabled)
        """
        if guild_id is not None:
            key = f"flags:{guild_id}"
            return await redis.getbit(key, flag_offset)
        else:
            return True
        
    @staticmethod
    async def set_guild_flag_custom(redis: aioredis.Redis, gid, name: str, value: bool, flag_offset: int) -> None:
        """
        Sets flags for a guild with a custom name. They are stored as Bitfields.
        """
        key = f"flags-{name}:{gid}"
        await redis.setbit(key, flag_offset, int(value))

    @staticmethod
    async def get_guild_flag_custom(redis: aioredis.Redis, gid, name: str, flag_offset: int,) -> None:
        """
        Gets flags for a guild with a custom name. They are stored as Bitfields.
        """
        key = f"flags-{name}:{gid}"
        return await redis.getbit(key, flag_offset)

    @staticmethod
    async def get_guild_flags(redis: aioredis.Redis, gid: Union[str, int], *flag_offsets):
        """
        Checks multiple flags at once, useful for checking multiple flags at once
        """

        key = f"flags:{gid}"
        items = [("u1", offset) for offset in flag_offsets]

        values = await redis.bitfield_ro(key, "u1", 0, items=items)

    @staticmethod
    async def toggle_guild_flag(redis: aioredis.Redis, gid, flag_offset: int) -> bool:
        """
        Sets flags for a guild. They are stored as Bitfields. The flags are stored in the following order:
        0: NSFW (nsfwcog.py) - NSFW commands
        1: IMAGES (imagecog.py) - Image commands
        3: WELCOME COUNTING (welcomecog.py) - Welcome Counting
        4: UWUIFICATION (uwucog.py) - uwuify
        5: LINK DETRACKING (detrack.py) - detracking
        6: MUSIC (musiccog.py) - music commands
        7: CACHING
        8: WELCOME MESSAGE
        9: MODERATION
        10: STARBOARD (Disable-Flag, 1 = Disabled 0 = Enabled)
        """
        key = f"flags:{gid}"
        current = await RedisFlags.get_guild_flag(redis, gid, flag_offset)
        await redis.setbit(key, flag_offset, int(not current))
        return not current





