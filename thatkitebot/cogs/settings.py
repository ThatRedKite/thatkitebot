import discord
from discord.ext import commands
import redis


def pp(a):
    if type(a) is str:
        return a.upper()
    else:
        return a


class SettingsCog(commands.Cog, name="settings"):
    def __init__(self, bot):
        self.bot: discord.Client = bot
        self.redis = self.bot.redis

    @commands.group(name="setting")
    @commands.has_permissions(administrator=True)
    async def settings(self, ctx):
        if not ctx.subcommand_passed:
            cmds = "\n".join([c.name for c in ctx.command.commands])
            await ctx.send(f"This command cannot be used alone. Please use one of the following subcommands:\n**{cmds}**")

    @settings.command(name="add", aliases=["update"])
    @commands.cooldown(3, 10, commands.BucketType.user)
    async def _add(self, ctx, name: str, arg):
        channel = ctx.channel
        author = ctx.message.author
        yes_choices = ["y", "yes", "ja", "j"]

        def check(m):
            if m.channel == channel and m.author is author:
                return m.content.lower() in yes_choices

        self.redis.hset(ctx.guild.id, pp(name), pp(arg))
        await ctx.send(f"Add the setting `{name}` with the value `{arg}` to the settings? (y/n)")
        msg = await self.bot.wait_for("message", timeout=10, check=check)
        if msg.content in yes_choices:
            self.redis.hset(ctx.guild.id, pp(name), pp(arg))
            await ctx.send("Okay, done.")
        else:
            await ctx.send("Cancelled.")

    @settings.command(name="list", aliases=["ls"])
    async def _list(self, ctx):
        settings = self.redis.hgetall(ctx.guild.id)
        embed = discord.Embed(title=f"settings for **guild {str(ctx.guild)}**")
        for setting in settings:
            embed.add_field(name=setting, value=settings.get(setting))
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(SettingsCog(bot))
