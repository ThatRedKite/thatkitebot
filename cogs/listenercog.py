#  MIT License
#
#  Copyright (c) 2020 ThatRedKite
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

#  MIT License
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#
#

import random
from datetime import datetime
import discord
from discord.enums import Status
from discord.ext import commands, tasks
from discord.ext.commands.errors import CommandInvokeError
from backend.util import colors
from backend.util import errormsg


class listeners(commands.Cog):
    def __init__(self, bot, dirname, ):
        self.dirname = dirname
        self.bot: discord.Client = bot
        self.colors = colors()

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: CommandInvokeError):
        if isinstance(error, commands.CommandNotFound):
            await errormsg(ctx, f"unknown command | do `{ctx.prefix}help` in order to see what i can do")
        elif isinstance(error, commands.CommandOnCooldown):
            await errormsg(ctx, "Sorry, but this command is on cooldown! Try again in a few seconds.")
        elif isinstance(error, CommandInvokeError) and self.bot.debugmode:
            await errormsg(ctx, str(error))
            await errormsg(ctx, str(error.original))
            raise error
        else:
            raise error

    @tasks.loop(minutes=5.0)
    async def statuschange(self):
        ontime = datetime.now() - self.bot.starttime
        times = str(ontime).split(".")

        possible_status = [
            (Status.idle, "nothing"),
            (Status.online, "with code"),
            (Status.online, f"{self.bot.command_prefix}help"),
            (Status.online, f"uptime:    {times[0]}"),
            (Status.dnd, "with trains"),
            (Status.dnd, "with myself"),
            (Status.online, "games"),
            (Status.online, "dead"),
            (Status.online, "catch with myself"),
            (Status.online, f"Python 3.{random.randint(5, 9)}"),
            (Status.online, "a cool game"),
            (Status.online, "chess"),
            (Status.online, f"Fallout {random.randint(1, 4)}"),
            (Status.online, "gecko eating contest"),
            (Status.online, "K.I.T.E The Game")
        ]

        chosen_status, chosen_message = random.choice(possible_status)
        await self.bot.change_presence(status=chosen_status, activity=discord.Game(chosen_message))

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"\nbot successfully started!")
        await self.bot.change_presence(status=discord.Status.dnd, activity=discord.Game("booting"))
        self.statuschange.start()
