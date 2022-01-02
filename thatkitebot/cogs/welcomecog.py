#  Copyright (c) 2019-2022 ThatRedKite and contributors

import discord
from discord.ext import commands
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
                    return
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
        self.settings_redis: aioredis.Redis = bot.redis
            
    async def cog_check(self, ctx):
        return await self.settings_redis.hget(ctx.guild.id, "WELCOME") == "TRUE"

    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command(name="welcomes")
    async def welcome(self, ctx, *, args=None):
        """Welcome leaderboard"""
        current_time = datetime.utcfromtimestamp(int(time.mktime(ctx.message.created_at.timetuple())))
        # Scan all users in the DB
        # here's a nice one-liner
        key_list = [key async for key in self.redis_welcomes.scan_iter(match=f"leaderboard:*:{ctx.guild.id}")]
        
        leaderboard = dict()
        for i in key_list:
            author = re.findall(r":[\d]{5,}:", i)[0][1:-1]  # extract the author id
            leaderboard[f"<@{author}>"] = await self.redis_welcomes.hgetall(i)

        sorted_lb = sorted(leaderboard.items(), key=lambda x: int(x[1]['welcome_count']), reverse=True)

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
            last_join_dict = await self.redis_welcomes.hgetall(f"latest_join:{ctx.message.guild.id}")
            embed.add_field(name=":medal: Top 10:", value=lb_str, inline=False)
            if 'user_id' in last_join_dict:
                footer = str(str(f"<@{last_join_dict['user_id']}>") + " joined: **"
                             + str((current_time - datetime.utcfromtimestamp(
                    int(last_join_dict['latest_join']))).seconds // 3600)) + "** hours ago"
                embed.add_field(name=":partying_face: Latest join:", value=footer, inline=False)
        
        elif args.lower() == "me":
            embed = discord.Embed(title="Personal welcome count")
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
