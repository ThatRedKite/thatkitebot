#  Copyright (c) 2019-2023 ThatRedKite and contributors

import re
import io
import textwrap
from typing import Union

import discord

from unidecode import unidecode
from uwuipy import uwuipy
from discord import abc
from discord.ext import commands
from redis import asyncio as aioredis

import thatkitebot
from thatkitebot.base.url import get_avatar_url
from thatkitebot.base.util import PermissonChecks as pc
from thatkitebot.base.util import set_up_guild_logger
from thatkitebot.tkb_redis.settings import RedisFlags



async def uwuify(message: str, id: int, intensity: float = 1.0, enable_nsfw = False):
    # initialize the uwuipy class, multiplying the default intensites by :intensity:
    uwu = uwuipy(id, *map(lambda m: (m * intensity), (0.1, 0.05, 0.0075)),nsfw_actions=enable_nsfw)
    message = uwu.uwuify(message)

    # return without that awfully long message 
    return message.replace("***breaks into your house and aliases neofetch to rm -rf --no-preserve-root /***", "")

async def get_uwu_webhook(webhook_id, channel: discord.TextChannel) -> Union[discord.Webhook, None]:
    webhooks = await channel.webhooks()
    uwu_webhook: discord.Webhook = next((hook for hook in webhooks if hook.name == f"uwuhook{webhook_id}"), None)
    if not uwu_webhook:
        try:
            webhooker = await channel.create_webhook(
                name=f"uwuhook{webhook_id}",
                reason='uwuhook is for UwU'
            )
        except discord.HTTPException:
            return None
        return webhooker

    else:
        return uwu_webhook


