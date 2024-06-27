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
from discord.ext import commands

from thatkitebot import ThatKiteBot
from thatkitebot.base.exceptions import *
#endregion

#region Functions
def some_function() -> None:
    pass
#endregion

#region Cog
class CogName(commands.Cog, name="Cog Name"): #replace with actual name
    def __init__(self, bot: ThatKiteBot):
        self.bot = bot
        self.redis = bot.redis

    #region Methods

    async def some_method(self) -> None:
        pass
    #endregion

    #region command groups

    # command groups here 
    command_group = discord.SlashCommandGroup("example", "Change This")

    #endregion

    #region Commands
    @command_group.command(name="command", description="This is an example command")
    async def _example(self, ctx: discord.ApplicationContext):
        pass
    
    #endregion

    #region Listeners
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        pass
    #endregion
#endregion

def setup(bot: ThatKiteBot):
    #replace with actual name
    bot.add_cog(CogName(bot))