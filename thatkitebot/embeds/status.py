
import psutil
from datetime import datetime

import si_prefix
from discord import Embed
from thatkitebot.base.util import EmbedColors as ec


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
               f"Events per hour: **{bot.events_hour}**\n"
               f"Events total: **{bot.events_total}**"
               ),
        inline=False
    )

    try:
        embed.set_thumbnail(url=str(bot.user.avatar.url))
    except:
        pass

    embed.color = ec.lime_green
    return embed
