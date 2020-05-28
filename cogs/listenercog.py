from discord.ext import commands, tasks
import discord
import  string
from bf.yamler import  Yamler
import random
import asyncio
from bf import url
import re
class Listeners(commands.Cog):
    def __init__(self, bot, dirname,):
        self.dirname = dirname
        self.active = 0
        self.bot:discord.Client = bot
        self._last_member = None
        self.counter = 0
        
    @commands.Cog.listener()
    async def on_message(self, message:discord.Message):
        channel :discord.TextChannel = self.bot.get_channel(message.channel.id)
        userid = message.author.id
        self.banlist = []
        guild :discord.Guild = channel.guild 
        content = message.content.lower()
        zolllist = ["halt", "halt!", "halt zoll", "halt zoll!","zoll", "zoll!"]

        if message.content.lower() in zolllist:
            choice = random.randint(0,1)
            if choice == 0:
                emojilist = ["HALTZOLL", "HALTZOLL2"]
                emoji = discord.utils.get(guild.emojis, name=random.choice(emojilist))
                await message.add_reaction(emoji)
            if choice == 1:
                if message.content.lower().startswith("halt") and message.author.id != self.bot.user.id:
                    await channel.send("ZOLL!")
                if message.content.lower().startswith("zoll") and message.author.id != self.bot.user.id:
                    await  channel.send("HALT!")
        
        if channel.id == 693167481027690527 and len(re.findall("yi[f]+|fu[ry]+", str(message.content).lower())) and message.author.id != self.bot.user.id:
            if self.counter == 0:
                await channel.send("🚨 🚨 🚨**__WARNING, do not say that again!__**🚨 🚨 🚨")
                self.counter += 1
            elif self.counter == 1:
                await channel.send("__**are you sure you wanna say that again????**__")
                self.counter += 1
            elif self.counter == 2:
                await channel.send("🚨 🚨 🚨**__THIS IS YOUR FINAL WARNING!__**🚨 🚨 🚨")
                self.counter += 1                
            else:
                await channel.send("Well, seems like you didn't listen \n deploying yiff in **3 seconds**")
                await asyncio.sleep(1)
                payload = {"tags": ["canine", "cock", "canine_penis"], "limit": 320}
                urllist = await url.monosodiumcarbonate(payload, "page")
                for x in range(5):
                    choice = random.choice(urllist)
                    embed = discord.Embed(title="**You have been warned**", url=choice)
                    embed.color = 0xff00cc
                    embed.set_image(url=choice)
                    await channel.send(embed=embed)
                self.counter = 0

        elif len(re.findall("busbr", str(message.content).lower())) and message.author.id != self.bot.user.id:
            choice = random.randint(0,100)
            if choice < 100:
                emoji = discord.utils.get(guild.emojis, name="busbr_irl")
                await message.add_reaction(emoji)
            else:
                emoji:discord.Emoji = discord.utils.get(guild.emojis, name="busbr_irl")
                await channel.send(f"<:busbr_irl:{emoji.id}>")

    @commands.Cog.listener()
    async def on_ready(self):
        print("Bot is up and running!")
    