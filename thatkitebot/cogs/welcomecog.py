# ------------------------------------------------------------------------------
#  MIT License
#
#  Copyright (c) 2019-2021 dimonDDL
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
#  documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
#  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
#  and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all copies or substantial portions of
#  the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
#  THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
#  TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
# ------------------------------------------------------------------------------
import discord
from discord.ext import commands
from thatkitebot.backend import util
#from aioredis import Redis
import aioredis
import time
import aioredis
import re
from datetime import datetime


async def update_count(redis: aioredis.Redis, message: discord.Message):
    if "welcome" in message.content.lower():
        guild = message.guild.id
        channel = message.channel.id
        author = message.author.id
        unixtime = time.mktime(message.created_at.timetuple())
        join_key = f"latest_join:{guild}"
        usr_key = f"leaderboard:{author}:{guild}"
        write = True
        welcome_count = 1
        if await redis.exists(join_key):
            if await redis.exists(usr_key):
                user_dict = await redis.hgetall(usr_key)
                joined_dict = await redis.hgetall(join_key)

                latest_welcome = int(user_dict["latest_welcome"])
                welcome_count = int(user_dict["welcome_count"])
                welcome_channel = int(joined_dict["join_channel"])
                latest_join = int(joined_dict["latest_join"])
                joined_id = int(joined_dict["user_id"])

                if welcome_channel == channel and latest_welcome <= latest_join and joined_id != author:
                    welcome_count += 1
                else:
                    write = False
            else:
                write = True
        datadict = dict(
            latest_welcome=int(unixtime),
            welcome_count=int(welcome_count)
        )
        if write:
            await redis.hmset(usr_key, datadict)


class WelcomeCog(commands.Cog, name="Welcome counter"):
    def __init__(self, bot):
        self.bot: discord.Client = bot
        self.redis_welcomes: aioredis.Redis = bot.redis_welcomes

    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command(name="welcomes")
    async def welcome(self, ctx, *, args=None):
        """Welcome leaderboard"""
        current_time = datetime.utcfromtimestamp(int(time.mktime(ctx.message.created_at.timetuple())))
        # Scan all users in the DB
        cur = b'0'  # set initial cursor to 0
        key_list = []
        while cur:
            cur, keys = await self.redis_welcomes.scan(cur, match=f'leaderboard:*:{ctx.guild.id}')
            key_list += keys
        leaderboard = {}
        for i in key_list:
            author = re.findall(r":[\d]{5,}:", i)[0][1:-1]
            leaderboard[f"<@{author}>"] = await self.redis_welcomes.hgetall(i)

        sorted_lb = sorted(leaderboard.items(), key=lambda x: x[1]['welcome_count'], reverse=True)

        if not args:
            embed = discord.Embed(title="Welcome leaderboard")
            lb_str = ""
            number = 1
            for i in sorted_lb:
                if number <= 10:
                    if number == 1:
                        number_str = ":first_place: "
                    elif number == 2:
                        number_str = ":second_place: "
                    elif number == 3:
                        number_str = ":third_place: "
                    else:
                        number_str = "​  **" + str(number) + "**. "
                    lb_str += number_str + str(i[0]) \
                              + " welcomes: **" + str(i[1]["welcome_count"]) + "**, last welcome: **" \
                              + str(
                        (current_time - datetime.utcfromtimestamp(int(i[1]["latest_welcome"]))).seconds // 3600) \
                              + "** hours ago\n"
                    number += 1
                    continue
                break
            last_join_dict = await self.redis_welcomes.hgetall(f"latest_join:{ctx.message.guild.id}")
            embed.add_field(name=":medal: Top 10:", value=lb_str, inline=False)
            footer = str(str(f"<@{last_join_dict['user_id']}>") + " joined: **"
                         + str((current_time - datetime.utcfromtimestamp(
                int(last_join_dict['latest_join']))).seconds // 3600)) + "** hours ago"
            embed.add_field(name=":partying_face: Latest join:", value=footer, inline=False)
        elif args.lower() == "me":
            embed = discord.Embed(title="Personal Welcome count")
            target_user = ctx.message.author.id
            lb_str = ""
            number = 1
            for i in sorted_lb:
                if str(target_user) in i[0]:
                    lb_str += "**" + str(number) + "**. " + str(i[0]) \
                              + " welcomes: **" + str(i[1]["welcome_count"]) + "**, last welcome: **" \
                              + str(
                        (current_time - datetime.utcfromtimestamp(int(i[1]["latest_welcome"]))).seconds // 3600) \
                              + "** hours ago\n"
                    embed.add_field(name=f"{str(ctx.message.author)}'s welcome count:", value=lb_str, inline=False)
                number += 1
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(WelcomeCog(bot))
