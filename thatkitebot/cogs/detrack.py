#  Copyright (c) 2019-2022 ThatRedKite, diminDDL and contributors
import discord
import aioredis
import thatkitebot
import json
import os
import re
import toml
from urllib.parse import urlparse, parse_qs, urlencode
from discord.ext import commands, bridge
from thatkitebot.cogs.settings import mods_can_change_settings

# Automatically removed tracking content from links and de-ampifies links when the setting is turned on
class DetrackCog(commands.Cog, name="Detrack commands"):
    def __init__(self, bot):
        self.bot: thatkitebot.ThatKiteBot = bot
        self.redis: aioredis.Redis = bot.redis
        with open(os.path.join(bot.data_dir, "detrackparams.toml"), "r") as f:
            try:
                self.detrack_data = toml.load(f)
                self.doms = self.detrack_data["domains"]
                self.LUT = self.detrack_data["LUT"]
            except toml.decoder.TomlDecodeError:
                print("detrackparams.toml is not valid toml. Please fix it.") 

    def construct_re(self, data):
        # replace parts that are in the LUT
        for key in self.LUT:
            data = data.replace(key, self.LUT[key])
        return data

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
            # remove all whitespaces in the urls
            urls = [url.strip() for url in urls]
            if not urls:
                return
            for p in urls:
                url = urlparse(p)
                if url.scheme in ["http", "https"]:
                    # check if we match a domain
                    for domain in self.doms:
                        if domain == "LUT":
                            continue
                        # check if the netloc regex matches
                        if re.match(self.construct_re(self.doms[domain]["netloc"]), self.construct_re(url.netloc)):
                            # if netloc_dl is set, remove the netloc regex mathes
                            if "netloc_dl" in self.doms[domain]:
                                url = url._replace(netloc=re.sub(self.construct_re(self.doms[domain]["netloc_dl"]), '', url.netloc))
                            # remove the path regex mathes
                            url = url._replace(path=re.sub(self.construct_re(self.doms[domain]["path"]), '', url.path))
                            # remove the params regex mathes
                            url = url._replace(params=re.sub(self.construct_re(self.doms[domain]["params"]), '', url.params))
                            # remove the query regex mathes
                            url = url._replace(query=re.sub(self.construct_re(self.doms[domain]["query"]), '', url.query))
                            # remove the fragment regex mathes
                            url = url._replace(fragment=re.sub(self.construct_re(self.doms[domain]["fragment"]), '', url.fragment))
                # return the untracked url
                if len(url.geturl()) + 5 < len(p):
                    detracked_strs.append(url.geturl().strip('?&;#'))
        else:
            return
        # return the detracted message
        if detracked_strs:
            message_str = "Tracking/mobile links detected, below are the sanitized links. OP can press 🗑️ to remove this message\n"
            for i in detracked_strs:
                message_str += f"<{i}>\n"
            my_mgs = await message.reply(message_str)
            await my_mgs.add_reaction("🗑️")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        # check if the bot is reacting to the message
        if payload.user_id == self.bot.user.id:
            return
        # check if the reaction is a trash can
        if payload.emoji.name != "🗑️":
            return
        # check if the bot also added the trash can reaction
        message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
        if self.bot.user not in await message.reactions[0].users().flatten():
            return
        
        try:
            author = (await self.bot.get_channel(payload.channel_id).fetch_message(message.reference.message_id)).author.id
        except discord.errors.NotFound:
            # if the message is not found, we delete our message regardless of who reacted
            author = payload.user_id
        # if the author of the message is the same as the user who reacted to the message
        if payload.user_id == author:
            # delete the message
            await message.delete()
        

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