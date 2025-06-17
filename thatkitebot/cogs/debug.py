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
import gc

import discord
from discord.ext import commands

import wand
import wand.resource

from thatkitebot.base.exceptions import *
#endregion

#region Functions
def some_function() -> None:
    pass
#endregion

#region Cog
class CogName(commands.Cog, name="Cog Name"): #replace with actual name
    def __init__(self, bot):
        self.bot = bot
        self.redis = bot.redis


    #region command groups
    dbg = discord.SlashCommandGroup("debug", "Debug Commands", guild_ids=[759419755253465188])
    #endregion


    #region Commands

    @commands.is_owner()
    @dbg.command(name="gc")
    async def _garbage_test(self, ctx: discord.ApplicationContext):
        await ctx.send_response(str(gc.collect()), ephemeral=True)

    @commands.is_owner()
    @dbg.command(name="wand_resources")
    async def _imagemagick_memory_stats(self, ctx: discord.ApplicationContext):
        b = "ImageMagick Resources\n```"
        for resource in wand.resource.limits.limits:
            if resource in ("memory", "map", "disk"):
                b += f"{resource}: {wand.resource.limits.resource(resource) / 1048576}/{wand.resource.limits[resource] / 1048576} MiB\n"
            else:
                b += f"{resource}: {wand.resource.limits.resource(resource)}/{wand.resource.limits[resource]}\n"

        b += "```"
        await ctx.respond(b, ephemeral=True)
        print(b)

    @commands.is_owner()
    @dbg.command(name="wand_cleanup")
    async def _error_test_slash(self, ctx: discord.ApplicationContext):
       wand.resource.shutdown()

    @commands.is_owner()
    @dbg.command(name="test_error")
    async def _error_test(self, ctx: discord.ApplicationContext):
        raise commands.CommandError
    

    #endregion

    #region Listeners

    #endregion

#endregion


#region Setup
def setup(bot):
    #replace with actual name
    if bot.debug_mode:
        bot.add_cog(CogName(bot))
#endregion
