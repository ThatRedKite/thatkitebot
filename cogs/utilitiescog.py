import discord
from discord.ext import commands

from backend import utilcog_backend as back


class utility_commands(commands.Cog):
    def __init__(self, bot: commands.Bot, dirname):
        self.dirname = dirname
        self.bot = bot

    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command()
    async def help(self, ctx):
        embed = discord.Embed(title="**a list of the bot's commands**")
        for cog in self.bot.cogs:
            commandstring = ""
            for command in self.bot.get_cog(cog).walk_commands():
                if cog != "NSFW":
                    commandstring += f"{command}\n"
            if len(commandstring) > 1:
                embed.add_field(name=f"**{cog}**", value=f"\n{commandstring}", inline=True)
        embed.set_footer(text=f"\nThatKiteBot² version {self.bot.version}", icon_url=self.bot.user.avatar_url)
        await ctx.send(embed=embed)

    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command(pass_context=True, aliases=["uptime", "load"])
    async def status(self, ctx):
        """
        Bot's Current Status
        """
        mem, cpu, cores_used, cores_total, ping, uptime = await back.get_status(self.bot.pid, self.bot)
        embed = discord.Embed(title="bot status")
        embed.add_field(name="RAM usage <:rammy:784103886150434866>",
                        value=f"{mem} MB\n**CPU usage** <:cpu:784103413804826665>\n{cpu}%", inline=True)
        embed.add_field(name="cores <:cpu:784103413804826665>",
                        value=f"{cores_used}/{cores_total}\n**ping** <:ping:784103830102736908>\n{ping} ms")
        embed.add_field(name="uptime <:uptime:784103801896042547>",
                        value=f"{uptime}\n**debugmode** <:buggy:784103932204548151>\n{self.bot.debugmode}")
        embed.set_footer(text="version: {}".format(self.bot.version))
        embed.set_thumbnail(url=str(self.bot.user.avatar_url))
        if not self.bot.debugmode:
            embed.color = 0x00ff00
        else:
            embed.color = 0x5105ad
        await ctx.trigger_typing()
        await ctx.send(embed=embed)

