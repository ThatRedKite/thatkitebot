#  Copyright (c) 2019-2024 ThatRedKite and contributors


import discord
from discord.ext import commands

import time
import re
from datetime import datetime
from operator import itemgetter
from typing import Optional

import discord
from discord.ext import commands
from redis import asyncio as aioredis

from thatkitebot.tkb_redis.settings import RedisFlags


async def update_count(redis: aioredis.Redis, message: discord.Message):
    """
    Updates the welcome count for the given message's author.
    """
    if "welcome" in message.content.lower():
        write = True
        guild, channel, author = message.guild.id, message.channel.id, message.author.id
        unix_time = time.mktime(message.created_at.timetuple())
        join_key = f"latest_join:{guild}"
        assert await redis.exists(join_key)  # make sure there is a last_joined key
        joined_dict = await redis.hgetall(join_key)
        welcome_channel, latest_join, joined_id = itemgetter("join_channel", "latest_join", "user_id")(joined_dict)
        welcome_channel, latest_join, joined_id = int(welcome_channel), int(latest_join), int(joined_id)
        usr_key = f"leaderboard:{author}:{guild}"
        if await redis.exists(usr_key):
            latest_welcome = int(await redis.hget(usr_key, "latest_welcome"))
            if latest_welcome <= latest_join and joined_id != author:
                await redis.hincrby(usr_key, "welcome_count", 1)  # increase welcome_count by one; create if not exist
            else:
                return
        else:
            write = (welcome_channel == channel)
            await redis.hset(usr_key, "welcome_count", 1)

        if write:
            await redis.hset(usr_key, "latest_welcome", int(unix_time))


