import discord
from discord.ext import commands
import PIL
import  wand
from datetime import datetime
import re
class image_stuff(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot=bot
        self.path=f"{self.bot.dirname}/data/"

    @commands.command()
    async def test(self,ctx:commands.Context):
        message=ctx.message
        channel:discord.TextChannel=ctx.channel
        async for message in channel.history(limit=50,around=datetime.now()):
            attachments=message.attachments
            for attachment in attachments:
                if attachment is not None:
                    print(attachment.url)

        







