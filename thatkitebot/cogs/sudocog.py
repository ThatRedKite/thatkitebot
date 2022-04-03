#  Copyright (c) 2019-2022 ThatRedKite and contributors

from discord.ext import commands


class SudoCommands(commands.Cog, name="administrative commands"):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.dirname = bot.dirname

    @commands.is_owner()
    @commands.command()
    async def kill(self, ctx):
        """Kills the bot :("""

        # close the aiohttp session
        await self.bot.aiohttp_session.close()

        # close the redis connections
        await self.redis.close()
        await self.redis_repost.close()
        await self.redis_welcomes.close()
        await self.redis_cache.close()

        # close the discord session
        await self.bot.close()

    @commands.is_owner()
    @commands.command(aliases=["reload", "reboot", "r"])
    async def restart(self, ctx):
        """Reloads all cogs"""
        # this will currently break all image commands
        extensions = list(self.bot.extensions.keys())
        for extension in extensions:
            if not extension == "thatkitebot.cogs.electroslash":
                try:
                    self.bot.reload_extension(extension)
                    print(f"Reloaded {extension}")
                except Exception as exc:
                    raise exc
        await ctx.send(f"All cogs reloaded.")
        print("\n")

    @commands.is_owner()
    @commands.command()
    async def debug(self, ctx):
        """produces more verbose error messages"""
        self.bot.debugmode = not self.bot.debugmode
        await ctx.message.delete()

    @commands.is_owner()
    @commands.command()
    async def echo(self, ctx, *, message: str):
        """pretend to be the bot"""
        await ctx.message.delete()
        await ctx.send(message)


def setup(bot):
    bot.add_cog(SudoCommands(bot))
