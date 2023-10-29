#  Copyright (c) 2019-2023 ThatRedKite and contributors

import re
import io
import textwrap
from typing import Union

import discord
from unidecode import unidecode
from uwuipy import uwuipy
from discord.ext import commands
from redis import asyncio as aioredis

import thatkitebot
from thatkitebot.base.util import PermissonChecks as pc
from thatkitebot.base.util import set_up_guild_logger
from thatkitebot.tkb_redis.settings import RedisFlags


async def uwuify(message: str, id: int):
    uwu = uwuipy(id)
    message = uwu.uwuify(message)
    return message


async def get_uwu_webhook(channel: discord.TextChannel) -> Union[discord.Webhook, None]:
    webhooks = await channel.webhooks()
    uwu_webhook: discord.Webhook = next((hook for hook in webhooks if hook.name == "uwuhook"), None)
    if not uwu_webhook:
        print("trying to create new hook")
        try:
            webhooker = await channel.create_webhook(
                name='uwuhook',
                reason='uwuhook is for UwU'
            )
        except discord.HTTPException:
            print("failed to create hook")
            return None
        return webhooker

    else:
        print("got hook: ", uwu_webhook)
        return uwu_webhook


class UwuCog(commands.Cog, name="UwU Commands"):
    def __init__(self, bot):
        self.bot: thatkitebot.ThatKiteBot = bot
        self.redis: aioredis.Redis = bot.redis

    async def _uwu_enabled(self, ctx):
        return await RedisFlags.get_guild_flag(self.redis, ctx.guild.id, RedisFlags.UWU)

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

    @uwu.command(
        name="channel",
        description="Make a channel automatically UwU every message",
        checks=[pc.mods_can_change_settings]
    )
    async def _add_channel(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        """
        uwuifies an entire channel by deleting the original messages
        and replacing them with bot clones.

        Usage:
        `+uwu_channel #channel` - toggles the setting for a channel

        Only administrators and moderators can use this command.
        """
        await ctx.defer()
        logger = set_up_guild_logger(ctx.guild.id)

        key = f"uwu_channels:{ctx.guild.id}"

        if not await self._uwu_enabled(ctx):
            return await ctx.followup.send("This command is disabled on this server.")

        if not await self.redis.sismember(key, str(channel.id)):
            await self.redis.sadd(key, channel.id)
            await ctx.followup.send(f"{channel.mention} is now an UwU channel.")
            logger.info(f"UWU: {ctx.author.name} uwuified #{channel.name} in {ctx.guild.name}")

        else:
            try:
                await self.redis.srem(key, channel.id)
            except aioredis.ResponseError:
                await ctx.followup.send(f"{channel.mention} is not an UwU channel.")
                return

            await ctx.respond(f"{channel.mention} is no longer an UwU channel.")
            logger.info(f"UWU: {ctx.author.name} de-uwuified #{channel.name} in {ctx.guild.name}")

    @uwu.command(name="user", description="Turn every message from this user into unintelligible uwu gibberish.")
    async def add_user(
            self,
            ctx: discord.ApplicationContext,
            user: discord.Option(discord.User, description="The user to uwuify.", required=True)
    ):
        """
        uwuifies all messages sent by a specific person by deleting
        their original messages and replacing them with a bot clone.

        Usage:
        `+uwu_user @user True` - toggle the setting for a user

        Only admins and moderators can use this command.
        """
        await ctx.defer()
        logger = set_up_guild_logger(ctx.guild.id)
        
        if not await self._uwu_enabled(ctx):
            return await ctx.followup.send("This command is disabled on this server.")

        key = f"uwu_users:{ctx.guild.id}"

        if not await self.redis.sismember(key, user.id):
            await self.redis.sadd(key, user.id)
            await ctx.followup.send(f"{user.name} is now fucked.")
            logger.info(f"UWU: {ctx.author.name} uwuified #{user.name} in {ctx.guild.name}")

        else:
            await self.redis.srem(key, user.id)
            await ctx.followup.send(f"{user.name} is now unfucked.")
            logger.info(f"UWU: {ctx.author.name} de-uwuified #{user.name} in {ctx.guild.name}")

    #
    #   --- main listener function ---
    #

    @commands.command(name="uwu_user")
    async def _uwu_user(self, ctx):
        await ctx.send("This command is deprecated, please use the slash command version")

    @commands.command(name="uwu_channel")
    async def _uwu_channel(self, ctx):
        await ctx.send("This command is deprecated, please use the slash command version")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        self.bot.events_hour += 1
        self.bot.events_total += 1

        webhook = None

        # Check if the user is a bot and if they are affected by uwuify
        if not await self._listener_checks(message):
            return

        # Carter's code (Updated)
        # ignore webhooks
        if not message.webhook_id:
            # get or create the uwu webhook
            webhook = await get_uwu_webhook(message.channel)

            # if we failed to create it somehow, return
            if not webhook:
                print("no hookey :(")
                return

            files = []
            for attachment in message.attachments:
                async with self.bot.aiohttp_session.get(attachment.url) as resp:
                    fp = io.BytesIO(await resp.read())
                    files.append(discord.File(fp, filename=attachment.filename))
            await message.delete(reason="UwU Delete")
            # convert the input string to ascii
            msg_len = len(message.content) + 20
            msg = unidecode(message.content)

            # if the user cant embed links, make links not embed by surrounding them with <>
            if not message.channel.permissions_for(message.guild.get_member(message.author.id)).embed_links:
                links = r"(https?:\/\/[A-Za-z0-9\-._~!$&'()*+,;=:@\/?]+)"
                msg = re.sub(links, r"<\1>", msg)

            msg_small = textwrap.wrap(msg, msg_len)
            msg = await uwuify(msg_small[0], message.id)
            # split it up while maintaining whole words
            output = textwrap.wrap(msg, 2000)
            # for each new "message" send it in the channel
            # thanks paradox for breaking the >2000 msg limit
            await webhook.send(
                content=output[0],
                username=message.author.name + "#" + message.author.discriminator,
                avatar_url=message.author.display_avatar.url,
                files=files
            )


def setup(bot):
    bot.add_cog(UwuCog(bot))
