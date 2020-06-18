
import os
import re
import psutil
import discord
import logging
import subprocess
from PIL import Image
from bf.util import errormsg
from datetime import datetime
from discord.ext import commands

class utility_commands(commands.Cog):
    def __init__(self, bot:commands.Bot, dirname):
        self.dirname=dirname
        self.bot=bot
        self.version=self.bot.version
        self._last_member=None

    @commands.command()
    async def status(self, ctx):
        process=psutil.Process(os.getpid())
        mem=int(round((process.memory_info()[0] / 1000000)))
        cpu=process.cpu_percent(interval=10)
        cores_used=len(process.cpu_affinity())   
        cores_total=psutil.cpu_count()
        ping=round(self.bot.latency * 1000, 1)
        ass=process.status()

        embed=discord.Embed(title="__Status of {0}__".format(self.bot.user.name, description=" "))
        embed.add_field(name="**Current RAM usage**", value="`{0} MB`".format(mem), inline=True)
        embed.add_field(name="**Current CPU usage:**",value="`{0}%`".format(cpu))
        embed.add_field(name="**Active Cores:**", value="`{0} / {1}`".format(cores_used, cores_total))
        embed.add_field(name="**Current Ping**", value="`{0} ms`".format(ping))
        embed.add_field(name="**Meme Status:**", value="`BANNED`")
        embed.color=0x00ff00
        embed.add_field(name="**Status:**", value="`{0}`".format(ass))
        embed.set_footer(text="version: {}".format(self.version))    
        embed.set_thumbnail(url=str(self.bot.user.avatar_url))
        await ctx.trigger_typing()
        await ctx.send(embed=embed)

    @commands.command()
    async def about(self, ctx):
        embed=discord.Embed(title="about {0}".format(self.bot.user.name), description="{0} is a Discord Bot made By ThatRedKite".format(self.bot.user.name))
        embed.add_field(name="Author:", value="`ThatRedKite#0815`")
        embed.add_field(name="License:", value="`MIT`")
        embed.add_field(name="Version:", value="`{0}`".format(self.version))
        embed.add_field(name="Copyright", value="`©2020`")
        embed.set_thumbnail(url=str(self.bot.user.avatar_url))
        embed.color=0x00ff00
        embed.set_footer(text="why am I here?")
        await ctx.trigger_typing()
        await ctx.send(embed=embed)

    @commands.command()
    async def license(self, ctx):
        embed=discord.Embed(title="This product is licensed under the MIT License",
                                    description="look at https://opensource.org/licenses/MIT if you want to read it")
        embed.color=0x00ffff
        await ctx.trigger_typing()
        await ctx.send(embed=embed)

    @commands.command()
    async def userinfo(self, ctx, mention="asdf"):
        message=ctx.message
        user_mentions = message.mentions
        if len(user_mentions) > 0:
            # set :user: to the first user mentioned
            user = user_mentions[0] 
            is_user = True 
        else:
            rest=re.findall("(\d+)", mention)
            if len(rest) > 0 :
                is_user=True
                # set :user: to the user mentioned by id
                user=self.bot.get_user(int(rest[0]))
            else:
                user=ctx.message.author # set :user: to the user who issued the command
                is_usernel=True 
        username=user.name
        userid=user.id
        isbot=user.bot
        creationtime=user.created_at.strftime("%d.%m.%Y\n@%H:%M UTC")
        if isbot is not True:
            embed=discord.Embed(title=f"UserInfo for the user {username}")
            embed.add_field(name="Is Bot?", value="\n\n❌")
        else:
            embed=discord.Embed(title=f"BotInfo for the bot {username}")
            embed.add_field(name="Is Bot?", value="✅")
        embed.set_thumbnail(url=str(user.avatar_url))
        embed.add_field(name="creation date:", value=f"```py\n{creationtime}```")
        embed.add_field(name="id", value=f"```fix\n{userid}```")
        await ctx.send(embed=embed)

    @commands.cooldown(1,10,commands.BucketType.user)
    @commands.command()
    async def man(self,ctx,*,args):
        command=["man"]
        sep=';'
        rest=args.split(sep, 1)[0]
        construct=rest.split(" ")
        if type(construct) == list:
            for x in construct:
                command.append(str(x))
        with subprocess.Popen(command, stdout=subprocess.PIPE) as idk:
            text=idk.stdout.read().decode("utf-8")
            chunk_length=2010
            segments=[text[i:i+chunk_length] for i in range(0, len(text), chunk_length)]
            segments.reverse()
            for x in segments:
                xtext=str(x)
                embed=discord.Embed(title=f"Manual entry for the command {args}", description=xtext)
                await ctx.send(embed=embed)
                
    @commands.command()
    async def color(self,ctx,*,args):
        # broken for some reason, need to fix it   
        if len(args.split(" ")) == 1:
            color=int(args[0],16)
            img=Image.new("RGB", (128,128), )
            img.save(f"{self.dirname}/data/color.png")
            file=discord.File(f"{self.dirname}/data/color.png", filename="color.png")
            embed=discord.Embed()
            embed.color=discord.Color(color)
            embed.set_image(url="attachment://color.png")
            embed.set_footer(text=f"color values: HEX:{args}")
            await ctx.send(file=file, embed=embed)
            img.close()
        else:
            try: 
                r, g, b=args.split(" ")
                img=Image.new("RGB", (128,128), (int(r),int(g),int(b)))
                img.save(f"{self.dirname}/data/color.png")
                file=discord.File(f"{self.dirname}/data/color.png", filename="color.png")
                embed=discord.Embed()
                embed.set_image(url="attachment://color.png")
                embed.set_footer(text=f"color values: RGB: {args} ; HEX: {'#%02x%02x%02x'.upper() % (int(r),int(g),int(b))}")
                await ctx.send(file=file, embed=embed)
                img.close()
            except Exception as exc:
                print(exc)
                await errormsg(ctx, "Please check your inputs!")

    @commands.command()
    async def settings(self, ctx):
        embed = discord.Embed(title="**settings**")
        for setting in self.bot.settings[str(ctx.guild.id)]:
            embed.add_field(name=f"**{setting}:**", value=f"```py\n{self.bot.settings[setting]}```", inline=True)
        await ctx.send(embed=embed) 

    @commands.command()
    async def help(self,ctx):
        embed = discord.Embed(title="**a list of the bot's commands**")
        for cog in self.bot.cogs:
            commandstring = "" 
            for command in self.bot.get_cog(cog).walk_commands():
                if cog != "NSFW":
                    commandstring += f"{command}\n"
            if len(commandstring) > 1:
                embed.add_field(name=f"__**[{cog}]**__", value=f"```fix\n{commandstring}```",inline=False) 
        embed.set_footer(text=f"\nThatKiteBot² version {self.bot.version}", icon_url=self.bot.user.avatar_url)
        await ctx.send(embed=embed)
