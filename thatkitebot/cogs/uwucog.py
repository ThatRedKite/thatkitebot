from ast import alias
import re

import aioredis
import discord
from discord.ext import commands, bridge
from thatkitebot.cogs.settings import can_change_settings


async def uwuify(message: str):
    trans_table = message.maketrans({"l": "w", "L": "W", "r": "w", "R": "W"})
    return message.replace('na', 'nya').translate(trans_table).replace("no", "yo").replace("mo", "yo").lower()+' uwu'

# Yes this definately needs its own cog shut the fuck up kite (Jk I love you)
class UwuCog(commands.Cog, name="UwU Commands"):
    def __init__(self, bot):
        self.bot = bot
        self.redis: aioredis.Redis = bot.redis
        
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Check if the user is a bot 
        if message.author.bot:
            return

        # Check if the message is in an UwU channel
        if not await self.redis.sismember(f"uwu_channels:{message.guild.id}", message.channel.id):
            return

        # Carter's code (Updated)
        if not message.webhook_id:
            await message.delete()

            webhooks = await message.channel.webhooks()
            webhook = next((hook for hook in webhooks if hook.name == "uwuhook"), None)

            if not webhook:
                webhook = await message.channel.create_webhook(name='uwuhook', reason='uwuhook is for uwu channel uwu')

            await webhook.send(content=await uwuify(message.content),
                               username=message.author.display_name,
                               avatar_url=message.author.avatar.url)
    
    # Sorry mom
    @commands.check(can_change_settings)
    @bridge.bridge_command(name="uwu_channel", aliases=["uwuchannel", "uwuch"],
                           description="Make a channel automatically UwU every message")
    async def add_uwu_channel(self, ctx: bridge.BridgeContext, channel: discord.TextChannel, add: bool = True):
        if not can_change_settings(ctx):
            return await ctx.respond("You don't have permission to change settings.")
        
        key = f"uwu_channels:{ctx.guild.id}"
        if add:
            await self.redis.sadd(key, channel.id)
            await ctx.respond(f"{channel.mention} is now an UwU channel.")
        else:
            try:
                await self.redis.srem(key, channel.id)
            except aioredis.ResponseError:
                await ctx.respond(f"{channel.mention} is not an UwU channel.")
                return

            await ctx.respond(f"{channel.mention} is no longer an UwU channel.")

def setup(bot):
    bot.add_cog(UwuCog(bot))