class WelcomeCog(commands.Cog, name="Welcome counter"):
    """
    A cog that counts the number of times a user has welcome newly joined members.
    """
    def __init__(self, bot):
        self.bot: discord.Client = bot
        self.redis_welcomes: aioredis.Redis = bot.redis_welcomes
        self.settings_redis: aioredis.Redis = bot.redis

    async def cog_check(self, ctx):
        return await RedisFlags.get_guild_flag(self.settings_redis, ctx.guild, RedisFlags.FlagEnum.WELCOME)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        self.bot.events_hour += 1
        self.bot.events_total += 1
        """
        Updates the welcome count for the given message's author. This is called by the bot on every message.
        """
        # ignore DMs
        if not message.guild:
            return

        # check, if welcome features are even enabled
        if not await RedisFlags.get_guild_flag(self.settings_redis, message.guild, RedisFlags.FlagEnum.WELCOME):
            return

        # make sure we are in the system channel. If not, return
        if message.channel is not message.guild.system_channel:
            return

        # make sure the message is not a bot command
        elif message.content.startswith(self.bot.command_prefix):
            return

        # ignore the bot's own messages
        elif message.author is self.bot.user:
            return

        try:
            await update_count(self.redis_welcomes, message)
        except AssertionError:
            pass

    @commands.Cog.listener()
    async def on_member_join(self, joined_member):
        """
        Updates the latest_join key for the given member. This is called by the bot on every member join.
        """
        self.bot.events_hour += 1
        self.bot.events_total += 1
        # check, if welcome features are even enabled
        if not await RedisFlags.get_guild_flag(self.settings_redis, joined_member.guild, RedisFlags.FlagEnum.WELCOME):
            return

        # get some values
        welcome_channel = joined_member.guild.system_channel.id
        last_joined = joined_member.joined_at
        unix_time = time.mktime(last_joined.timetuple())
        guild = joined_member.guild.id

        # assemble the redis key
        key = f"latest_join:{guild}"

        # make a dict containint all the data we want to write
        datadict = dict(
            latest_join=int(unix_time),
            user_id=int(joined_member.id),
            join_channel=int(welcome_channel)
        )

        # write the data
        await self.redis_welcomes.hset(key, mapping=datadict)
        if await RedisFlags.get_guild_flag(self.settings_redis, joined_member.guild, RedisFlags.FlagEnum.WELCOME_MESSAGE):
            await joined_member.guild.system_channel.send("welcome")

    # TODO: honestly, this should just be completely rewritten using a sorted set instead of hashes
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command(name="welcomes")
    async def welcome(self, ctx, *, user: Optional[discord.Member] = None):
        """
        Displays the top 10 users with the most welcome count.
        """

        # get the current time through some really overcomplicated means
        current_time = datetime.utcfromtimestamp(int(time.mktime(ctx.message.created_at.timetuple())))

        # Scan all users in the DB
        # here's a nice one-liner
        key_list = [key async for key in self.redis_welcomes.scan_iter(match=f"leaderboard:*:{ctx.guild.id}")]

        # create an empty dict that will hold all the leaderboard data
        leaderboard = dict()

        # do some very inefficient stuff
        # iterate over every key for every thing because yes
        for i in key_list:
            author = re.findall(r":[\d]{5,}:", i)[0][1:-1]  # extract the author id
            leaderboard[f"<@{author}>"] = await self.redis_welcomes.hgetall(i)
        sorted_lb = sorted(leaderboard.items(), key=lambda x: int(x[1]['welcome_count']), reverse=True)
        
        # display the total leaderboard
        if not user:
            embed = discord.Embed(title="Welcome leaderboard")
            lb_str = ""

            number = 1

            for i in sorted_lb:
                if number <= 10:
                    match number:
                        case 1:
                            number_str = ":first_place: "
                        case 2:
                            number_str = ":second_place: "
                        case 3:
                            number_str = ":third_place: "
                        case _:
                            number_str = "​  **" + str(number) + "**. "
                    delta = (current_time - datetime.utcfromtimestamp(int(i[1]["latest_welcome"])))
                    if delta.days == 1:
                        resp_str = "1 day ago**\n"
                    elif delta.days > 0:
                        resp_str = str(delta.days) + " days ago**\n"
                    else:
                        resp_str = str(delta.seconds // 3600) + " hours ago**\n"
                    lb_str += number_str + str(i[0]) \
                              + " welcomes: **" + str(i[1]["welcome_count"]) + "**, last welcome: **" \
                              + resp_str
                    number += 1
                    continue
            last_join_dict = await self.redis_welcomes.hgetall(f"latest_join:{ctx.message.guild.id}")
            embed.add_field(name=":medal: Top 10:", value=lb_str, inline=False)
            if 'user_id' in last_join_dict:
                delta = (current_time - datetime.utcfromtimestamp(int(last_join_dict['latest_join'])))
                if delta.days == 1:
                    resp_str = "1 day ago**"
                elif delta.days > 0:
                    resp_str = str(delta.days) + " days ago**"
                else:
                    resp_str = str(delta.seconds // 3600) + " hours ago**"
                footer = str(str(f"<@{last_join_dict['user_id']}>")
                             + " joined: **"
                             + resp_str)
                embed.add_field(name=":partying_face: Latest join:", value=footer, inline=False)

        else:
            embed = discord.Embed(title="Personal welcome count") 
            target_user = user.id
            number = 1
            found = False
            for i in sorted_lb:
                if str(target_user) in i[0]:
                    found = True
                    delta = (current_time - datetime.utcfromtimestamp(int(i[1]["latest_welcome"])))
                    if delta.days == 1:
                        resp_str = "1 day ago**\n"
                    elif delta.days > 0:
                        resp_str = str(delta.days) + " days ago**\n"
                    else:
                        resp_str = str(delta.seconds // 3600) + " hours ago**\n"
                    lb_str = "**" + str(number) + "**. " + str(i[0]) \
                              + " welcomes: **" + str(i[1]["welcome_count"]) + "**, last welcome: **" \
                              + resp_str
                    embed.add_field(name=f"{user.display_name}'s welcome count:", value=lb_str, inline=False)
                number += 1
            if not found:
                embed.add_field(name=f"{user.display_name}'s welcome count:", value=f"**∞**. {user.mention} welcomes: **0**, last welcome: **Never**", inline=False)
        await ctx.send(embed=embed)
        
    @commands.is_owner()
    @commands.command(aliases=["ewlb"])
    async def editwelcomelb(self, ctx: commands.Context, user: discord.Member = None, new_value: int = None):
        """
        Edits the welcome leaderboard.
        """
        if user and new_value:
            unix_time = time.mktime(ctx.message.created_at.timetuple())
            key = f"leaderboard:{user.id}:{ctx.guild.id}"
            await self.redis_welcomes.hset(key, "welcome_count", new_value)
            await self.redis_welcomes.hset(key, "latest_welcome", int(unix_time))
            await ctx.send(f"{user.mention}'s welcome count has been set to {new_value}.")
        else:
            await ctx.send(f"Please specify a user and a new value. eg. `{self.bot.command_prefix}ewlb @user 10`")


def setup(bot):
    bot.add_cog(WelcomeCog(bot))
