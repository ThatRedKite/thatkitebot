#region License
"""
MIT License

Copyright (c) 2019-present The Kitebot Team

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
#endregion

#region Imports
import discord

from redis import asyncio as aioredis
from discord.ext import commands

from thatkitebot.base.util import PermissonChecks as pc
#endregion

#region Cog
class SettingsCog(commands.Cog, name="legacy settings"):
    """
    Settings Cog. Allows the bot owner or admins to change settings for their server. All settings are stored in Redis
    and only apply to the server the command was used in. Global settings are not a thing (yet).
    """
    def __init__(self, bot):
        self.bot: discord.Client = bot
        self.redis: aioredis.Redis = self.bot.redis
        self.possible_settings = ["NSFW", "IMAGE", "REPOST", "WELCOME", "UWU"]

    @commands.group(name="setting", aliases=["settings", "set"], hidden=True)
    @commands.check(pc.can_change_settings)
    async def settings(self, ctx):
        """
        This is a command group used to change some bot settings.
        You have to be an Administrator or the bot owner to change use this command group.
        You should use one of the following subcommands: add, list, help.
        """
        pass

    @settings.command(name="add", aliases=["update"], hidden=True)
    @commands.cooldown(3, 10, commands.BucketType.user)
    async def _add(self, ctx: commands.Context):
        """
        This command changes the value of a setting.
        """
        await ctx.send("""
        This command is deprecated, please use the `/settings` slash command group.
        You can use 
        """)
#endregion

def setup(bot):
    bot.add_cog(SettingsCog(bot))
