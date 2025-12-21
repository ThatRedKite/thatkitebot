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

from thatkitebot.types.message import Message
from thatkitebot.tkb_redis.cache import RedisCacheSyncPartial, RedisCacheSync, decompress_data

import asyncio
import copy
import logging
from datetime import timedelta

import discord

discord_logger = logging.getLogger("discord")

# only caches messages with redis
class PartiallyCachedState(discord.state.ConnectionState):
    def __init__(self, *, dispatch, handlers, hooks, http, loop, cache, **options):
        self.r_cache: RedisCacheSyncPartial = cache
        self.max_messages = None
        self.logger = logging.getLogger("global")

        super().__init__(dispatch=dispatch, handlers=handlers, hooks=hooks, http=http, loop=loop, **options)


    def parse_message_create(self, data):
        channel, _ = self._get_guild_channel(data)
        self.r_cache.add_message_dict(data)
        # channel would be the correct type here
        message = self.create_message(channel=channel, data=data)  # type: ignore
        
        # cache the message
        self.dispatch("message", message)

        # we ensure that the channel is either a TextChannel, VoiceChannel, StageChannel, or Thread
        if channel and channel.__class__ in (
            discord.TextChannel,
            discord.VoiceChannel,
            discord.StageChannel,
            discord.Thread,
        ):
            channel.last_message_id = message.id  # type: ignore

    def parse_message_delete(self, data) -> None:
        raw = discord.RawMessageDeleteEvent(data)

        found = self._get_message(raw.message_id)
        raw.cached_message = found
        self.r_cache.expire_message_now(raw.message_id, raw.guild_id, raw.channel_id)
        self.dispatch("raw_message_delete", raw)
        
        if found is not None:
            self.dispatch("message_delete", found)

    def parse_message_delete_bulk(self, data) -> None:
        raw = discord.RawBulkMessageDeleteEvent(data)

        #TODO: implement cached message retrieval here
        raw.cached_messages = []

        self.r_cache.mass_expire_messages(raw.message_ids, raw.guild_id, raw.channel_id)
        self.dispatch("raw_bulk_message_delete", raw)

    def parse_message_reaction_add(self, data) -> None:
        emoji = data["emoji"]
        emoji_id = discord.utils._get_as_snowflake(emoji, "id")
        emoji = discord.PartialEmoji.with_state(
            self, id=emoji_id, animated=emoji.get("animated", False), name=emoji["name"]
        )
        raw = discord.RawReactionActionEvent(data, emoji, "REACTION_ADD")

        if member_data := data.get("member"):
            if (guild := self._get_guild(raw.guild_id)) is not None:
                raw.member = discord.Member(data=member_data, guild=guild, state=self)
            else:
                raw.member = None
        else:
            raw.member = None

        self.dispatch("raw_reaction_add", raw)

        # rich interface here
        if (message := self._get_message_with_data(raw.message_id)) is not None:
            message, data_old = message
            emoji = self._upgrade_partial_emoji(emoji)
            reaction = message._add_reaction(data, emoji, raw.user_id)
            self.r_cache.add_message_object(message)

            if user := (raw.member or self._get_reaction_user(message.channel, raw.user_id)):
                self.dispatch("reaction_add", reaction, user)

    def parse_message_update(self, data) -> None:
        raw = discord.RawMessageUpdateEvent(data)
        self.dispatch("raw_message_edit", raw)
        if (message := self._get_message_with_data(raw.message_id)) is not None:
            message, original_data = message # unpack the message tuple containing the message and the old data
            new_message: Message = copy.copy(message)
            
            original_data.update(data) # update the original data
            self.r_cache.add_message_dict(original_data) # add updated data to the cache
            new_message._update(data) # update the message object

            raw.cached_message = message
            new_message.author = message.author
            
            self.dispatch("message_edit", message, new_message)
        else:
            self.r_cache.add_message_dict(data)

        if "components" in data and self._view_store.is_message_tracked(raw.message_id):
            self._view_store.update_from_message(raw.message_id, data["components"])

    def create_message(self, *, channel, data) -> Message:
        if (d := data.get("message_reference")) is not None:
            if not d.get("channel_id"):
                data["message_reference"].update({"channel_id": data["channel_id"]})
        return Message(state=self, channel=channel, data=data)

        
    def _get_message(self, msg_id: int) -> Message:
        if (data := self.r_cache.get_message_dict(msg_id)) is not None:
            channel, _ = self._get_guild_channel(data)
            return self.create_message(channel=channel, data=data)
    
    def _get_message_with_data(self, msg_id: int) -> tuple[Message, dict]:
        if (data := self.r_cache.get_message_dict(msg_id)) is not None:
            channel, _ = self._get_guild_channel(data)
            a = copy.copy(data)
            message = self.create_message(channel=channel, data=a), data
            return message
    

