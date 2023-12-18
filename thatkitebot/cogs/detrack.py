#  Copyright (c) 2019-2023 ThatRedKite and contributors

import os
import re
from urllib.parse import urlparse

import toml
import discord
from discord.ext import commands
from redis import asyncio as aioredis
import discord_emoji as de

import thatkitebot
from thatkitebot.tkb_redis.settings import RedisFlags
from thatkitebot.tkb_redis.cache import RedisCache

# Automatically removed tracking content from links
# and de-ampifies links (not yet implemented) when the setting is turned on

class DetrackView(discord.ui.View):
    @discord.ui.button(label="Close", style=discord.ButtonStyle.red, emoji=de.discord_to_unicode("wastebasket"))
    async def close_button_callback(self, button, interaction: discord.Interaction):
         pass

class DetrackCog(commands.Cog, name="Detrack commands"):
    def __init__(self, bot):
        self.bot: thatkitebot.ThatKiteBot = bot
        self.redis: aioredis.Redis = bot.redis

        with open(os.path.join(bot.data_dir, "detrackparams.toml"), "r") as f:
            # load the detrackparams.toml file to get the detrack settings
            try:
                self.detrack_data = toml.load(f)
                self.domains = self.detrack_data["domains"]
                self.LUT: dict = self.detrack_data["LUT"]
            except toml.decoder.TomlDecodeError:
                print("detrackparams.toml is not valid TOML. Please fix it.")
                return

        self.reassembled_regexes = dict()
        for domain in self.domains:
            new_values = {
                domain: dict(
                    path=self.construct_re(self.domains[domain]["path"]),
                    params=self.construct_re(self.domains[domain]["params"]),
                    netloc=self.construct_re(self.domains[domain]["netloc"]),
                    netloc_dl=self.construct_re(self.domains[domain].get("netloc_dl")) if self.domains[domain].get("netloc_dl") else None,
                    query=self.construct_re(self.domains[domain]["query"]),
                    fragment=self.construct_re(self.domains[domain]["fragment"]),
                    )
                }
            self.reassembled_regexes.update(new_values)

    def construct_re(self, data, return_pattern = True):
        # replace parts that are in the LUT
        for key in self.LUT:
            data = data.replace(key, self.LUT[key])
        if return_pattern:
            a = re.compile(data)
            return a
        else:
            return data

    def _remove_tracking(self, url, domain):
        netloc_pattern: re.Pattern = self.reassembled_regexes[domain]["netloc"]
        if netloc_pattern.match(self.construct_re(url.netloc, return_pattern=False)):
            # if netloc_dl is set, remove the netloc regex matches
            if "netloc_dl" in self.domains[domain]:
                pattern: re.Pattern = self.reassembled_regexes[domain]["netloc_dl"]
                url = url._replace(netloc=pattern.sub("", url.netloc))

            path_pattern: re.Pattern = self.reassembled_regexes[domain]["path"]
            url = url._replace(path=path_pattern.sub("", url.path))

            params_pattern: re.Pattern = self.reassembled_regexes[domain]["params"]
            url = url._replace(params=params_pattern.sub("", url.params))

            query_pattern: re.Pattern = self.reassembled_regexes[domain]["query"]
            url = url._replace(query=query_pattern.sub("", url.query))

            fragment_pattern: re.Pattern = self.reassembled_regexes[domain]["query"]
            url = url._replace(fragment=fragment_pattern.sub("", url.fragment))
        return url

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        self.bot.events_hour += 1
        self.bot.events_total += 1

        # Check if the user is a bot 
        if message.author.bot:
            return

        # do not detrack in DMs
        elif isinstance(message.channel, discord.DMChannel):
            return

        # find all urls in the message
        urls = re.findall(r"(?P<url>https?://\S+)", message.content)
        # remove all whitespaces in the urls
        # urls = list(map(lambda a: a.strip(), urls))
        if not urls:
            return

        # check if detracking is enabled
        if not await RedisFlags.get_guild_flag(self.redis, message.guild, RedisFlags.DETRACK):
            return

        detracked_strs = []
        for p in urls:
            url = urlparse(p.strip())
            if url.scheme not in ["http", "https"]:
                return
                # check if we match a domain
            if (domain := url.netloc.split(".")[-2]) in self.domains.keys():
                url = self._remove_tracking(url, domain)

            url = self._remove_tracking(url, "global")
            # return the untracked url
            if len(url.geturl()) + 5 < len(p):
                detracked_strs.append(url.geturl().strip('?&;#'))

        # return the detracted message
        if detracked_strs:
            embed = discord.Embed(title="I've cleaned tracking links contained your message!", description="You can find the clean versions below. You can copy them and edit your original message. The original author can react with '🗑️' to delete this.")
            clean_links = ""
            for i in detracked_strs:
                clean_links += f"```{i}```\n"
                
            embed.add_field(name="​", value=clean_links)
            embed.set_footer(text="Tip: you can copy the link directly to your clipboard by clicking on the right side of the link")
            my_mgs = await message.reply(embed=embed, silent=True)
            await my_mgs.add_reaction("🗑️")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        self.bot.events_hour += 1
        self.bot.events_total += 1

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
            cache = RedisCache(self.bot.redis_cache, self.bot)
            author_id = await cache.get_author_id(message.reference.message_id)
            if author_id is None:
                author_id = (await self.bot.get_channel(payload.channel_id).fetch_message(message.reference.message_id)).author.id

        except discord.errors.NotFound:
            # if the message is not found, we delete our message regardless of who reacted
            author_id = payload.user_id

        # if the author of the message is the same as the user who reacted to the message
        if payload.user_id == author_id:
            # delete the message
            await message.delete()


def setup(bot):
    bot.add_cog(DetrackCog(bot))