class UwuCog(commands.Cog, name="UwU Commands"):
    def __init__(self, bot):
        self.bot: thatkitebot.ThatKiteBot = bot
        self.redis: aioredis.Redis = bot.redis

    async def _uwu_enabled(self, ctx):
        return await RedisFlags.get_guild_flag(self.redis, ctx.guild, RedisFlags.FlagEnum.UWU.value)
    
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
        if message.author.bot:
            return False

        if not await self._uwu_enabled(message):
            return False

        # check if message is in an uwu channel
        is_channel = await self.redis.sismember(f"uwu_channels:{message.guild.id}", str(message.channel.id))
        is_user = await self.redis.sismember(f"uwu_users:{message.guild.id}", str(message.author.id))

        #if not (is_user and is_channel):
        #    return False

        return is_user or is_channel

    #
    #   --- UwU command groups
    #

    uwu = discord.SlashCommandGroup(
        "uwu",
        "UwUify Commands",
        checks=[pc.mods_can_change_settings, lambda ctx: ctx.guild is not None]
    )

    @uwu.command(name="channel",description="Make a channel automatically UwU every message",checks=[pc.mods_can_change_settings])
    async def _add_channel(
        self,
        ctx: discord.ApplicationContext,
        channel: discord.Option(abc.GuildChannel, description="The Channel to uwuify"),
        intensity: discord.Option(
            float,
            description="The intensity of the uwuification, default is 1.0",
            default=1.0,
            required=False,
            min_value=0.1,
            max_value=10.0,
            ),
        silent: discord.Option(bool, description="Hide the confirmation message?", default=False)
    ):
        if not await self._uwu_enabled(ctx):
            return ctx.interaction.response.send_message("This command is disabled on this server.")

        if not await self._change_uwu_status(ctx, channel, intensity):
            await ctx.interaction.response.send_message(f"{channel.mention} has been uwuified. Run for your lives!", ephemeral=silent)
        else:
            await ctx.interaction.response.send_message(f"{channel.mention} has been liberated from uwuification. Thank goodneess!", ephemeral=silent)


    @uwu.command(name="user", description="Turn every message from this user into unintelligible uwu gibberish.")
    async def add_user(
            self,
            ctx: discord.ApplicationContext,
            user: discord.Option(discord.User, description="The user to uwuify.", required=True),
            intensity: discord.Option(
                float,
                description="The intensity of the uwuification, default is 1.0",
                default=1.0,
                required=False,
                min_value=0.1,
                max_value=10.0,
            ),
        silent: discord.Option(bool, description="Hide the confirmation message?", default=False)
    ):
        if not await self._uwu_enabled(ctx):
            return await ctx.interaction.response.send_message("This command is **disabled** on this server.")

        if not await self._change_uwu_status(ctx, user, intensity):
            await ctx.interaction.response.send_message(f"{user.name} is now fucked. **Pick a god and pray**.", ephemeral=silent)
        else:
            await ctx.interaction.response.send_message(f"{user.name} is now unfucked.", ephemeral=silent)

    @uwu.command(name="intensity", description="Change the global uwu intensity.")
    async def change_intensity(
        self,
        ctx: discord.ApplicationContext,
        intensity: discord.Option(
            float,
            description="The intensity of the uwuification, default is 1.0",
            default=1.0,
            required=False,
            min_value=0.1,
            max_value=10.0,
        ),
    ):
        logger = set_up_guild_logger(ctx.guild.id)

        if not await self._uwu_enabled(ctx):
            return await ctx.interaction.response.send_message("This command is **disabled** on this server.")
        
        await self.redis.hset("uwui", "g", intensity)
        logger.info(f"UWU: {ctx.author.name} set global intensity to {intensity} in '{ctx.guild.name}'")
        return await ctx.interaction.response.send_message(f"Set the global intensity to **{intensity}**")

    @commands.command(name="uwu_user")
    async def _uwu_user(self, ctx):
        await ctx.send("This command is deprecated, please use the slash command version")

    @commands.command(name="uwu_channel")
    async def _uwu_channel(self, ctx):
        await ctx.send("This command is deprecated, please use the slash command version")


    #
    #   --- main listener function ---
    #
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        self.bot.events_hour += 1
        self.bot.events_total += 1

        # ignore DMs
        if not message.guild:
            return

        webhook = None

        # Check if the user is a bot and if they are affected by uwuify
        if not await self._listener_checks(message):
            return

        # Carter's code (Updated)
        # ignore webhooks
        if not message.webhook_id:
            # get or create the uwu webhook
            webhook = await get_uwu_webhook("", message.channel)

            # if we failed to create it somehow, return
            if not webhook:
                return
            
            if not webhook.token:
                # try to create a webhook with the bot id in the name, in case another uwuhook already exists (like the dev server)
                webhook = await get_uwu_webhook(self.bot.user.id, message.channel)

                # if we still fail to create it, return
                if not webhook:
                    return

            files = []
            for attachment in message.attachments:
                async with self.bot.aiohttp_session.get(attachment.url) as resp:
                    fp = io.BytesIO(await resp.read())
                    files.append(discord.File(fp, filename=attachment.filename))
            
            # convert the input string to ascii
            msg_len = len(message.content) + 20
            msg = unidecode(message.content, errors="preserve")

            # if the user cant embed links, make links not embed by surrounding them with <>
            if not message.channel.permissions_for(message.guild.get_member(message.author.id)).embed_links:
                links = r"(https?:\/\/[A-Za-z0-9\-._~!$&'()*+,;=:@\/?]+)"
                msg = re.sub(links, r"<\1>", msg)

            msg_small = textwrap.wrap(msg, msg_len)

            # - all intensities override each other, individual user being the strongest one -

            # try to get the global intensity
            intensity = await self.redis.hget(f"uwui:{message.guild.id}", "g") or 1.0

            # try to get the channel's intensity
            intensity = float(await self.redis.hget(f"uwui:{message.guild.id}", f"c:{message.channel.id}") or intensity)

            # try to get the user's individual intensity
            intensity = float(await self.redis.hget(f"uwui:{message.guild.id}", f"u:{message.author.id}") or intensity)

            msg = await uwuify(msg_small[0], message.id, intensity, message.channel.nsfw)
            # split it up while maintaining whole words

            output = textwrap.wrap(msg, 2000)
            # for each new "message" send it in the channel
            # thanks paradox for breaking the >2000 msg limit

            username = message.author.name if message.author.discriminator == "0" else message.author.name + "#" + message.author.discriminator

            await webhook.send(
                content=output[0],
                username=username,
                avatar_url=get_avatar_url(user=message.author),
                files=files,
                allowed_mentions=discord.AllowedMentions(
                    everyone=message.author.guild_permissions.mention_everyone,
                    roles=False,
                    users=True
                ),
            )

            await message.delete(reason="UwU Delete")


def setup(bot):
    bot.add_cog(UwuCog(bot))
