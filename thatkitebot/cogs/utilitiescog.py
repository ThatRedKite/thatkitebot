# ------------------------------------------------------------------------------
#  MIT License
#
#  Copyright (c) 2019-2021 ThatRedKite
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
from thatkitebot.backend import misc as back
from thatkitebot.backend.util import EmbedColors as ec


class UtilityCommands(commands.Cog, name="utility commands"):
    def __init__(self, bot: commands.Bot):
        self.dirname = bot.dirname
        self.bot = bot

    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command(pass_context=True, aliases=["uptime", "load"])
    async def status(self, ctx):
        """
        Bot's Current Status
        """
        async with ctx.typing():
            mem, cpu, cores_used, cores_total, ping, uptime = await back.get_status(self.bot.pid, self.bot)
            total_users = sum([users.member_count for users in self.bot.guilds])
            guilds = len(self.bot.guilds)
            embed = discord.Embed()
            embed.add_field(name="System status",
                            value=f"""RAM usage: **{mem} Mb**
                                    CPU usage: **{cpu} %**
                                    core affinity: **{cores_used}/{cores_total}**
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
                else: embed.color = ec.lime_green
            else:embed.color = ec.purple_violet
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
            f"https://discord.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=412317247552&scope=bot"
        )


def setup(bot):
    bot.add_cog(UtilityCommands(bot))
