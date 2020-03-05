from discord.ext import commands
import discord
import  string
from bf.yamler import  Yamler
import random
class Listeners(commands.Cog):
    def __init__(self, bot, dirname):
        self.active = 0
        self.bot = bot
        self._last_member = None
        self.dirname = dirname
    @commands.Cog.listener()
    async def on_message(self, message :discord.Message):
        channel :discord.TextChannel = self.bot.get_channel(message.channel.id)
        userid = message.author.id
        guild :discord.Guild = channel.guild 
        yam = Yamler("{0}/data/banlist.yml".format(self.dirname))
        self.banlist = yam.load()
        content = message.content.lower()

        zolllist = ["halt", "halt!", "halt zoll", "halt zoll!","zoll", "zoll!"]

        if message.content.lower() in zolllist:
            emojilist = ["HALTZOLL", "HALTZOLL2"]
            emoji = discord.utils.get(guild.emojis, name=random.choice(emojilist))
            await message.add_reaction(emoji)
        else:
            for word in content.split(" "):
                if word in self.banlist and message.author.id == 142705172395589632:
                    await message.delete()
        

        
