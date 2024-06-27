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
import psutil
from datetime import datetime

import si_prefix #type: ignore
from discord import Embed

from thatkitebot.base.util import EmbedColors as ec
#endregion

async def gen_embed(bot, redis):
    process = psutil.Process(bot.pid)
    mem = process.memory_info()[0]
    redis_memory = (await redis.info())["used_memory"] + (await redis.info())["used_memory"]
    cpu = psutil.cpu_percent(interval=None)
    ping = round(bot.latency * 1000, 1)
    uptime = str(datetime.now() - bot.start_time).split(".")[0]

    total_users = sum([users.member_count for users in bot.guilds])

    guilds = len(bot.guilds)

    embed = Embed()
    embed.add_field(
        name="System status",
        value=(f"RAM usage: **{si_prefix.si_format(mem)}B**\n"
               f"Cache: **{si_prefix.si_format(redis_memory)}B**\n"
               f"CPU usage: **{cpu} %**\n"
               f"Uptime: **{uptime}**\n"
               f"Ping: **{ping} ms**\n"
               ),
        inline=False
    )

    embed.add_field(
        name="Bot stats",
        value=(f"Guilds: **{guilds}**\n"
               f"Extensions loaded: **{len(bot.extensions)}**\n"
               f"Total users: **{total_users}**\n"
               f"Bot version: **{bot.version}**\n"
               f"Running commit: **[{bot.git_hash[0:7]}](https://github.com/ThatRedKite/thatkitebot/tree/{bot.git_hash})**\n"
               f"Total command invokes: **{bot.command_invokes_total}**\n"
               f"Commands invoked this hour: **{bot.command_invokes_hour}**\n"
               f"Events per hour: **{si_prefix.si_format(bot.events_hour, 0)}**\n"
               f"Events total: **{si_prefix.si_format(bot.events_total, 0)}**"
               ),
        inline=False
    )

    embed.set_footer(text=f"{bot.user.name} - Version {bot.version}")

    try:
        embed.set_thumbnail(url=str(bot.user.avatar.url))
    except:
        pass

    embed.color = ec.lime_green
    return embed
