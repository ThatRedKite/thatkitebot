#  Copyright (c) 2019-2022 ThatRedKite and contributors

import asyncio
import re

import discord
from discord.ext import commands

from redis import asyncio as aioredis


class EmbedColors:
    blood_orange = 0xe25303
    lime_green = 0x00b51a
    traffic_red = 0xbb1e10
    purple_violet = 0x47243c
    light_grey = 0xc5c7c4
    sulfur_yellow = 0xf1dd38
    ultramarine_blue = 0x00387b
    telemagenta = 0xbc4077
    cum = 0xfbf5e9


def list_chunker(list_to_chunk, size):
    for i in range(0, len(list_to_chunk), size):
        yield list_to_chunk[i:i + size]


def link_from_ids(guild_id: int, channel_id: int, message_id: int):
    return f"https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"


def ids_from_link(url: str) -> (int, int, int):
    """
    Gets the message-, channel- and guild id from a jump url
    """
    split = url.split("/")
    message_id = int(split[-1])
    channel_id = int(split[-2])
    guild_id = int(split[-3])

    return message_id, channel_id, guild_id


async def errormsg(ctx=None, msg: str = "", exc="", embed_only=False):
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


class Parsing:
    @staticmethod
    def check_emoji(emoji):
        emoji_regex = r"<\S+:\d+>"
        if len(emoji) == 1:
            return True
        elif re.match(emoji_regex, emoji):
            return True
        else:
            return False

    @staticmethod
    def preprocessor(a):
        if type(a) is str:
            return a.upper()
        else:
            return a

    @staticmethod
    def parse_arguments_input(a: str):
        """
        Simple function that parses a string to extract values
        """
        s = a.replace("=", " ").split(" ")
        s_dict = dict(zip(s[::2], s[1::2]))
        for key in s_dict.keys():
            old = s_dict[key]
            new = old.replace("v", "").replace("V", "").replace("u", "µ").replace("Ω", "")
            s_dict.update({key: new})
        return s_dict

    @staticmethod
    def slash_command_arguments_parser(a: str):
        """
        Preprocesses a string to be used in a command.
        """
        return a.replace("v", "").replace("V", "").replace("u", "µ").replace("F", "").strip() if a else None


class PermissonChecks:
    @staticmethod
    async def can_change_settings(ctx: commands.Context):
        """
        Checks if the user has the permission to change settings. (Owner and admin)
        """
        channel: discord.TextChannel = ctx.channel
        is_owner = await ctx.bot.is_owner(ctx.author)
        is_admin = channel.permissions_for(ctx.author).administrator
        return is_owner or is_admin

    @staticmethod
    async def mods_can_change_settings(ctx: commands.Context):
        """
        Checks if the user has the permission to change settings. (Mods included)
        """
        key = f"mod_roles:{ctx.guild.id}"
        channel: discord.TextChannel = ctx.channel
        is_owner = await ctx.bot.is_owner(ctx.author)
        is_admin = channel.permissions_for(ctx.author).administrator
        redis: aioredis.Redis = ctx.bot.redis
        is_mod = False
        if ctx.bot.redis:
            pipe = redis.pipeline()
            for role in ctx.author.roles:
                await pipe.sismember(key, role.id)
            is_mod = any(await pipe.execute())
            #await pipe.close()   # why are you like this, redis???
        return is_owner or is_admin or is_mod

    @staticmethod
    def can_send_image(ctx):
        can_attach = ctx.channel.permissions_for(ctx.author).attach_files
        can_embed = ctx.channel.permissions_for(ctx.author).embed_links
        return can_attach and can_embed
