import discord
import random
import re
import requests
import os
import typing
from cogs.funstuffcog import fun_stuff
from io import BytesIO
from datetime import datetime
from wand.display import display
from discord.ext import commands
from wand import image as wandimg
from PIL import Image, ImageDraw, ImageFont
from concurrent.futures import  ThreadPoolExecutor

class image_stuff(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot=bot
        self.path=f"{self.bot.dirname}/data"
    
    def image_url_fetcher(self,messages:list=[],bypass=False,gif=False):
        if not bypass:
            # list of file types, supports regex syntax
            filetypes = ["png","webp","gif","jpe?g"] 
            # some regex tomfuckery
            pattern_generated = f"^(https?://\S+({'|'.join(filetypes)}))"
            if len(messages) > 0: 
                for message in messages:
                    attachments = message.attachments
                    if len(attachments) > 0:
                        donkey=re.findall(pattern_generated,attachments[0].url)
                        url, filetype=donkey[0]
                        break
                    else:
                        donkey=re.findall(pattern_generated,message.clean_content)
                        if donkey is not None and len(donkey) > 0:
                            url, filetype=donkey[0]
                            break
        else:
            url = str(messages[0])                
        r = requests.get(url).content
        inbuffer = BytesIO(r)
        if not gif:
            with Image.open(inbuffer) as img:
                outbuffer = BytesIO()
                img = img.convert("RGBA")
                img.save(outbuffer,"png")
            return outbuffer
        else:
            return inbuffer

                        
        
    def do_magik(self,buffer:BytesIO):
        buffer.seek(0)
        with wandimg.Image(file=buffer) as im:
            im.alpha_channel=True
            i=im.clone()
            i.alpha_channel=True
            i.transform(resize='797x804>')
            i.liquid_rescale(width=int(i.width*0.4), height=int(i.height*0.4), delta_x=1, rigidity=0)
            i.liquid_rescale(width=int(i.width*1.75233), height=int(i.height*1.75233), delta_x=2, rigidity=0)
            i.resize(i.width, i.height)
            i.save(filename=f"{self.path}/magik.png")

        image_file = discord.File(f"{self.path}/magik.png", filename="magik.png")
        embed = discord.Embed()
        embed.set_image(url="attachment://magik.png")
        return embed, image_file


    def deepfried(self,buffer):
        buffer.seek(0)
        with wandimg.Image(file=buffer) as im:
            i:image.Image = im.clone()
            i.transform(resize='300x300>')
            i.adaptive_sharpen(radius=50.0,sigma=10.32)
            i.modulate(saturation=800.00)
            i.noise("gaussian",attenuate=0.1)
            i.save(filename=f"{self.path}/deepfried.png")

        image_file = discord.File(f"{self.path}/deepfried.png", filename="deepfried.png")
        embed = discord.Embed()
        embed.set_image(url="attachment://deepfried.png")
        return embed, image_file
    
    @commands.cooldown(1,5,commands.BucketType.user)
    @commands.command()
    async def magik(self,ctx:commands.Context):
        with ctx.channel.typing():
            messages = []
            async for message in ctx.channel.history(limit=50,around=datetime.now()):
                messages.append(message)
            pool=ThreadPoolExecutor()
            # get image urls from message history
            future=pool.submit(self.image_url_fetcher,messages)
            buffer=future.result()

            future=pool.submit(self.do_magik,buffer)
            embed,image_file=future.result()

        await ctx.send(file=image_file)
    
    @commands.cooldown(1,5,commands.BucketType.user)
    @commands.command()
    async def pfpmagik(self,ctx,usermention="nonetti"):
        with ctx.channel.typing():
            message=ctx.message
            user_mentions = message.mentions
            if len(user_mentions) > 0:
                # set :user: to the first user mentioned
                user = user_mentions[0] 
                is_user = True 
            else:
                rest=re.findall("(\d+)", usermention)
                if len(rest) > 0 :
                    is_user=True
                    # set :user: to the user mentioned by id
                    user=self.bot.get_user(int(rest[0]))
                else:
                    user=ctx.message.author # set :user: to the user who issued the command
                    is_usernel=True 

            pool=ThreadPoolExecutor()
            # get image urls from message history
            future=pool.submit(self.image_url_fetcher,[user.avatar_url],bypass=True)
            buffer=future.result()
            future=pool.submit(self.do_magik,buffer)
            embed,image_file=future.result()

        await ctx.send(file=image_file)
    
    @commands.cooldown(1,5,commands.BucketType.user)
    @commands.command()
    async def deepfry(self,ctx:commands.Context):
        with ctx.channel.typing():
            messages = []
            async for message in ctx.channel.history(limit=50,around=datetime.now()):
                messages.append(message)
            pool=ThreadPoolExecutor()
            # get image urls from message history
            future=pool.submit(self.image_url_fetcher,messages)
            buffer=future.result()
            
            future=pool.submit(self.deepfried,buffer)
            embed,image_file=future.result()

        await ctx.send(file=image_file)

    @commands.command()
    async def quote(self,ctx,user="assa",old:int=100,new:int=100):
        guild=ctx.guild
        author: discord.User=ctx.message.author
        with ctx.channel.typing():
            generated_list, chan=await fun_stuff.mark(ctx,user,old,new,5,30,mode="short")
            r=requests.get(chan.avatar_url).content
            buffer = BytesIO(r)
            def imager(buffer):
                buffer.seek(0)
                with Image.open(buffer) as im:
                    if len(generated_list) > 0:
                        quotestring= random.choice(generated_list)
                        draw=ImageDraw.Draw(im)
                        if im.size <= (512,512):
                            a=1
                        else:
                            a=3
                        x,y=im.size
                        fontsize = int(x/(int(len(quotestring)/2)+a))
                        font=ImageFont.truetype(f"{self.dirname}/data/DejaVuSans.ttf", fontsize)
                        quotestring += f"\n-{chan.name}"
                        draw.text((4-a,(y-int(y / 5))-a),quotestring, (0,0,0), font=font)
                        draw.text((4+a,(y-int(y / 5))+a),quotestring, (0,0,0), font=font)
                        draw.text((4-a,(y-int(y / 5))+a),quotestring, (0,0,0), font=font)
                        draw.text((4+a,(y-int(y / 5))-a),quotestring, (0,0,0), font=font)
                        draw.text((4,(y-int(y / 5))-a),quotestring, (255,255,555), font=font)
                        im.save(f"{self.dirname}/data/pfp_edit.webp")
                    else:
                        raise Exception
            with ThreadPoolExecutor(5) as executor:
                executor.submit(imager,buffer)
        
        file=discord.File(f"{self.dirname}/data/pfp_edit.webp", filename="pfp_edit.webp")
        embed=discord.Embed()
        embed.set_image(url="attachment://pfp_edit.webp")
        await ctx.send(file=file, embed=embed)
        
    