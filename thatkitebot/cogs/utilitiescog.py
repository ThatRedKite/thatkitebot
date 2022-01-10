#  Copyright (c) 2019-2022 ThatRedKite and contributors

import discord
from discord.ext import commands
from thatkitebot.backend.util import EmbedColors as ec
import psutil
from datetime import datetime
import si_prefix


class UtilityCommands(commands.Cog, name="utility commands"):
    def __init__(self, bot: commands.Bot):
        self.dirname = bot.dirname
        self.redis = bot.redis
        self.bot = bot

    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command(pass_context=True, aliases=["uptime", "load"])
    async def status(self, ctx):
        """
        Displays the status of the bot.
        """
        process = psutil.Process(self.bot.pid)
        mem = process.memory_info()[0]
        redismem = (await self.redis.info())["used_memory"] + (await self.bot.redis_cache.info())["used_memory"]

        cpu = psutil.cpu_percent(interval=None)
        ping = round(self.bot.latency * 1000, 1)
        uptime = str(datetime.now() - self.bot.starttime).split(".")[0]
        total_users = sum([users.member_count for users in self.bot.guilds])
        guilds = len(self.bot.guilds)

        embed = discord.Embed()
        embed.add_field(name="System status",
                        value=f"""RAM usage: **{si_prefix.si_format(mem + redismem)}B**
                                CPU usage: **{cpu} %**
                                uptime: **{uptime}**
                                ping: **{ping} ms**""")

        embed.add_field(name="Bot stats",
                        value=f"""guilds: **{guilds}**
                                extensions loaded: **{len(self.bot.extensions)}**
                                total users: **{total_users}**
                                bot version: **{self.bot.version}**
                                total command invokes: **{self.bot.command_invokes_total}**
                                commands invoked this hour: **{self.bot.command_invokes_hour}**
                                """, inline=False)

        embed.set_thumbnail(url=str(self.bot.user.avatar.url))

        if not self.bot.debugmode:
            if cpu >= 90.0:
                embed.color = ec.traffic_red
                embed.set_footer(text="Warning: CPU usage over 90%")
            else:
                embed.color = ec.lime_green
        else:
            embed.color = ec.purple_violet
        await ctx.send(embed=embed)

    # TODO: make this command actually do something
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command(pass_context=True)
    async def about(self, ctx):
        pass

    @commands.command()
    async def invite(self, ctx):
        """This sends you an invite for the bot if you want to add it to one of your servers."""
        await ctx.author.send(
            f"https://discord.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=412317247552&scope=bot%20applications.commands"
        )


def setup(bot):
    bot.add_cog(UtilityCommands(bot))
