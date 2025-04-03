#region License
"""
MIT License

Copyright (c) 2019-present The Kitebot Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
#endregion

#region Imports
import os
import re
from typing import Optional
from urllib.parse import urlparse
from urllib.parse import ParseResult

import toml
import discord
from discord.ext import commands
from redis import asyncio as aioredis
import discord_emoji as de

import thatkitebot
from thatkitebot.tkb_redis.settings import RedisFlags
from thatkitebot.tkb_redis.cache import RedisCacheAsync
from thatkitebot.base.util import errormsg
#endregion

# Automatically removed tracking content from links
# and de-ampifies links (not yet implemented) when the setting is turned on

class DetrackView(discord.ui.View):
    @discord.ui.button(label="Close", style=discord.ButtonStyle.red, emoji=de.discord_to_unicode("wastebasket"))
    async def close_button_callback(self, button, interaction: discord.Interaction) -> None:
         pass

#region Cog
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

    @staticmethod
    def get_detrack_aliases() -> list[str]:
        return ["detrack", "det"]   # this is here to make sure we don't detrack our own messages (the first alias is the command name)

    def construct_re(self, data: str, return_pattern = True) -> str:
        # replace parts that are in the LUT
        for key in self.LUT:
            data = data.replace(key, self.LUT[key])
        if return_pattern:
            a = re.compile(data)
            return a
        else:
            return data

    def _remove_tracking(self, url: ParseResult, domain: str) -> ParseResult:
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

    async def raw_detrack_link(self, input_string: str) -> Optional[str]:
        """
        Detracks the link provided. Returns None if the link is not valid.
        """
        url = urlparse(input_string.strip())
        if url.scheme not in ["http", "https"]:
            return None

        # try to match url.netloc to a domain regex
        for domain in self.domains:
            if domain == "global": # skip the global domain for now
                continue
            if self.reassembled_regexes[domain]["netloc"].match(url.netloc):
                url = self._remove_tracking(url, domain)
                return url.geturl().strip('?&;#')

        url = self._remove_tracking(url, "global")
        # return the untracked url
        return url.geturl().strip('?&;#')


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        self.bot.events_hour += 1
        self.bot.events_total += 1
        # Check if the user is a bot 
        if message.author.bot:
            return

        # check if the message starts with our detrack command
        for alias in self.get_detrack_aliases():
            if message.content.startswith(f"{self.bot.command_prefix}{alias}"):
                return        

        # do not detrack in DMs
        if isinstance(message.channel, discord.DMChannel):
            return

        # find all urls in the message
        urls = re.findall(r"(?P<url>https?://\S+)", message.content)
        # remove all whitespaces in the urls
        # urls = list(map(lambda a: a.strip(), urls))
        if not urls:
            return

        # check if detracking is enabled
        if not await RedisFlags.get_guild_flag(self.redis, message.guild, RedisFlags.FlagEnum.DETRACK):
            return

        detracked_strs = []
        for p in urls:
            p = p.strip()
            url = await self.raw_detrack_link(p)
            if url is None:
                continue
            # return the untracked url
            if len(url) + 5 < len(p):
                detracked_strs.append(url)

        # return the detracted message
        if detracked_strs:
            embed = discord.Embed(
                title="I've cleaned tracking links contained in your message!",
                description=
                    " You can find the clean versions below."
                    " You can copy them and edit your original message."
                    " The original author can react with '🗑️' to delete this"
                    "\nThis ~~tape~~ message will self-destruct in 30 seconds."
            )
                  
            clean_links = ""
            for i in detracked_strs:
                clean_links += f"```{i}```\n"
                
            embed.add_field(name="​", value=clean_links)
            embed.set_footer(text="Tip: you can copy the link directly to your clipboard by clicking the icon to the right of the link.")
            my_mgs = await message.reply(embed=embed, silent=True, delete_after=30.0)
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
            cache = RedisCacheAsync(self.bot.redis_cache, self.bot)
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

    @commands.command(aliases=get_detrack_aliases()[1:])
    async def detrack(self, ctx: commands.Context, *, args=""):
        """
        Peroforms detracking on the string provided. Automatically detracks all the links in the string.
        """
        # we need to traverse the message to find all the links, detrack them, and re assemble the message
        message = args

        if len(message) == 0:
            # check if this is a reply
            if ctx.message.reference is not None:
                message = (await self.bot.get_message(ctx.message.reference.message_id)).content
            else:
                await errormsg(ctx, "No message provided.")
                return

        # split the message along the urls
        url_pattern = r'https?://\S+'
        msg_parts = re.split(r'('+url_pattern+')', message)

        if len(msg_parts) == 1:
            await errormsg(ctx, "No valid links found in the message.")
            return
        
        # detrack all the urls
        for i, part in enumerate(msg_parts):
                if re.match(url_pattern, part):
                    # Detrack the url
                    msg_parts[i] = await self.raw_detrack_link(part)
        
        # reassemble the message
        new_msg = "".join(msg_parts)

        # add ``` around the message if it is not a code block
        if not (args.startswith("```") and args.endswith("```")):
            new_msg = f"```{new_msg}```"

        await ctx.send(new_msg)
        return
#endregion        

def setup(bot):
    bot.add_cog(DetrackCog(bot))
