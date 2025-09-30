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
import re
import io
import textwrap
import asyncio

from typing import Union
import discord

from unidecode import unidecode
from uwuipy import uwuipy
from discord import abc
from discord.ext import commands, tasks
from redis import asyncio as aioredis

import thatkitebot
from thatkitebot.base.url import get_avatar_url
from thatkitebot.base.util import PermissonChecks as pc
from thatkitebot.base.util import set_up_guild_logger
from thatkitebot.tkb_redis.settings import RedisFlags
from thatkitebot.types.message import Message
#endregion


#region Functions
def uwuify(message: str, id: int, intensity: float = 1.0, enable_nsfw = False):
    # initialize the uwuipy class, multiplying the default intensites by :intensity:
    uwu = uwuipy(id, *map(lambda m: (m * intensity), (0.1, 0.05, 0.0075)), 1.0, nsfw_actions=enable_nsfw)
    message = uwu.uwuify(message)

    return message

def uwuify_embeds(message: Message, id: int, intensity: float = 1.0, enable_nsfw = False) -> list[discord.Embed]:
    uwu = uwuipy(id, *map(lambda m: (m * intensity), (0.1, 0.05, 0.0075)), 1.0, nsfw_actions=enable_nsfw)
    embeds = []
    for embed in message.embeds:
        match embed.type:
            # ignore embeds that just contain media
            case "image" | "gifv" | "youtube":
                embeds.append(embed)

            # bot rich embeds often contain fields and footers which will need to be uwuified as well
            case "rich":
                fields = []

                for field in embed.fields:
                    uwu_field = discord.EmbedField(
                        name = uwu.uwuify(field.name),
                        value = uwu.uwuify(field.value),
                        inline=field.inline
                    )
                    fields.append(uwu_field)

                footer = None
                if embed.footer:
                    footer = discord.EmbedFooter(
                        text = uwu.uwuify(embed.footer.text),
                        icon_url=embed.footer.icon_url
                    )

                uwu_rich = discord.Embed(
                    title=uwu.uwuify(embed.title) if embed.title else None,
                    description=uwu.uwuify(embed.description) if embed.description else None,
                    image=embed.image,
                    thumbnail=embed.thumbnail,
                    url=embed.url,
                    fields=fields,
                    footer=footer,
                    type="rich",
                    color=embed.color,
                    timestamp=embed.timestamp
                )
                
                if embed.author:
                    # uwuify the author, if present
                    uwu_rich.set_author(
                        name=uwu.uwuify(embed.author.name),
                        url=embed.author.url,
                        icon_url=embed.author.icon_url
                    )

                embeds.append(uwu_rich)

            case "article" | "link":
                uwu_article = discord.Embed(
                    title=uwu.uwuify(embed.title),
                    description=uwu.uwuify(embed.description),
                    image=embed.thumbnail if embed.thumbnail else None,
                    url=embed.url if embed.url else None,
                    color=embed.color,
                    type="article"
                )
                if embed.provider:
                    uwu_article.set_author(name=uwu.uwuify(embed.provider.name), url=embed.provider.url)
                embeds.append(uwu_article)

            case _:
                raise
    return embeds
                
#endregion

