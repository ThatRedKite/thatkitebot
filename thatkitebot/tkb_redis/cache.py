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
from datetime import timedelta
from typing import Optional, Union

import discord.state
import orjson
import brotli
import discord
from redis import asyncio as aioredis

from thatkitebot.base.channels import get_channel
from .exceptions import *
#endregion


#region main class
class RedisCacheAsync:
    def __init__(
            self,
            bot: discord.Bot,
            state: discord.state.ConnectionState,
            auto_exec=False
            ):
        
        self.state = state
        self.bot = bot

        self.auto_exec = auto_exec
        
        self.lut            =   aioredis.Redis(host="redis", db=15, decode_responses=False)
        self.guild_cache    =   aioredis.Redis(host="redis_cache", db=1, decode_responses=False)
        self.channel_cache  =   aioredis.Redis(host="redis_cache", db=2, decode_responses=False)
        self.user_cache     =   aioredis.Redis(host="redis_cache", db=3, decode_responses=False)
        self.message_cache  =   aioredis.Redis(host="redis_cache", db=4, decode_responses=False)

        self.id_pipeline        =   self.lut.pipeline(transaction=True)
        self.message_pipeline   =   self.message_cache.pipeline(transaction=True)
        self.channel_pipeline   =   self.channel_cache.pipeline(transaction=True)
        self.guild_pipeline     =   self.guild_cache.pipeline(transaction=True)
        self.user_pipeline      =   self.user_cache.pipeline(transaction=True)

    @staticmethod
    def _serialize_embeds(message: discord.Message) -> list[Optional[discord.Embed]]:
        if message.embeds:
                return [embed.to_dict() for embed in message.embeds]
        else:
            return []
    
    @staticmethod
    def _compress(data_dict: dict) -> bytes:
        try:
            data_serialized = orjson.dumps(data_dict)
            return brotli.compress(data_serialized, quality=11)
        except:
            raise CompressionException
        
    @staticmethod
    def _decompress(data_bytes) -> dict:
        try:
            data_decompressed = brotli.decompress(data_bytes)
            return orjson.loads(data_decompressed)
        except:
            raise CompressionException
        
    @staticmethod
    def _sanity_check():
        return True
    
    @staticmethod
    def guild_to_dict(guild: discord.Guild) -> dict:
        guild_data = dict(
            id=guild.id,
            name=guild.name,
            icon=guild._icon,
            splash=guild._splash,
            discovery_splash=guild._discovery_splash,
            owner_id=guild.owner_id,
            afk_channel_id=guild.afk_channel.id if guild.afk_channel else None,
            afk_timeout=guild.afk_timeout,
            verification_level=guild.verification_level.value,
            default_message_notifications=guild.default_notifications.value,
            explicit_content_filter=guild.explicit_content_filter.value,
            roles=guild._roles,
            emojis=guild.emojis,
            features=guild.features,
            mfa_level=int(guild.mfa_level) if guild.mfa_level else None,
            application_id=guild.owner.id if guild.owner and guild.owner.bot else None,
            system_channel_id=guild._system_channel_id,
            system_channel_flags=guild._system_channel_flags,
            rules_channel_id=guild._rules_channel_id,
            max_presences=guild.max_presences,
            max_members=guild.max_members,
            vanity_url_code=None,
            description=guild.description,
            banner=guild._banner,
            premium_tier=guild.premium_tier,
            premium_subscription_count=guild.premium_subscription_count,
            preferred_locale=guild.preferred_locale,
            public_updates_channel_id=guild._public_updates_channel_id,
            max_video_channel_users=guild.max_video_channel_users,
            approximate_member_count=guild.approximate_member_count,
            approximate_presence_count=guild.approximate_presence_count,
            nsfw_level=guild.nsfw_level.value,
            stickers=guild.stickers,
            premium_progress_bar_enabled=guild.premium_progress_bar_enabled,
            safety_alerts_channel_id=None,
            incidents_data=None
        )

        return guild_data
    
    @staticmethod
    def user_to_dict(user: discord.User) -> dict:
        user_dict = dict(
            id=user.id,
            username=user.name,
            discriminator=user.discriminator,
            global_name=user.global_name,
            avatar=user.avatar.key if user.avatar else None,
            bot=user.bot,
            system=user.system,
            banner=user.banner.key if user.banner else None,
            accent_color=int(user.accent_color) if user.accent_color else None,
            )
        return user_dict 

    
    def message_to_dict(self, message: discord.Message) -> dict:
        dict_message = dict(
            content=message.content,
            clean_content=message.clean_content,
            reference=message.reference.to_message_reference_dict() if message.reference else None,
            tts=message.tts,
            mention_everyone=message.mention_everyone,
            attachments=message.attachments,
            embeds=self._serialize_embeds(message),
            edited_timestamp=int(message.edited_at.timestamp) if message.edited_at else None,
            mentions=message.raw_mentions,
            mention_roles=message.raw_role_mentions,
            pinned=message.pinned,
            type=message.type.value,
            reactions=message.reactions
        )
        return dict_message

    def channel_to_dict(self, channel: discord.abc.GuildChannel) -> dict:
        channel_dict = dict(
            id=channel.id,
            type=channel.type.value,
            guild_id=channel.guild.id if channel.guild else None,
            position=channel.position,
            name=channel.name,
            topic=channel.topic,
            nsfw=channel.nsfw,
            last_message_id=channel.last_message_id,
            bitrate=channel.bitrate if channel.bitrate else None,
            user_limit=channel.user_limit if channel.user_limit else None,
            recipients=[self.user_to_dict(user) for user in channel.recipients] if channel.recipients else None,
            icon=channel.icon.key if channel.icon else None,
            owner_id=channel.owner_id,
            application_id=None, # FIXME
            managed=None, # FIXME
            parent_id=channel.parent_id if channel.parent_id else None,
            video_quality_mode=channel.video_quality_mode.value,
            message_count=channel.message_count if channel.message_count else None,
            member_count=channel.member_count if channel.member_count else None,
            flags=channel.flags.value,
            total_message_sent=channel.total_message_sent if channel.total_message_sent else None
        )

        return channel_dict

    async def compressed_write_hash(self, pipeline, name: str, key: str, dict_data:dict):
        return await pipeline.hset(name, key, self._compress(dict_data))
    
    async def compressed_read_hash(self, redis: aioredis.Redis, name: str, key: str) -> dict:
        if data_compressed := await redis.hget(name, key):
            return self._decompress(data_compressed)
        return None
    
    async def compressed_write_key(self, pipeline, key: str, dict_data:dict):
        return await pipeline.set(key, self._compress(dict_data))
    
    async def compressed_read_key(self, redis: aioredis.Redis, key: str) -> dict:
        if data_compressed := await redis.get(key):
            return self._decompress(data_compressed)
        return None
    
    async def add_user(self, user: discord.User):
        await self.compressed_write_key(self.user_cache, str(user.id), self.user_to_dict(user))
        
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
            return self.state.create_user(data=data)
    
    async def add_message(self, message: discord.Message):
        entry_name = f"{message.guild.id}:{message.author.id}:{message.channel.id}:{message.id}"

        await self.compressed_write_key(self.message_pipeline, entry_name, self.message_to_dict(message))
        await self.message_pipeline.expire(entry_name, timedelta(weeks=2))

        # set up LUT
        await self.id_pipeline.hset("id_to_author", mapping={str(message.id): str(message.author.id)})
        await self.id_pipeline.hset("id_to_channel", mapping={str(message.id): str(message.channel.id)})
        await self.id_pipeline.hset("id_to_guild", mapping={str(message.id): str(message.guild.id)})
        await self.id_pipeline.hset("channel_to_guild", mapping={str(message.channel.id): str(message.guild.id)})
        
    async def get_author_id(self, message_id: Union[int, str]):
        # exectue the write pipeline to commit any pending changes before reading
        # ID pipeline
        await self.id_pipeline.execute()

        raw = await self.lut.hget("id_to_author", str(message_id))
        if raw is not None:
            return int(raw.decode("ASCII"))
        else:
            return None

    async def get_channel_id(self, message_id: Union[int, str]):
        # exectue the write pipeline to commit any pending changes before reading
        # ID pipeline
        await self.id_pipeline.execute()

        raw = await self.lut.hget("id_to_channel", str(message_id))
        if raw is not None:
            return int(raw.decode("ASCII"))
        else:
            return None

    async def get_guild_id(self, message_id: Union[int, str]):
        # exectue the write pipeline to commit any pending changes before reading 
        # uses ID pipeline
        await self.id_pipeline.execute()

        raw = await self.lut.hget("id_to_guild", str(message_id))
        if raw is not None:
            return int(raw.decode("ASCII"))
        else:
            return None

    async def get_guild_id_from_channel_id(self, channel_id):
        # exectue the write pipeline to commit any pending changes before reading 
        # uses ID pipeline

        await self.id_pipeline.execute()
        raw = await self.lut.hget("channel_to_guild", str(channel_id))
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
                message_data = self._decompress(raw_data)
                ids: str = key.decode("ASCII")
                ids = ids.split(":")
                author = await self.get_user_dict(ids[0])
                message_data.update({"id": ids[2], "author": author})
                yield discord.Message(state=self.state, data=message_data, channel=channel)

            counter += 1

    async def get_message(self, message_id: int, guild_id: Optional[int]=None, channel_id: Optional[int]=None, author_id: Optional[int]=None) -> Optional[discord.Message]:
        # exectue the write pipeline to commit any pending changes before reading 
        # ID pipeline, Message pipeline, Channel Pipeline, User Pipeline

        await self.id_pipeline.execute()
        await self.message_pipeline.execute()
        await self.channel_pipeline.execute()
        await self.user_pipeline.execute()

        try:
            if not guild_id:
                guild_id = await self.get_guild_id(message_id)

            if not author_id:
                author_id = await self.get_author_id(message_id)

            if not channel_id:
                channel_id = await self.get_channel_id(message_id)
                
        except AttributeError:
            raise CacheInvalidMessageException

        assert guild_id and author_id and channel_id


        # if we got the message data from the cache, cool
        if (message_data := await self.compressed_read_key(self.message_cache, f"{guild_id}:{author_id}:{channel_id}:{message_id}")) is not None:
            author = await self.get_user_dict(author_id)
            channel = await self.get_channel_dict(channel_id)
            message_data.update({"id": message_id, "author": author})
            return discord.Message(state=self.state, channel=channel, data=message_data)
        
        else:
            # if we didn't, we need to try to get it from the API
            message_data = await self.state.http.get_message(message_id)
            # add it to the cache pipeline
            new_message = discord.Message(state=self.state, channel=channel, data=message_data)
            await self.add_message(new_message)
            await self.exec()

        
    # TODO: channel cache stuff
    async def add_channel(self, channel: discord.abc.GuildChannel):
        channel_data = self.channel_to_dict(channel)

        # Channel Pipeline & ID Pipeline
        await self.compressed_write_key(self.channel_pipeline, str(channel.id), channel_data)
        await self.id_pipeline.hset("channel_to_guild", str(channel.id), channel_data["guild"]["id"])

    async def get_channel_object(self, channel_id: int, guild_id: Optional[int] = None, fetch=True):
        # exectue the write pipeline to commit any pending changes before reading 

        # ID Pipeline, Channel Pipeline, Guild Pipeline
        await self.channel_pipeline.execute()
        await self.id_pipeline.execute()
        await self.guild_pipeline.execute()

        if not guild_id:
            # try to get the guild id from the lookup table
            if (guild_id := await self.get_guild_id_from_channel_id(channel_id)) is not None:
                if channel_data := await self.channel_cache.get(str(channel_id)):
                    guild = await self.get_guild_object(guild_id)

                    return get_channel(self.bot, channel_data, guild)
                else:
                    return None

            elif (channel_data := await self.state.http.get_channel(channel_id)) is not None and fetch is True:
                    guild = await self.add_guild_by_id(guild_id)
                    await self.compressed_write_key(self.channel_cache, str(channel_id), channel_data)
                    return get_channel(self.bot,channel_data, guild)
                    # update the guild we have in the cache

            else:
                return None
                
    async def get_channel_dict(self, channel_id: int, fetch=True) -> dict:
        # exectue the write pipeline to commit any pending changes before reading 
        # Channel Pipeline
        await self.channel_pipeline.execute()
        if channel_data := await self.compressed_read_key(self.channel_cache, str(channel_id)):
            return channel_data
        
        if fetch:
            return await self.state.http.get_channel(channel_id)

    async def add_guild_by_id(self, guild_id: int, sync_channels=False) -> discord.Guild:
        # get the guild data from the API
        guild_data = await self.state.http.get_guild(guild_id)

        # Guild Pipeline
        await self.guild_pipeline.execute()
        await self.compressed_write_key(self.guild_pipeline, str(guild_id), guild_data)

        # return the guild object for good measure as well
        return discord.Guild(data=guild_data, state=self.state)
    
    async def add_guild_object(self, guild: discord.Guild, sync_channels=False, sync_members=False):
        # TODO: add missing values

        # Guild Pipeline
        await self.compressed_write_key(self.guild_pipeline, str(guild.id), self.guild_to_dict(guild))
        
        if sync_channels:
            for channel in guild.channels:
                await self.add_channel(channel)
                
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
                raise CacheMissException
            
        raise CacheMissException

    async def get_guild_object(self, guild_id: int, with_counts=False, fetch=True):
        guild_data = await self.get_guild_dict(guild_id, with_counts, fetch)
        return discord.Guild(data=guild_data,state=self.state)
        
            
    async def exec(self):
        await self.guild_pipeline.execute()
        await self.id_pipeline.execute()
        await self.channel_pipeline.execute()
        await self.message_pipeline.execute()
        await self.user_pipeline.execute()

    def get_pipeline_stats(self):
        return dict(
            id_pipeline=len(self.id_pipeline.command_stack),
            message_pipeline=len(self.message_pipeline.command_stack),
            channel_pipeline=len(self.channel_pipeline.command_stack),
            user_pipeline=len(self.user_pipeline.command_stack),
            guild_pipeline=len(self.guild_pipeline.command_stack),
        )

#endregion
