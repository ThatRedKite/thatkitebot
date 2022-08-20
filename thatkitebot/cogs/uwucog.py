import aioredis
import discord
import io
from discord.ext import commands, bridge
from thatkitebot.cogs.settings import mods_can_change_settings
from uwuipy import uwuipy
import textwrap
from unidecode import unidecode


async def uwuify(message: str, id: int):
    uwu = uwuipy(id)
    message = uwu.uwuify(message)
    return message


# Yes this definitely needs its own cog shut the fuck up kite (Jk I love you)
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
        if not await self.redis.sismember(f"uwu_channels:{message.guild.id}", message.channel.id) and not await self.redis.sismember(f"uwu_users:{message.guild.id}", message.author.id):
            return

        # Carter's code (Updated)
        if not message.webhook_id:
            await message.delete()

            webhooks = await message.channel.webhooks()
            webhook: discord.Webhook = next((hook for hook in webhooks if hook.name == "uwuhook"), None)

            if not webhook:
                webhook = await message.channel.create_webhook(name='uwuhook', reason='uwuhook is for uwu channel uwu')

            files = []
            for attachment in message.attachments:
                async with self.bot.aiohttp_session.get(attachment.url) as resp:
                    fp = io.BytesIO(await resp.read())
                    files.append(discord.File(fp, filename=attachment.filename))

            # convert the input string to ascii
            msg_len = len(message.content) + 20
            msg = unidecode(message.content)
            msg_small = textwrap.wrap(msg, msg_len)
            msg = await uwuify(msg_small[0], message.id)
            # split it up while maintaining whole words
            output = textwrap.wrap(msg, 2000)
            # for each new "message" send it in the channel
            # thanks paradox for breaking the >2000 msg limit
            await webhook.send(content=output[0],
                               username=message.author.name + "#" + message.author.discriminator,
                               avatar_url=message.author.display_avatar.url,
                               files=files)

    # Sorry mom
    @commands.check(mods_can_change_settings)
    @bridge.bridge_command(name="uwu_channel", aliases=["uwuchannel", "uwuch"],
                           description="Make a channel automatically UwU every message")
    async def add_uwu_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """
        uwuifies an entire channel by deleting the original messages
        and replacing them with bot clones.
        
        Usage: 
        `+uwu_channel #channel` - toggles the setting for a channel
               
        Only admins can use this command.
        """
        if not await mods_can_change_settings(ctx):
            return await ctx.respond("You don't have permission to change settings.")
        
        key = f"uwu_channels:{ctx.guild.id}"
        if not await self.redis.sismember(key, channel.id):
            await self.redis.sadd(key, channel.id)
            await ctx.respond(f"{channel.mention} is now an UwU channel.")
            print(f"{ctx.guild.name}:  {ctx.author.name}#{ctx.author.discriminator} uwuified #{channel.name}")
        else:
            try:
                await self.redis.srem(key, channel.id)
            except aioredis.ResponseError:
                await ctx.respond(f"{channel.mention} is not an UwU channel.")
                return

            await ctx.respond(f"{channel.mention} is no longer an UwU channel.")
            print(f"{ctx.guild.name}:  {ctx.author.name}#{ctx.author.discriminator} de-uwuified #{channel.name}")

    @commands.check(mods_can_change_settings)
    @bridge.bridge_command(name="uwu_user", aliases=["fuck_you"], hidden=True,
                           description="Make a user automatically UwU every message")
    async def add_uwu_user(self, ctx: bridge.BridgeContext, user: discord.User):
        """
        uwuifies all messages sent by a specific person by deleting
        their original messages and replacing them with a bot clone.
        
        Usage: 
        `+uwu_user @user True` - toggle the setting for a user
               
        Only admins can use this command.
        """
        if not await mods_can_change_settings(ctx):
            return await ctx.respond("You don't have permission to change settings.")
        
        key = f"uwu_users:{ctx.guild.id}"
        if not await self.redis.sismember(key, user.id):
            await self.redis.sadd(key, user.id)
            await ctx.respond(f"{user.name} is now fucked.")
            print(f"{ctx.guild.name}: {ctx.author.name}#{ctx.author.discriminator} uwuified {user.name}#{user.discriminator}")
        else:
            try:
                await self.redis.srem(key, user.id)
            except aioredis.ResponseError:
                await ctx.respond(f"{user.name} is not fucked.")
                return
            await ctx.respond(f"{user.name} is now unfucked.")
            print(f"{ctx.guild.name}: {ctx.author.name}#{ctx.author.discriminator} de-uwuified {user.name}#{user.discriminator}")


def setup(bot):
    bot.add_cog(UwuCog(bot))
