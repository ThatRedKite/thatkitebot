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
from io import BytesIO

import discord
from discord.ext import commands

from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from wand.image import Image as WandImage
from wand.color import Color as WandColor

from thatkitebot import __main__ as tkb
from thatkitebot.embeds.status import gen_embed as status_embed
from thatkitebot.embeds.about import gen_embed as about_embed
from thatkitebot.embeds.gdpr import gen_embed as gdpr_embed
from thatkitebot.base.util import EmbedColors as ec
#endregion

#region Cog
class UtilityCommands(commands.Cog, name="Potentially useful commands"):
    """
    Utility commands for the bot. These commands are basically informational commands.
    """
    def __init__(self, bot: tkb.ThatKiteBot):
        self.redis = bot.redis
        self.bot = bot

    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command(pass_context=True, aliases=["uptime", "load"])
    async def status(self, ctx):
        """
        Displays the status of the bot.
        """

        await ctx.send(embed=await status_embed(self.bot, self.bot.redis_cache))

    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command(pass_context=True, aliases=["serverinfo", "guildinfo", "server"])
    async def guild(self, ctx):
        """
        Displays information about the server.
        """
        guild = ctx.guild
        embed = discord.Embed()
        embed.title = guild.name
        embed.description = guild.description
        embed.add_field(name="Owner", value=guild.owner.mention)
        embed.add_field(name="Members", value=guild.member_count)
        embed.add_field(name="Channels", value=len(guild.channels))
        embed.add_field(name="Roles", value=len(guild.roles))
        embed.add_field(name="Created at", value=guild.created_at.strftime("%d/%m/%Y %H:%M:%S"))
        age = relativedelta(datetime.now(timezone.utc), guild.created_at)
        embed.add_field(name="Age", value=(f"{(str(age.years) + (' years, ' if age.years != 1 else ' year' + ', ')) if age.years != 0 else ''}{(str(age.months) + (' months, ' if age.months != 1 else ' month, ')) if age.months != 0 else ''}{age.days} {'days' if age.days != 1 else 'day'}"))
        if guild.icon:
            embed.set_thumbnail(url=guild.icon)
        embed.color = ec.lime_green
        await ctx.send(embed=embed)

    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command(pass_context=True, aliases=["userinfo", "user"])
    async def whois(self, ctx, user: discord.Member = None):
        """
        Displays information about a user.
        """
        if user is None:
            user = ctx.author
        embed = discord.Embed()
        embed.title = user.name
        embed.description = user.mention
        embed.add_field(name="ID", value=user.id)
        embed.add_field(name="Server joined", value=user.joined_at.strftime("%d/%m/%Y %H:%M:%S"))
        age = relativedelta(datetime.now(timezone.utc), user.joined_at)
        embed.add_field(name="Server age", value=(f"{(str(age.years) + (' years, ' if age.years != 1 else ' year' + ', ')) if age.years != 0 else ''}{(str(age.months) + (' months, ' if age.months != 1 else ' month, ')) if age.months != 0 else ''}{age.days} {'days' if age.days != 1 else 'day'}"))
        embed.add_field(name="Account created", value=user.created_at.strftime("%d/%m/%Y %H:%M:%S"))
        age = relativedelta(datetime.now(timezone.utc), user.created_at)
        embed.add_field(name="Account age", value=(f"{(str(age.years) + (' years, ' if age.years != 1 else ' year' + ', ')) if age.years != 0 else ''}{(str(age.months) + (' months, ' if age.months != 1 else ' month, ')) if age.months != 0 else ''}{age.days} {'days' if age.days != 1 else 'day'}"))
        # a list of roles, excluding @everyone
        embed.add_field(name="Roles", value=", ".join([role.mention for role in user.roles if role.name != "@everyone"]))
        # a footnote with the percentage of the servers existence the user has been in
        embed.set_footer(text=f"The user has been in the server for {round(100 - (user.joined_at - ctx.guild.created_at).total_seconds() / (datetime.now(timezone.utc) - ctx.guild.created_at).total_seconds() * 100, 2)}% of the servers existence")
        if user.avatar:
            embed.set_thumbnail(url=user.avatar)
        embed.color = ec.lime_green
        await ctx.send(embed=embed)

    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command(pass_context=True)
    async def about(self, ctx):
        """
        This command is here to show you what the bot is made of.
        """
        await ctx.send(embed=await about_embed(self))

    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command(pass_context=True)
    async def gdpr(self, ctx):
        """
        This command shows you what data the bot collects and how it is used.
        """
        await ctx.send(embed=gdpr_embed(self))

    @commands.command()
    async def invite(self, ctx):
        """This sends you an invite for the bot if you want to add it to one of your servers."""
        await ctx.author.send(
            f"https://discord.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=275418311744&scope=bot%20applications.commands"
        )
    
    @commands.command()
    async def color_test(self,ctx,id):
        id_color = hex(int(id))[4:10].replace("0x","")  
        with WandImage(width=256, height=256, background=WandColor(f"#{id_color}")) as colorimg:
            b = colorimg.make_blob(format="jpeg")
        file = discord.File(BytesIO(b), filename="id_color.jpeg")

        embed = discord.Embed(title=f"ID color tester")

        embed.set_image(url="attachment://id_color.jpeg")
        await ctx.send(file=file, embed=embed)
#endregion

def setup(bot):
    bot.add_cog(UtilityCommands(bot))
