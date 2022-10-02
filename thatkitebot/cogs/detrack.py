#  Copyright (c) 2019-2022 ThatRedKite, diminDDL and contributors

from tkinter import HIDDEN
import discord
import aioredis
import thatkitebot
import json
import os
import re
from urllib.parse import urlparse
from discord.ext import commands, bridge
from thatkitebot.cogs.settings import mods_can_change_settings

# Automatically removed tracking content from links and de-ampifies links when the setting is turned on
class DetrackCog(commands.Cog, name="Detrack commands"):
    def __init__(self, bot):
        self.bot: thatkitebot.ThatKiteBot = bot
        self.redis: aioredis.Redis = bot.redis
        # this seems like a bad idea, maybe move it to __main__.py?
        with open(os.path.join(bot.data_dir, "detrackparams.json"), "r") as f:
            try:
                self.detrack_data = json.load(f)
            except json.decoder.JSONDecodeError:
                print("detrackparams.json is not valid json. Please fix it.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Check if the user is a bot 
        if message.author.bot:
            return

        #print(self.detrack_data["categories"][0]["name"])

        key = f"detrack:{message.guild.id}"

        if await self.redis.exists(key):
            # find all urls in the message
            urls = re.findall(r"(?P<url>https?://[^\s]+)", message.content)
            if not urls:
                return
            for p in urls:
                url = urlparse(p)
                domain = url.hostname
                print(domain)
                #check if domain has subdomains
                subs = domain.split(".")
                for sub in subs:
                    print(sub)
        else:
            return

    @commands.check(mods_can_change_settings)
    @bridge.bridge_command(name="detrack", aliases=["urlclean"],
                           description="Remove known tracking urls and de-ampify links")
    async def add_detrack_setting(self, ctx: commands.Context):
        """
        Remove known tracking urls and de-ampify links.
        For example: https://www.youtube.com/watch?&v=dQw4w9WgXcQ&feature=youtu.be will become https://www.youtube.com/watch?v=dQw4w9WgXcQ
        
        The way this works is that the original users message is removed and reposed by the bot as an embed, with a button to restore the ordinal message.
        But since discord can't undelete message it will create a "clone" of the original message using webhooks.

        This setting is off by default.

        Usage: 
        `+detrack` - toggles the setting server wide
               
        Only administrators and moderators can use this command.
        """

        if not await mods_can_change_settings(ctx):
            return await ctx.respond("You don't have permission to change settings.")
        
        key = f"detrack:{ctx.guild.id}"
        if await self.redis.exists(key) == 0:
            await self.redis.sadd(key, "1")
            await ctx.respond(f"Detrack has been enabled.")
        else:
            try:
                await self.redis.delete(key)
            except aioredis.ResponseError:
                await ctx.respond(f"Detrack was off.")
                return

            await ctx.respond(f"Detrack has been disabled.")


def setup(bot):
    bot.add_cog(DetrackCog(bot))