# insanely buggy mess
class FullyCachedState(PartiallyCachedState):
    def __init__(self, *, dispatch, handlers, hooks, http, loop, cache, **options):
        self.r_cache: RedisCacheSync = cache
        self.max_messages = None

        super().__init__(dispatch=dispatch, handlers=handlers, hooks=hooks, http=http, loop=loop, **options)

    @property
    def guilds(self) -> list[discord.Guild]:
        _guilds = []
        for data_compressed in self.r_cache.guild_cache.scan_iter("*"):
            _guilds.append(discord.Guild(data=decompress_data(data_compressed), state=self))

        return _guilds

    def parse_user_update(self, data) -> None:
        # self.user is *always* cached when this is called
        user: discord.ClientUser = self.user  # type: ignore
        user._update(data)

        if ref := self.r_cache.get_user_object(user.id):
            ref._update(data)
            self.r_cache.add_user(ref)

    def parse_channel_update(self, data) -> None:
        channel_type = discord.enums.try_enum(discord.ChannelType, data.get("type"))
        channel_id = int(data["id"])
        if channel_type is discord.ChannelType.group:
            channel = self._get_private_channel(channel_id)
            old_channel = copy.copy(channel)
            # the channel is a GroupChannel
            channel: discord.GroupChannel
            channel._update_group(data)  # type: ignore
            self.dispatch("private_channel_update", old_channel, channel)
            return

        guild_id = discord.utils._get_as_snowflake(data, "guild_id")
        if (guild := self._get_guild(guild_id)) is not None:
            if (channel := guild.get_channel(channel_id)) is not None:
                old_channel = copy.copy(channel)
                channel._update(guild, data)
                self.dispatch("guild_channel_update", old_channel, channel)
            else:
                discord_logger.debug(
                    "CHANNEL_UPDATE referencing an unknown channel ID: %s. Discarding.",
                    channel_id,
                )
        else:
            discord_logger.debug(
                "CHANNEL_UPDATE referencing an unknown guild ID: %s. Discarding.",
                guild_id,
            )

    def parse_ready(self, data) -> None:
        if not hasattr(self, "_ready_state"):
            self._ready_state = asyncio.Queue()

        self.user = user = discord.ClientUser(state=self, data=data["user"])
        # self._users is a list of Users, we're setting a ClientUser
        self.r_cache.add_user(user)
        #self._users[user.id] = user  # type: ignore

        if self.application_id is None:
            try:
                application = data["application"]
            except KeyError:
                pass
            else:
                self.application_id = discord.utils._get_as_snowflake(application, "id")
                self.application_flags = discord.ApplicationFlags._from_value(
                    application["flags"]
                )

        for guild_data in data["guilds"]:
            self._add_guild_from_data(guild_data)

        if self._messages:
            self._update_message_references()

        self.dispatch("connect")
        self.dispatch("shard_connect", data["__shard_id__"])

        if self._ready_task is None:
            self._ready_task = asyncio.create_task(self._delay_ready())

    def _add_guild(self, guild):
        self.r_cache.add_guild_object(guild)
        self.r_cache.guild_pipeline.execute()

    def _remove_guild(self, guild):
        self.r_cache.guild_pipeline.expire(str(guild.id), timedelta(seconds=10), lt=True)

        for emoji in guild.emojis:
            self._emojis.pop(emoji.id, None)

        for sticker in guild.stickers:
            self._stickers.pop(sticker.id, None)

    def store_user(self, data) -> discord.User:
        user_id = int(data["id"])
        if _user := self.r_cache.get_user_object(user_id):
            return _user

        else:
            user = discord.User(state=self, data=data)
            if user.discriminator != "0000":
                user._stored = True
                self.r_cache.add_user(user)

            return user

    def deref_user(self, user_id: int) -> None:
        #self._users.pop(user_id, None)
        self.r_cache.user_pipeline.expire(str(user_id), timedelta(seconds=10), lt=True)

    def get_user(self, id: int | None) -> discord.User | None:
        return self.r_cache.get_user_object(id)

    def get_channel(self, id):
        if guild_id := self.r_cache.get_guild_id_from_channel_id(id):
            return self.r_cache.get_channel_object(id, guild_id)

        return None

    def is_guild_evicted(self, guild) -> bool:
        return self.r_cache.guild_cache.exists(str(guild.id))

    def _get_guild(self, guild_id) -> discord.Guild:
        return self.r_cache.get_guild_object(guild_id)

    def _get_message(self, msg_id) -> Message:
        return self.r_cache.get_message_object(msg_id)
