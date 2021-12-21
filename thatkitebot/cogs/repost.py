from discord.ext import commands
from wand.image import Image
import aioredis
import asyncio
import re


class RepostCog(commands.Cog, name="Repost Commands"):
    def __init__(self, bot):
        self.bot = bot
        self.settings_redis = bot.redis
        self.repost_redis = bot.redis_repost

    @commands.Cog.listener()
    async def on_message(self, message):
        print("b")


def setup(bot):
    bot.add_cog(RepostCog(bot))
