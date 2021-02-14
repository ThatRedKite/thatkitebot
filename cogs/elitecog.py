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
from backend import elitedangerous

class EliteDangerous(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = self.bot.aiohttp_session
        self.last_system_by_user = {}

    @commands.command(name="deaths",aliases=["d"], pass_context=True)
    async def _get_deaths(self,ctx, *, sysname: str=""):
        uid = ctx.author.id
        if sysname:
            embed, system_name= await elitedangerous.get_deaths(self.session, sysname)
            self.last_system_by_user.update({uid:system_name})
        else:
            try:
                last_system=self.last_system_by_user.get(uid)
                embed = await elitedangerous.get_deaths(session=self.session,sysname=last_system,return_sysname=False)

            except TypeError:
                pass

        await ctx.send(embed=embed)

    @commands.command(name="traffic",aliases=["tr"], pass_context=True)
    async def _traffic_report(self,ctx, *, sysname: str=""):
        uid = ctx.author.id
        if sysname:
            embed, system_name= await elitedangerous.traffic_report(self.session, sysname)
            self.last_system_by_user.update({uid:system_name})
        else:
            try:
                last_system=self.last_system_by_user.get(uid)
                embed = await elitedangerous.traffic_report(session=self.session,sysname=last_system,return_sysname=False)

            except TypeError:
                pass

        await ctx.send(embed=embed)


    @commands.command(name="soldistance",aliases=["dts"], pass_context=True)
    async def _get_distance_to_sol(self, ctx, *, sysname: str=""):
        uid = ctx.author.id
        if sysname:
            embed = await elitedangerous.get_distance_to_sol(self.session, sysname)
            self.last_system_by_user.update({uid: sysname})
        else:
            try:
                last_system=self.last_system_by_user.get(uid)
                embed = await elitedangerous.get_distance_to_sol(session=self.session, sysname=last_system)

            except TypeError:
                pass

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(EliteDangerous(bot))

