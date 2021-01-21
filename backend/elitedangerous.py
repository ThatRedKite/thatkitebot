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

import aiohttp
import discord
from .util import errormsg, EmbedColors


async def get_deaths(session:aiohttp.ClientSession,sysname:str,return_sysname=True):
    payload = dict(systemName=sysname)
    async with session.get(url="https://www.edsm.net/api-system-v1/deaths", params=payload) as r:
        if r.status == 200:
            response_dict = await r.json()
            try:
                sysname = response_dict.get("name")
                today = response_dict.get("deaths")["day"]
                total = response_dict.get("deaths")["total"]
                week = response_dict.get("deaths")["week"]
            except TypeError:
                return await errormsg(msg="Cannot process the data. Your system name might be wrong", embed_only=True), None

            embed = discord.Embed(
                title=f"Death statistics for *{sysname}*",
                description=f"Today:**{today}**\nThis week:**{week}**\nTotal:**{total}**"
            )

            embed.color = EmbedColors.lime_green
            if return_sysname: return embed,sysname
            else: return embed

        else:
            return await errormsg(msg="Cannot connect to the EDSM API. Is it down?",embed_only=True), None


async def traffic_report(session:aiohttp.ClientSession,sysname:str,return_sysname=True):
    payload = dict(systemName=sysname)
    async with session.get(url="https://www.edsm.net/api-system-v1/traffic", params=payload) as r:
        if r.status == 200:
            report = await r.json()
            try:
                sysname = report.get("name")
                today = report.get("traffic")["day"]
                total = report.get("traffic")["total"]
                week = report.get("traffic")["week"]

                breakdown_string = ""
                for entry in report.get("breakdown"):
                    breakdown_string += f"""{entry}: **{report["breakdown"][entry]}**\n"""

                embed = discord.Embed(
                    title=f"Traffic report for *{sysname}*",
                    description=f"Today:`{today}`\nThis week:`{week}`\nTotal:`{total}`"
                )

                embed.add_field(name="Breakdown:", value=breakdown_string, inline=False)

            except TypeError:
                return await errormsg(msg="Cannot process the data. Your system name might be wrong", embed_only=True), None

            embed.color = EmbedColors.lime_green
            if return_sysname: return embed,sysname
            else: return embed

        else:
            return await errormsg(msg="Cannot connect to the EDSM API. Is it down?",embed_only=True), None
