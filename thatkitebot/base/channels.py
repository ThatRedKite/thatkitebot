"""
The MIT License (MIT)

Copyright (c) 2015-2021 Rapptz
Copyright (c) 2021-present Pycord Development

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

# this is a bit of copied code from pycord's internal channel factory stuff
# but i modified it to use pattern matching instead of if since this will always be run in an environment that supports it

from discord.enums import try_enum
import discord
from discord import ChannelType
from discord import TextChannel, VoiceChannel, CategoryChannel, StageChannel, ForumChannel, DMChannel, GroupChannel, Thread

def _guild_channel_factory(channel_type: int):
    value = try_enum(ChannelType, channel_type)

    match value:
        
        case ChannelType.text | ChannelType.news:
            return TextChannel, value
        
        case ChannelType.voice:
            return VoiceChannel, value
        
        case ChannelType.category:
            return CategoryChannel, value
        
        case ChannelType.stage_voice:
            return StageChannel, value
        
        case ChannelType.forum:
            return ForumChannel, value
        
        case _: 
            return None, value

def _channel_factory(channel_type: int):
    cls, value = _guild_channel_factory(channel_type)
    match value:

        case ChannelType.private:
            return DMChannel, value
        
        case ChannelType.group:
            return GroupChannel, value
        
        case _:
            return cls, value


def _threaded_channel_factory(channel_type: int):
    cls, value = _channel_factory(channel_type)
    match value:

        case ChannelType.private_thread | ChannelType.public_thread | ChannelType.news_thread:
            return Thread, value 

        case _:
            return cls, value

def get_channel(bot, channel_data: dict, guild: discord.Guild):
    factory, ch_type = _threaded_channel_factory(channel_data["type"])
    if factory is None:
        raise discord.InvalidData(
            "Unknown channel type {type} for channel ID {id}.".format_map(channel_data)
        )

    match ch_type:
        # the factory will be a DMChannel or GroupChannel here
        case ChannelType.group | ChannelType.private:
            return factory(me=bot.user, data=channel_data, state=bot._connection)

        case _:
            # the factory can't be a DMChannel or GroupChannel here
            # GuildChannels expect a Guild, we may be passing an Object
            return factory(guild=guild, state=bot._connection, data=channel_data)

        



