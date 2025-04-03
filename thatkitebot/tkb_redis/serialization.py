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

import discord
from typing import Optional

#region dict functions
def reaction_to_dict(reaction: discord.Reaction) -> dict:
    reaction_dict = dict(
        emoji={"name": reaction.emoji.name, "id": reaction.emoji.id} if not isinstance(reaction.emoji, str) else {"name": str(reaction.emoji), "id": None},
        count=reaction.count,
        me=reaction.me,
        burst=reaction.burst,
        me_burst=reaction.me_burst,
        burst_colors=reaction._burst_colours
    )

    return reaction_dict

def _serialize_embeds(message: discord.Message) -> list[Optional[discord.Embed]]:
    if message.embeds:
            return [embed.to_dict() for embed in message.embeds]
    else:
        return []
        
def _serialize_attachments(message: discord.Message):
    if message.attachments:
        return [attachment.to_dict() for attachment in message.attachments]
    else:
        return []
    
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

def member_to_dict(member: discord.Member) -> dict:
    return dict(
        roles = list(member._roles),
        premium_since = member.premium_since.isoformat() if member.premium_since else None,
        pending = member.pending,
        nick = member.nick,
        mute = member.voice.mute if member.voice else False,
        joined_at = member.joined_at.isoformat(),
        flags = member.flags.value,
        deaf = member.voice.deaf if member.voice else False,
        communication_disabled_until=member.communication_disabled_until.isoformat() if member.communication_disabled_until is not None else None,
        banner = member.banner._key if member.banner else None,
        avatar = member._avatar
    )

def message_to_dict(message: discord.Message) -> dict:
    dict_message = dict(
        type=message.type.value,
        tts=message.tts,
        timestamp=message.created_at.isoformat(),
        pinned=message.pinned,
        nonce=message.nonce,
        mentions=message.raw_mentions,
        mention_roles=message.raw_role_mentions,
        mention_everyone=message.mention_everyone,
        member=member_to_dict(message.author),
        id=message.id,
        channel_id=message.channel.id,
        author=user_to_dict(message.author),
        guild_id=message.guild.id or None,
        content=message.content,
        reference=message.reference.to_message_reference_dict() if message.reference else None,
        attachments=_serialize_attachments(message),
        embeds=_serialize_embeds(message),
        edited_timestamp=message._edited_timestamp,
        reactions=[reaction_to_dict(reaction) for reaction in message.reactions]
    )
    return dict_message

def channel_to_dict(channel: discord.abc.GuildChannel) -> dict:
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
        recipients=[user_to_dict(user) for user in channel.recipients] if channel.recipients else None,
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
#endregion 
  