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
from datetime import datetime, timezone

from discord import Embed

from thatkitebot.base.util import EmbedColors as ec
#endregion

def gen_embed(self) -> Embed:
    if self.bot.message_cache_cipher.enabled:
        message_storage = (
            "Message cache encryption is **enabled** on this instance. Cached messages are encrypted with AES-256.\n"
            "All cached user messages are encrypted using a key generated at startup. And is automatically erased when the bot stops.\n"
            "Messages are decrypted for a short period of time while the bot processes them."
        )
    else:
        message_storage = (
            "Message cache encryption is **disabled** on this instance. Cached message are not encrypted.\n"
        )

    embed = Embed(
        color=ec.purple_violet,
        title="ThatKiteBot Privacy Policy",
        description="ThatKiteBot is run by @thatredkite. This privacy policy will explain how this bot uses the personal data collected from you when you use it."
    )

    embed.add_field(
        name="What data does the bot collect?",
        value="The bot collects the following data:\n"
              "- Your Discord ID\n"
              "- Your Discord username\n"
              "- Your Discord avatar\n"
              "- Reactions you add to messages\n"
              "- Messages sent by you in channels the bot can access, including content, embeds, mentions and attachment metadata\n"
              "- Server and channel information needed for the bot's features\n"
              "- Any other data you provide the bot with while using its commands"
    )

    embed.add_field(
        name="How is the data collected?",
        value="The bot collects the data it needs to function. It does this only by using the Discord API.\n"
              "You directly provide the bot with most of the data we collect. The bot collects and processes the data when you:\n"
              "- Send or edit a message\n"
              "- Use a command\n"
              "- Use a reaction\n"
    )

    embed.add_field(
        name="How will your data be used?",
        value="The bot collects data so that it can:\n"
              "- Process your commands\n"
              "- Provide Markov functionality\n"
              "- Understand the context of commands\n"
              "- Provide enabled features such as moderation, bookmarks, repost detection and starboard\n"
              "Some commands contact Discord or other external services and send the input or request data needed for that feature."
    )

    embed.add_field(
        name="How is your data stored?",
        value="The bot is hosted on a server in Nuremberg (Germany). Only bot operators have access to the server, and we do not share any data with third parties.\n"
              "The message cache uses a separate RAM-only database configured without disk persistence. Other feature data is stored separately and can persist across restarts."
    )

    embed.add_field(
        name="Is the message cache encrypted?",
        value=message_storage,
        inline=False
    )

    embed.add_field(
        name="How long are cached messages retained?",
        value="Message cache entries expire 14 days after their last write. Updating or caching a message again can restart this timer.\n"
              "When a message deletion event is processed, its cache entry is removed or given a shorter expiry automatically.\n"
              "These expiry rules apply to the the bot's own message cache, not to separately stored feature data or copies posted to Discord.",
        inline=False
    )

    embed.add_field(
        name="What data is stored separately?",
        value="Message, user, channel and server IDs used as cache keys or lookup records are not encrypted.\n"
              "User, channel and server caches are also outside message cache encryption and have no default expiry.\n"
              "Settings, bookmarks and their comments, repost image hashes and message links, starboard mappings, and operational or moderation logs are persistent.\n"
              "Messages posted by bot features to Discord remain subject to Discord's storage and deletion behavior.",
        inline=False
    )

    embed.add_field(
        name="What are your data protection rights?",
        value="We would like to make sure you are fully aware of all of your data protection rights. Every user is entitled to the following:\n"
              "If you make a request, we have one month to respond to you. If you would like to exercise any of these rights, please contact @thatredkite on Discord.\n"
    )

    embed.add_field(
        name="Your rights listed below:",
        inline=False,
        value="The right to *access* – You have the right to request us for copies of your personal data. We may charge you a small fee for this service.\n"
              "The right to *rectification* – You have the right to request that we correct any information you believe is inaccurate. You also have the right to request us to complete the information you believe is incomplete.\n"
              "The right to *erasure* – You have the right to request that we erase your personal data, under certain conditions.\n"
              "The right to *restrict processing* – You have the right to request that we restrict the processing of your personal data, under certain conditions.\n"
              "The right to *object to processing* – You have the right to object to our processing of your personal data, under certain conditions.\n"
              "The right to *data portability* – You have the right to request that we transfer the data that we have collected to another organization, or directly to you, under certain conditions.\n"
    )

    embed.set_thumbnail(url=str(self.bot.user.avatar.url))
    embed.set_footer(text=f"{self.bot.user.name} v{self.bot.version} this policy was last updated: ")
    embed.timestamp = datetime(2026, 11, 11, tzinfo=timezone.utc)
    return embed