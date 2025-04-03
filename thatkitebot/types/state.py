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

import discord.types
import discord.types.channel
from thatkitebot.tkb_redis.serialization import message_to_dict
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

        super().__init__(dispatch=dispatch, handlers=handlers, hooks=hooks, http=http, loop=loop, **options)


    def parse_message_create(self, data):
        channel, _ = self._get_guild_channel(data)
        # channel would be the correct type here

        message = Message(channel=channel, data=data, state=self)  # type: ignore

        # cache the message
        self.r_cache.add_message_dict(data)

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
        self.dispatch("raw_message_delete", raw)

        if found is not None:
            self.dispatch("message_delete", found)
            self.r_cache.expire_message_now(raw.message_id, raw.guild_id, raw.channel_id)

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
        if (message := self._get_message(raw.message_id)) is not None:
            emoji = self._upgrade_partial_emoji(emoji)
            reaction = message._add_reaction(data, emoji, raw.user_id)
            self.r_cache.add_message_object(message)

            if user := (raw.member or self._get_reaction_user(message.channel, raw.user_id)):
                self.dispatch("reaction_add", reaction, user)

    def parse_message_update(self, data) -> None:
        raw = discord.RawMessageUpdateEvent(data)
        if (message := self._get_message(raw.message_id)) is not None:
            older_message = copy.copy(message)
            raw.cached_message = older_message
            self.dispatch("raw_message_edit", raw)
            # Coerce the `after` parameter to take the new updated Member
            # ref: #5999
            older_message.author = message.author

            self.r_cache.update_message(data)
            self.dispatch("message_edit", older_message, message)
        else:
            self.r_cache.add_message_dict(data)
            self.dispatch("raw_message_edit", raw)

        if "components" in data and self._view_store.is_message_tracked(raw.message_id):
            self._view_store.update_from_message(raw.message_id, data["components"])

    def create_message(self, *, channel, data) -> Message:
        return Message(state=self, channel=channel, data=data)

    def _get_message(self, msg_id: int) -> Message:
        if (data := self.r_cache.get_message_dict(msg_id)) is not None:
            channel_id = self.r_cache.get_channel_id(msg_id)
            channel = self.get_channel(channel_id)
            return self.create_message(channel=channel, data=data)
         
        return None
    

# insanely buggy mess
class FullyCachedState(discord.state.ConnectionState):
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

    def parse_message_create(self, data):
        channel, _ = self._get_guild_channel(data)
        # channel would be the correct type here

        message = Message(channel=channel, data=data, state=self)  # type: ignore

        # cache the message
        self.r_cache.add_message_dict(message)
        self.r_cache.message_pipeline.execute()

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
        self.dispatch("raw_message_delete", raw)

        if found is not None:
            self.dispatch("message_delete", found)
            self.r_cache.expire_message_now(raw.message_id, raw.guild_id, raw.channel_id)

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
        if (message := self._get_message(raw.message_id)) is not None:
            emoji = self._upgrade_partial_emoji(emoji)
            reaction = message._add_reaction(data, emoji, raw.user_id)
            self.r_cache.add_message_object(message)

            if user := (raw.member or self._get_reaction_user(message.channel, raw.user_id)):
                self.dispatch("reaction_add", reaction, user)

    def parse_message_update(self, data) -> None:
        raw = discord.RawMessageUpdateEvent(data)
        if (message := self._get_message(raw.message_id)) is not None:
            older_message = copy.copy(message)
            raw.cached_message = older_message
            self.dispatch("raw_message_edit", raw)
            # Coerce the `after` parameter to take the new updated Member
            # ref: #5999
            older_message.author = message.author

            self.r_cache.add_message_dict(data)
            self.dispatch("message_edit", older_message, message)
        else:
            self.dispatch("raw_message_edit", raw)

        if "components" in data and self._view_store.is_message_tracked(raw.message_id):
            self._view_store.update_from_message(raw.message_id, data["components"])

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
