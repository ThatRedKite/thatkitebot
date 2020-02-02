from discord.ext import commands
import discord

class Listeners(commands.Cog):
   def __init__(self, bot, dirname):
      self.bot = bot
      self._last_member = None
      self.dirname = dirname

   @commands.Cog.listener()
   async def on_member_join(self, member):
        guild = member.guild
        if guild.system_channel is not None:
            to_send = 'Welcome {0.mention} to {1.name}! Please behave like a normal human being!'.format(member, guild)
            await guild.system_channel.send(to_send)
