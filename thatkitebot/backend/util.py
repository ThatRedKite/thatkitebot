#  Copyright (c) 2019-2022 ThatRedKite and contributors

import asyncio
import glob
import os
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
        embed = discord.Embed(title="**ERROR!**", description=msg)
        embed.color = EmbedColors.traffic_red
        embed.set_footer(text=exc)
        await ctx.send(embed=embed, delete_after=5.0)
        await asyncio.sleep(5.0)
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



