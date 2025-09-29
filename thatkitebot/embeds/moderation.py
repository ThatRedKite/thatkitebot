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
from datetime import timedelta, datetime, timezone

from discord import Embed, Color, ClientException, Member
from thatkitebot.base.util import EmbedColors as ec
from thatkitebot.base.util import link_from_ids
from thatkitebot.base.url import get_avatar_url
#endregion

#region main code
def gen_edit_warning(payload) -> Embed:
    warn_embed = Embed(
        title="Edit Warning",
        description=f"Message older than threshold has been edited: [Go to Message]({link_from_ids(payload.guild_id, payload.channel_id, payload.message_id)})",
        color=ec.traffic_red
    )

    # try to add a field with the new contents, don't if it fails
    try:
        warn_embed.add_field(name="New Message", value=f"""{payload.data['content']}""")
    except KeyError:
        pass
    except ClientException:
        pass

    return warn_embed

# TODO
def gen_new_account_warning(member: Member, timediff: timedelta) -> Embed:
    warn_embed = Embed(
        title="New Account Warning",
        description=f"Accont age under threshold for user {member.mention}",
        color=ec.traffic_red,
        thumbnail=get_avatar_url(member)
    )

    warn_embed.add_field(
        name="** **",
        value=f"**Username**:\n`{member.name}`\n**Display Name**:\n`{member.display_name}`\n**Nickname**:\n`{member.nick}`\n**ID**:\n`{member.id}`"
    )
    
    warn_embed.add_field(
        name="** **",
        value=f"**Join Time**:\n<t:{int(member.joined_at.timestamp())}>\n**Account Creation Time**:\n<t:{int(member.created_at.timestamp())}:R>\n**Account Age**:\n`{timediff}`"
    )

    warn_embed.timestamp = datetime.now(timezone.utc)

    return warn_embed
#endregion
