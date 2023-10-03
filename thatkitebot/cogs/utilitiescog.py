#  Copyright (c) 2019-2022 ThatRedKite and contributors

import discord
from discord.ext import commands
from thatkitebot.backend.util import EmbedColors as ec
import psutil
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
import si_prefix
from thatkitebot.backend import url


class UtilityCommands(commands.Cog, name="utility commands"):
    """
    Utility commands for the bot. These commands are basically informational commands.
    """
    def __init__(self, bot: commands.Bot):
        self.redis = bot.redis
        self.bot = bot

    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command(pass_context=True, aliases=["uptime", "load"])
    async def status(self, ctx):
        """
        Displays the status of the bot.
        """
        process = psutil.Process(self.bot.pid)
        mem = process.memory_info()[0]
        redis_memory = (await self.redis.info())["used_memory"] + (await self.bot.redis_cache.info())["used_memory"]

        cpu = psutil.cpu_percent(interval=None)
        ping = round(self.bot.latency * 1000, 1)
        uptime = str(datetime.now() - self.bot.start_time).split(".")[0]
        total_users = sum([users.member_count for users in self.bot.guilds])
        guilds = len(self.bot.guilds)

        embed = discord.Embed()
        embed.add_field(name="System status",
                        value=f"""RAM usage: **{si_prefix.si_format(mem + redis_memory)}B**
                                CPU usage: **{cpu} %**
                                uptime: **{uptime}**
                                ping: **{ping} ms**""")

        embed.add_field(name="Bot stats",
                        value=f"""guilds: **{guilds}**
                                extensions loaded: **{len(self.bot.extensions)}**
                                total users: **{total_users}**
                                bot version: **{self.bot.version}**
                                Running commit: **[{self.bot.git_hash[0:7]}](https://github.com/ThatRedKite/thatkitebot/tree/{self.bot.git_hash})**
                                total command invokes: **{self.bot.command_invokes_total}**
                                commands invoked this hour: **{self.bot.command_invokes_hour}**
                                """, inline=False)
        try:
            embed.set_thumbnail(url=str(self.bot.user.avatar.url))
        except:
            pass

        if not self.bot.debug_mode:
            if cpu >= 90.0:
                embed.color = ec.traffic_red
                embed.set_footer(text="Warning: CPU usage over 90%")
            else:
                embed.color = ec.lime_green
        else:
            embed.color = ec.purple_violet
        await ctx.send(embed=embed)

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
        embed = discord.Embed(
            color=ec.purple_violet,
            title=f"About {self.bot.user.name}",
            description="""This bot licensed under the MIT license is open source and free to use for everyone.
                  I put a lot of my time into this bot and I really hope you enjoy it.
                  The source code is available [here](https://github.com/ThatRedKite/thatkitebot), feel free to contribute!
                  If you like it, consider [giving me a donation](https://www.buymeacoffee.com/ThatRedKite) to keep the server running.
                """
        )
        try:
            embed.set_thumbnail(url=str(self.bot.user.avatar.url))
        except:
            pass
        # dictionary for discord username lookup from GitHub username
        # format: "githubusername":"discordID"
        authordict = {
            "ThatRedKite": "<@249056455552925697>",
            "diminDDL": "<@312591385624576001>",
            "Cuprum77": "<@323502550340861963>",
            "laserpup": "<@357258808105500674>",
            "woo200": "<@1129767250342195222>",
            "Caraffa-git": "<@303227573121449994>"
        }
        jsonData = await url._contributorjson(self.bot.aiohttp_session)
        # get a list of "login" field values from json string variable jsonData
        authorlist = [x["login"] for x in jsonData]
        # if a username contains [bot] remove it from the list
        authorlist = [x for x in authorlist if not x.lower().__contains__("bot")]
        # keed only first 5 contributors in authorlist
        authorlist = authorlist[:5]
        embedStr = ""
        for i in authorlist:
            if i in authordict:
                embedStr += f"{authordict[i]}\n"
            else:
                embedStr += f"{i}\n"
        embedStr += "and other [contributors](https://github.com/ThatRedKite/thatkitebot/graphs/contributors)"    
        embed.add_field(
            name="Authors",
            value=embedStr
        )
        embed.add_field(
            name="libraries used",
            inline=False,
            value="""
            [pycord](https://github.com/Pycord-Development/pycord)
            [aiohttp](https://github.com/aio-libs/aiohttp)
            [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/)
            [PyYAML](https://pyyaml.org/)
            [Pillow](https://github.com/python-pillow/Pillow)
            [Wand](https://github.com/emcconville/wand)
            [markovify](https://github.com/jsvine/markovify)
            [psutil](https://github.com/giampaolo/psutil)
            [molmass](https://github.com/cgohlke/molmass)
            [si_prefix](https://github.com/cfobel/si-prefix)
            [redis-py](https://github.com/redis/redis-py)
            [lxml](https://lxml.de/)
            [hiredis-py](https://github.com/redis/hiredis-py)
            [aioredis-py](https://github.com/aio-libs/aioredis-py)
            [matplotlib](https://matplotlib.org/)
            [python-xkcd](https://github.com/TC01/python-xkcd)
            [imagehash](https://github.com/JohannesBuchner/imagehash)
            """
            # [dulwich](https://github.com/jelmer/dulwich)
        )

        embed.set_footer(text="ThatKiteBot v{}".format(self.bot.version))

        await ctx.send(embed=embed)

    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command(pass_context=True)
    async def gdpr(self, ctx):
        """
        This command shows you what data the bot collects and how it is used.
        """
        embed = discord.Embed(
            color=ec.purple_violet,
            title="ThatKiteBot Privacy Policy",
            description="""ThatKiteBot is run by ThatRedKite#4842. This privacy policy will
            explain how this bot uses the personal data collected from you when you use it."""
        )
        embed.add_field(
            name="What data does the bot collect?",
            value="""
            The bot collects the following data:
            - Your Discord ID
            - Your Discord username
            - Your Discord avatar
            - Reactions you add to messages
            - Messages sent by you
            - Any other data you provide the bot with while using it's commands"""
        )
        embed.add_field(
            name="How is the data collected?",
            value="""
            The bot collects the data it needs to function. It does this only by using the Discord API.
            You directly provide the bot with most of the data we collect. The bot collects and processes the data when you:
            - Send a messages
            - Use a command
            - Use a reaction
            """
        )
        embed.add_field(
            name="How will your data be used?",
            value="""
            The bot collects so that it can:
            - Process your commands
            - Provide Markov functionality
            - Understand the context of commands
            The data is not transferred to any third parties.
            """
        )
        embed.add_field(
            name="How is your data stored?",
            value="""
            The bot securely stores the data on a server in Nuremberg (Germany).
            - The bot does not permanently store message content it is only used for the Markov chain and thus stays in RAM only.
            - The RAM data is wiped whenever the bot is rebooted.
            - The only data that is permanently stored are Discord IDs.
            """
        )
        embed.add_field(
            name="What are your data protection rights?",
            value="""
            We would like to make sure you are fully aware of all of your data protection rights. Every user is entitled to the following:
            If you make a request, we have one month to respond to you. If you would like to exercise any of these rights, please contact ThatRedKite#4842 on Discord.
            """
        )
        embed.add_field(
            name="Your rights listed below:",
            inline=False,
            value="""
            The right to access – You have the right to request us for copies of your personal data. We may charge you a small fee for this service.
            The right to rectification – You have the right to request that we correct any information you believe is inaccurate. You also have the right to request us to complete the information you believe is incomplete.
            The right to erasure – You have the right to request that we erase your personal data, under certain conditions.
            The right to restrict processing – You have the right to request that we restrict the processing of your personal data, under certain conditions.
            The right to object to processing – You have the right to object to our processing of your personal data, under certain conditions.
            The right to data portability – You have the right to request that we transfer the data that we have collected to another organization, or directly to you, under certain conditions.
            """
        )
        embed.set_thumbnail(url=str(self.bot.user.avatar.url))
        embed.set_footer(text=f"{self.bot.user.name} v{self.bot.version} this policy was last updated: ")
        embed.timestamp = datetime(2022, 7, 30, 23, 55, 14, 0)
        await ctx.send(embed=embed)

    @commands.command()
    async def invite(self, ctx):
        """This sends you an invite for the bot if you want to add it to one of your servers."""
        await ctx.author.send(
            f"https://discord.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=275418311744&scope=bot%20applications.commands"
        )


def setup(bot):
    bot.add_cog(UtilityCommands(bot))
