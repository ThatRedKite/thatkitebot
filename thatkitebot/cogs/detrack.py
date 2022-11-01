#  Copyright (c) 2019-2022 ThatRedKite, diminDDL and contributors
import discord
import aioredis
import thatkitebot
import json
import os
import re
from urllib.parse import urlparse, parse_qs, urlencode
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

    def process_domain_specific(self, filter, query):
        if "*" in filter:
            # wildcard filter
            for k in list(query):
                if filter.strip("*") in k:
                    query.pop(k)
        else:
            if filter in query:
                query.pop(filter)
        # now reconstruct the url
        return query

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Check if the user is a bot 
        if message.author.bot:
            return

        key = f"detrack:{message.guild.id}"

        detracked_strs = []
        if await self.redis.exists(key):
            # find all urls in the message
            urls = re.findall(r"(?P<url>https?://[^\s]+)", message.content)
            if not urls:
                return
            for p in urls:
                url = urlparse(p)
                if url.scheme in ["http", "https"] and url.query != "":
                    domain = url.hostname
                    #check if domain has subdomains
                    subs = domain.split(".")
                    for category in self.detrack_data["categories"]:
                        rawFilter = category["params"]
                        for rF in rawFilter:
                            # parse the filter string into separate variables, @ - domain specific, * - wildcard
                            if "@" in rF:
                                filter = rF.split("@")[0]
                                for_domain = rF.split("@")[1]
                                if "*" in for_domain:
                                    if for_domain.strip("*").strip(".") in domain:
                                        # now we parse the query to detrack it
                                        query = parse_qs(url.query, keep_blank_values=True)
                                        query = self.process_domain_specific(filter, query)
                                        # now reconstruct the url
                                        url = url._replace(query=urlencode(query, True))
                                else:
                                    if for_domain == domain.strip("www."):
                                        # now we parse the query to detrack it
                                        query = parse_qs(url.query, keep_blank_values=True)
                                        query = self.process_domain_specific(filter, query)
                                        # now reconstruct the url
                                        url = url._replace(query=urlencode(query, True))
                            else:
                                # if we landed here means we need to apply the filter to all domains
                                filter = rF
                                if "*" in filter:
                                    # wildcard filter
                                    query = parse_qs(url.query, keep_blank_values=True)
                                    for k in list(query):
                                        if filter.strip("*") in k:
                                            query.pop(k)
                                    # now reconstruct the url
                                    url = url._replace(query=urlencode(query, True))
                                else:
                                    query = parse_qs(url.query, keep_blank_values=True)
                                    if filter in query:
                                        query.pop(filter)
                                    # now reconstruct the url
                                    url = url._replace(query=urlencode(query, True))
                # return the untracked url
                if url.geturl() != p:
                    detracked_strs.append(url.geturl())
        else:
            return
        # return the detracted message
        if detracked_strs:
            #embed = discord.Embed()
            #embed.add_field(name="Auto link Detrack", value="Tracking links were detected, below are the detracked versions of the links.", inline=False)
            message_str = "Tracking links were detected, below are the detracked versions of the links.\n"
            for i in detracked_strs:
                #embed.add_field(name="​", value=i, inline=False)
                message_str += f"<{i}>\n"
            #await message.reply(embed=embed)
            await message.reply(message_str)

    @commands.check(mods_can_change_settings)
    @bridge.bridge_command(name="detrack", aliases=["urlclean"],
                           description="Remove known tracking urls and de-ampify links")
    async def set_auto_detrack(self, ctx: commands.Context):
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
        if not await self.redis.exists(key):
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