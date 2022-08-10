#  Copyright (c) 2019-2022 ThatRedKite and contributors

import discord
import aioredis
from discord.ext import commands, tasks
from discord.ext.commands.errors import CommandInvokeError
from thatkitebot.backend.util import errormsg
from thatkitebot.backend import cache


class ListenerCog(commands.Cog):
    """
    The perfect place to put random listeners in.
    """
    def __init__(self, bot):
        self.dir_name = bot.dir_name
        self.redis_cache: aioredis.Redis = bot.redis_cache
        self.redis_welcomes: aioredis.Redis = bot.redis_welcomes
        self.repost_redis: aioredis.Redis = bot.redis_repost
        self.bot: discord.Client = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: CommandInvokeError):
        match type(error):
            case commands.CommandOnCooldown:
                await errormsg(ctx, f"Sorry, but this command is on cooldown! Please wait {int(error.retry_after)} seconds.")
            case commands.CommandInvokeError:
                if self.bot.debug_mode:
                    await errormsg(ctx, repr(error))
                raise error
            case commands.CheckFailure:
                await errormsg(ctx, "A check has failed! This command might be disabled on the server or you lack permission")
            case commands.MissingPermissions:
                await errormsg(ctx, "Sorry, but you don't have the permissions to do this")
            case commands.NotOwner:
                await errormsg(ctx, f"Only the bot owner can do this! Contact them if needed.")

    @tasks.loop(hours=1.0)
    async def reset_invoke_counter(self):
        self.bot.command_invokes_hour = 0

    @commands.Cog.listener()
    async def on_ready(self):
        print("\nbot successfully started!")
        self.reset_invoke_counter.start()
        await self.bot.change_presence(
            activity=discord.Activity(name="a battle against russia", type=5),
            status=discord.Status.online,
        )

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        self.bot.command_invokes_hour += 1
        self.bot.command_invokes_total += 1

    @commands.Cog.listener()
    async def on_slash_command_error(self, ctx, ex):
        raise ex

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        try:
            await cache.add_message_to_cache(self.redis_cache, message)
        except:
            print("could not add message to cache!")


def setup(bot):
    bot.add_cog(ListenerCog(bot))