#region Cog
class UwuCog(commands.Cog, name="UwU Commands"):
    def __init__(self, bot):
        self.bot: thatkitebot.ThatKiteBot = bot
        self.redis: aioredis.Redis = bot.redis
        self.webhooks = {}


    @tasks.loop(hours=1)
    async def clear_webhook_cache(self):
        self.webhooks.clear()

    #region private methods
    async def _uwu_enabled(self, ctx):
        return await RedisFlags.get_guild_flag(self.redis, ctx.guild, RedisFlags.FlagEnum.UWU)
    
    async def _change_uwu_status(self, ctx:discord.ApplicationContext, to_change: Union[abc.GuildChannel, discord.User, discord.Member], intensity: float) -> bool:
        logger = set_up_guild_logger(ctx.guild.id)

        # make sure none of the IDs are 0
        assert to_change.id != 0 and ctx.guild.id != 0

        if isinstance(to_change, abc.GuildChannel):
            key = f"uwu_channels:{ctx.guild.id}"
            symbol = "#"
            int_key = f"c:{to_change.id}"

        elif isinstance(to_change, abc.User):
            key = f"uwu_users:{ctx.guild.id}"
            symbol = "@"
            int_key = f"u:{to_change.id}"

        else:
            raise ValueError
        
        # try to remove the user from the list and see if it was successful
        if await self.redis.srem(key, to_change.id) == 0:
            # if unsuccessful, the user was not in the list, so we add them
            await self.redis.sadd(key, to_change.id)
            if intensity != 1.0:
                # set the intensity
                await self.redis.hset(f"uwui:{ctx.guild.id}", int_key, intensity)
            logger.info(f"UWU: {ctx.author.name} uwuified {symbol}{to_change.name} in '{ctx.guild.name}'")
            return False
        
        else:
            # if successful, do nothing but resetting the intensity and logging, we already removed the thing from the list
            await self.redis.hdel(f"uwui:{ctx.guild.id}", int_key)
            logger.info(f"UWU: {ctx.author.name} de-uwuified {symbol}{to_change.name} in '{ctx.guild.name}'")
            return True

    async def _listener_checks(self, message):
        if not await self._uwu_enabled(message):
            return False

        # check if message is in an uwu channel
        is_channel = await self.redis.sismember(f"uwu_channels:{message.guild.id}", str(message.channel.id))
        is_user = await self.redis.sismember(f"uwu_users:{message.guild.id}", str(message.author.id))

        #if not (is_user and is_channel):
        #    return False

        return is_user or is_channel
    
    async def get_uwu_webhook(self, webhook_id, channel: discord.TextChannel) -> Union[discord.Webhook, None]:
        # try to get cached webhook
        if (uwu_webhook := self.webhooks.get(channel.id)) is not None:
            return uwu_webhook
        
        else:
            webhooks = await channel.webhooks()
            uwu_webhook: discord.Webhook = next((hook for hook in webhooks if hook.name == f"uwuhook-{self.bot.user.id}"), None)

            if not uwu_webhook:
                try:
                    webhooker = await channel.create_webhook(
                        name=f"uwuhook-{self.bot.user.id}",
                        reason='uwuhook is for UwU'
                    )
                    self.webhooks.update({channel.id: webhooker})
                    return webhooker
                
                except discord.HTTPException:
                    return None
            
            else:
                self.webhooks.update({channel.id:uwu_webhook})
                return uwu_webhook
    #endregion

    #
    #   --- UwU command groups
    #

    #region slash commands

    uwu = discord.SlashCommandGroup(
        "uwu",
        "UwUify Commands",
        checks=[pc.mods_can_change_settings]
    )

    @discord.guild_only()
    @uwu.command(name="channel",description="Make a channel automatically UwU every message",checks=[pc.mods_can_change_settings],)
    async def _add_channel(
        self,
        ctx: discord.ApplicationContext,
        channel: discord.Option(abc.GuildChannel, description="The Channel to uwuify"),#type:ignore
        intensity: discord.Option(
            float,
            description="The intensity of the uwuification, default is 1.0",
            default=1.0,
            required=False,
            min_value=0.1,
            max_value=10.0,
            ),#type:ignore
        silent: discord.Option(bool, description="Hide the confirmation message?", default=False)#type:ignore
    ):
        if not await self._uwu_enabled(ctx):
            return await ctx.interaction.response.send_message("This command is disabled on this server.")

        if not await self._change_uwu_status(ctx, channel, intensity):
            await ctx.interaction.response.send_message(f"{channel.mention} has been uwuified. Run for your lives!", ephemeral=silent)
        else:
            await ctx.interaction.response.send_message(f"{channel.mention} has been liberated from uwuification. Thank goodneess!", ephemeral=silent)
    
    @discord.guild_only()
    @uwu.command(name="user", description="Turn every message from this user into unintelligible uwu gibberish.")
    async def add_user(
            self,
            ctx: discord.ApplicationContext,
            user: discord.Option(discord.User, description="The user to uwuify.", required=True),#type:ignore
            intensity: discord.Option(
                float,
                description="The intensity of the uwuification, default is 1.0",
                default=1.0,
                required=False,
                min_value=0.1,
                max_value=10.0,
            ),#type:ignore
        silent: discord.Option(bool, description="Hide the confirmation message?", default=False)#type:ignore
    ):
        if not await self._uwu_enabled(ctx):
            return await ctx.interaction.response.send_message("This command is **disabled** on this server.")

        if not await self._change_uwu_status(ctx, user, intensity):
            await ctx.interaction.response.send_message(f"{user.name} is now fucked. **Pick a god and pray**.", ephemeral=silent)
        else:
            await ctx.interaction.response.send_message(f"{user.name} is now unfucked.", ephemeral=silent)

    @discord.guild_only()
    @uwu.command(name="intensity", description="Change the global uwu intensity.")
    async def change_intensity(
        self,
        ctx: discord.ApplicationContext,
        intensity: discord.Option(
            float,
            description="The intensity of the uwuification, default is 1.0",
            default=2.0,
            required=False,
            min_value=0.1,
            max_value=30.0,
        ),#type:ignore
    ):
        logger = set_up_guild_logger(ctx.guild.id)

        if not await self._uwu_enabled(ctx):
            return await ctx.interaction.response.send_message("This command is **disabled** on this server.")
        
        await self.redis.hset(f"uwui:{ctx.guild_id}", f"g:", intensity)
        logger.info(f"UWU: {ctx.author.name} set global intensity to {intensity} in '{ctx.guild.name}'")
        return await ctx.interaction.response.send_message(f"Set the global intensity to **{intensity}**")
    #endregion

    #region prefixed commands
    @discord.guild_only()
    @commands.command(name="uwu_user")
    async def _uwu_user(self, ctx):
        await ctx.send(f"This command is deprecated, please use {self.add_user.mention}")

    @discord.guild_only()
    @commands.command(name="uwu_user")
    async def _uwu_user(self, ctx):
        await ctx.send(f"This command is deprecated, please use {self.add_user.mention}")

    @discord.guild_only()
    @commands.command(name="uwu_channel")
    async def _uwu_channel(self, ctx):
        await ctx.send(f"This command is deprecated, please use {self._add_channel.mention}")
    #endregion

    async def uwuify_message(self, message: Message) -> tuple[str, list, list]:
        files = []
        process_embeds = True
        uwu_embeds = None
        output = None

        # copy attachments if they are not remixes
        if not message.is_remix and message.attachments:
            for attachment in message.attachments:
                async with self.bot.aiohttp_session.get(attachment.url) as resp:
                    fp = io.BytesIO(await resp.read())
                    files.append(discord.File(fp, filename=attachment.filename))
        
        # convert the input string to ascii
        msg_len = len(message.content) + 20
        msg_content = unidecode(message.content, errors="preserve")
        
        # if the user cant embed links, make links not embed by surrounding them with <>
        if not message.channel.permissions_for(message.guild.get_member(message.author.id)).embed_links:
            links = r"(https?:\/\/[A-Za-z0-9\-._~!$&'()*+,;=:@\/?]+)"
            msg_content = re.sub(links, r"<\1>", msg_content)
            process_embeds = False
        
        msg_small = textwrap.wrap(msg_content, msg_len)

        # - all intensities override each other, individual user being the strongest one -
        # get the intensities in order author, channel, global
        intensities = await self.redis.hmget(f"uwui:{message.guild.id}", [f"u:{message.author.id}", f"c:{message.channel.id}", "g"])
        
        # get the first non-None intensity or default to 1.0 if there isn't any intensity set
        intensity = next((float(i) for i in intensities if i is not None), 1.0)

        # check if we have text in the message and uwuify it
        if len(msg_small) > 0:
            msg_content = uwuify(msg_small[0], message.id, intensity, message.channel.nsfw) 

            # split it up while maintaining whole words
            output = textwrap.wrap(msg_content, 2000)
            # for each new "message" send it in the channel
            # thanks paradox for breaking the >2000 msg limit

        # process the embeds
        if process_embeds:
            uwu_embeds = uwuify_embeds(message, message.id, intensity, message.channel.nsfw)
        
        if output:
            return output[0], files, uwu_embeds
        else:
            return None, files, uwu_embeds
        
    
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(name="uwuify", aliases=["uwu"])
    async def _uwuify(self, ctx: commands.Context, *, msg: str = None) -> None:
        """
        UwUify your text (now even more cursed)
        """
        message = None
        # fetch the message from the reference
        if ctx.message.reference:
            ref = ctx.message.reference
            message = await self.bot.get_or_fetch_message(ref.message_id, ref.channel_id)
        
        # if the message content is empty, return
        output, files, uwu_embeds = await self.uwuify_message(message)
        
        await ctx.reply(output, files=files, embeds=uwu_embeds)

    #region main listener
    @commands.Cog.listener()
    async def on_message(self, message: Message):
        self.bot.events_hour += 1
        self.bot.events_total += 1

        # ignore DMs and webhooks
        if not message.guild or message.webhook_id:
            return
        
        if not await self._listener_checks(message):
            return
        
        # Check if the user is a bot and if they are affected by uwuify
        # Carter's code (Updated)
        
        # get or create the uwu webhook
        # if we failed to create it somehow, raise 
        try:
            if not (webhook := await self.get_uwu_webhook("", message.channel)):
                return
            
            if not webhook.token:
                # try to create a webhook with the bot id in the name, in case another uwuhook already exists (like the dev server)
                webhook = await self.get_uwu_webhook(self.bot.user.id, message.channel)

                # if we still fail to create it, return
                if not webhook:
                    return

        except discord.Forbidden:
            return
        
        output, files, uwu_embeds = await self.uwuify_message(message)

        # get the username to use for the webhook, uses new usernames if discriminator is 0 else it uses old usernames (bots tend to have old usernames)
        username = message.author.name if message.author.discriminator == "0" else message.author.name + "#" + message.author.discriminator

        # wrap both the send webhook and delete message coroutines into Future objects
        a = asyncio.ensure_future(webhook.send(
            content=output,
            username=message.author.nick or username,
            avatar_url=get_avatar_url(user=message.author),
            files=files,
            embeds=uwu_embeds or [],
            allowed_mentions=discord.AllowedMentions(
                everyone=message.author.guild_permissions.mention_everyone,
                roles=False,
                users=True
            ),
        ))

        b = asyncio.ensure_future(message.delete(reason="UwU Delete"))
    
        # await those futures side by side
        try:
            await a, b
        except discord.InvalidArgument:
            # remove the non-working webhook from the cache
            try:
                self.webhooks.pop(message.channel.id)
            except KeyError:
                return

    #endregion
#endregion

def setup(bot):
    bot.add_cog(UwuCog(bot))
