"""
MIT License

Copyright (c) 2020 ThatRedKite

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import glob
import os
import random
import re
import string

import discord


async def errormsg(ctx, msg: str, exc=""):
    with ctx.channel.typing():
        embed = discord.Embed(title="**ERROR!**", description=msg)
        embed.color = 0xC1121C  # set the color to "traffic red"
        embed.set_footer(text=exc)
    await ctx.send(embed=embed)


def typeguesser(setting, value):
    setting = str(setting).lower()
    value = str(value).lower()

    if len(setting) > 0:
        first = setting[0]

    if first == "i":
        return int(value)

    elif first == "s":
        return str(value)

    elif first == "f":
        return float(value)

    elif first == "b":
        if value in ('yes', 'y', 'true', 't', '1', 'enable', 'on'):
            return True
        elif value in ('no', 'n', 'false', 'f', '0', 'disable', 'off'):
            return False


def mentioner(bot, ctx, message, usermention: str = "", channel_allowed: bool = False):
    is_user = False
    is_channel = False
    user_mentions = message.mentions
    channel_mentions = message.channel_mentions
    if len(user_mentions) > 0:
        # set :chan: to the first user mentioned
        chan = user_mentions[0]
        is_user = True
    elif len(user_mentions) == 0 and len(channel_mentions) > 0 and channel_allowed:
        # set :chan: to the first channel mentioned
        chan = channel_mentions[0]
        is_channel = True
    else:
        rest = re.findall("(\d+)", usermention)
        if len(rest) > 0 and not is_channel:
            is_user = True
            # set :chan: to the user mentioned by id
            chan = bot.get_user(int(rest[0]))
        else:
            chan = ctx.message.author  # set :chan: to the user who issued the command
            is_user = True

    if chan:
        return chan, is_user, is_channel


def bool_parse(boolean):
    if boolean in ('yes', 'y', 'true', 't', '1', 'enable', 'on'):
        return True
    elif boolean in ('no', 'n', 'false', 'f', '0', 'disable', 'off'):
        return False


def randid(len):
    strin = ""
    for x in range(len):
        strin += random.choice(strin.ascii_letters)
    return strin


class colors():
    def __init__(self):
        self.clear = self._cc(0)
        self.bold = self._cc(1)
        self.red = self._cc(31)
        self.green = self._cc(32)
        self.yellow = self._cc(33)
        self.blue = self._cc(34)
        self.magenta = self._cc(35)
        self.cyan = self._cc(36)
        self.grey = self._cc(90)
        self.underlined = self._cc(4)
        self.reverse = self._cc(7)
        self.white = self._cc(97)
        self.background_red = self._cc(41)
        self.background_green = self._cc(42)
        self.background_yellow = self._cc(43)
        self.background_blue = self._cc(44)
        self.background_magenta = self._cc(45)
        self.background_cyan = self._cc(46)

    def multi(self, *args):
        output = ""
        for arg in args:
            output += getattr(self, arg)
        return output

    def _cc(self, code):
        return f"\033[{code}m"

    def __getattr__(self, item):
        return ""


def clear_temp_folder(dirname):
    """
        a simple function to clear the temp data folder of the bot
    """
    cleanupfiles = glob.glob(os.path.join(dirname, "data", "temp", "*.png"))
    cleanupfiles += glob.glob(os.path.join(dirname, "data", "temp", "*.webp"))
    cleanupfiles += glob.glob(os.path.join(dirname, "data", "temp", "*.gif"))
    cleanupfiles += glob.glob(os.path.join(dirname, "data", "temp", "*.mp3"))
    for file in cleanupfiles:
        os.remove(file)
