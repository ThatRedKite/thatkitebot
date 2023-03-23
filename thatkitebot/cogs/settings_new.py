import asyncio
from redis import asyncio as aioredis
import discord

from discord.ext import commands, bridge
from thatkitebot.base import util



class SettingsCog(commands.Cog):
    self.bot: discord.Client = bot
    self.redis: aioredis.Redis = self.bot.redis