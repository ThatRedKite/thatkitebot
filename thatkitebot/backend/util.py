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


import glob
import os
import random
import re
import discord


class EmbedColors:
    blood_orange = 0xe25303
    lime_green = 0x00b51a
    traffic_red = 0xbb1e10
    purple_violet = 0x47243c
    light_grey = 0xc5c7c4
    sulfur_yellow = 0xf1dd38
    ultramarine_blue = 0x00387b
    telemagenta = 0xbc4077


async def errormsg(ctx=None, msg: str="", exc="", embed_only=False):
    if not embed_only:
        with ctx.channel.typing():
            embed = discord.Embed(title="**ERROR!**", description=msg)
            embed.color = EmbedColors.traffic_red
            embed.set_footer(text=exc)
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="**ERROR!**", description=msg)
        embed.color = EmbedColors.traffic_red
        embed.set_footer(text=exc)
        return embed


def clear_temp_folder(dirname):
    """
        a simple function to clear the temp data folder of the bot
    """
    cleanupfiles = glob.glob(os.path.join(dirname, "*.png"))
    cleanupfiles += glob.glob(os.path.join(dirname, "*.webp"))
    cleanupfiles += glob.glob(os.path.join(dirname, "*.gif"))
    cleanupfiles += glob.glob(os.path.join(dirname, "*.mp3"))
    for file in cleanupfiles:
        os.remove(file)



