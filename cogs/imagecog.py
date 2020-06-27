import re
import os
import discord
import asyncio
import typing
from bf import  util
from io import BytesIO
from requests import get
from random import choice
from datetime import datetime
from wand.display import display
from discord.ext import commands
from wand import image as wandimg
from cogs.funstuffcog import mark
from PIL import Image, ImageDraw, ImageFont
from concurrent.futures import  ThreadPoolExecutor, ProcessPoolExecutor

def image_url_fetcher(messages,bypass=False,gif=False):
    if not bypass:
        # list of file types, supports regex syntax
        filetypes=["png","webp","gif","jpe?g"] 
        # some regex tomfuckery
        pattern_generated=f"^(https?://\S+({'|'.join(filetypes)}))"
        if len(messages) > 0: 
            for message in messages:
                attachments=message.attachments
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
        url=messages            
    r=get(url).content
    inbuffer=BytesIO(r)
    if not gif:
        with Image.open(inbuffer) as img:
            outbuffer=BytesIO()
            img=img.convert("RGBA")
            img.save(outbuffer,"png")
        return outbuffer
    else:
        return inbuffer

def deepfried(buffer,path):
    buffer.seek(0)
    with wandimg.Image(file=buffer) as im:
        i:wandimg.Image=im.clone()
        i.transform(resize='300x300>')
        i.adaptive_sharpen(radius=50.0,sigma=10.32)
        i.modulate(saturation=800.00)
        i.noise("gaussian",attenuate=0.1)
        i.save(filename=os.path.join(path,"deepfried.png"))

    image_file=discord.File(os.path.join(path,"deepfried.png"), filename="deepfried.png")
    embed=discord.Embed()
    embed.set_image(url="attachment://deepfried.png")
    return embed, image_file

def do_magik(buffer:BytesIO,path):
    buffer.seek(0)
    with wandimg.Image(file=buffer) as im:
        im.alpha_channel=True
        i:wandimg.Image=im.clone()
        i.alpha_channel=True
        i.liquid_rescale(width=int(i.width*0.5), height=int(i.height*0.5), delta_x=1, rigidity=0)
        i.liquid_rescale(width=int(i.width*2.512), height=int(i.height*2.512), delta_x=2, rigidity=0)
        i.resize(im.width, im.height)
        i.save(filename=os.path.join(path,"magik.png"))

    image_file=discord.File(os.path.join(path,"magik.png"), filename="magik.png")
    embed=discord.Embed()
    embed.set_image(url="attachment://magik.png")
    return embed, image_file

def make_wide(buffer,path):
    buffer.seek(0)
    with wandimg.Image(file=buffer) as img:
        im:wandimg.Image=img.clone()
        width=img.width
        height=img.height
        im.resize(width=int(width * 3), height=int(height / 1.5))
        width=im.width
        height=im.height
        im.crop(left=int(width/4),top=1,right=(width-(int(width/4.3))),bottom=height)
        im.save(filename=os.path.join(path,"wide.png"))

    image_file=discord.File(os.path.join(path,"wide.png"), filename="wide.png")
    embed=discord.Embed()
    embed.set_image(url="attachment://wide.png")
    return embed, image_file

def image_downloader(url,path):
    r=get(url).content
    inbuffer=BytesIO(r)
    with Image.open(inbuffer) as img:
        outbuffer=BytesIO()
        img=img.convert("RGBA")
        img.save(outbuffer,"png")
        img.save(fp=path)
    return outbuffer

def quoter(buffer,chan,path,quotestring):
    buffer.seek(0)
    with Image.open(buffer) as im:
        draw=ImageDraw.Draw(im)
        if im.size <=(512,512):
            a=1
        else:
            a=3
        x,y=im.size
        fontsize=int(x/(int(len(quotestring)/2)+a))
        font=ImageFont.truetype(os.path.join(path,"DejaVuSans.ttf"),fontsize)
        quotestring +=f"\n-{chan.name}"
        draw.text((4-a,(y-int(y / 5))-a),quotestring, (0,0,0), font=font)
        draw.text((4+a,(y-int(y / 5))+a),quotestring, (0,0,0), font=font)
        draw.text((4-a,(y-int(y / 5))+a),quotestring, (0,0,0), font=font)
        draw.text((4+a,(y-int(y / 5))-a),quotestring, (0,0,0), font=font)
        draw.text((4,(y-int(y / 5))-a),quotestring, (255,255,555), font=font)
        im=im.convert("RGBA")
        path = os.path.join(path,"pfp_edit.png")
        im.save(path)
        file=discord.File(os.path.join(path,"pfp_edit.png"), filename="pfp_edit.png")
        embed=discord.Embed()
        embed.set_image(url="attachment://pfp_edit.png")

class image_stuff(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot=bot
        self.path=os.path.join(self.bot.dirname,"data")
        self.localloop=asyncio.get_event_loop()
    
    
    @commands.cooldown(1,5,commands.BucketType.user)
    @commands.command()
    async def quote(self,ctx:commands.Context,user="assa",old:int=100,new:int=100):
        author=ctx.message.author
        with ctx.channel.typing():
            generated_list,chan=await mark(
                                        bot=self.bot,ctx=ctx,
                                        user=user,old=old,
                                        new=new,leng=5,
                                        leng2=30,mode="short")
            with ThreadPoolExecutor() as executor:
                buffer = await self.localloop.run_in_executor(executor,image_url_fetcher,messages=chan.avatar_url,bypass=True)
            
            if len(generated_list) > 0:
                with ThreadPoolExecutor() as executor:
                    embed,file=await self.localloop.run_in_executor(executor,quoter,buffer,chan,self.path)
                embed,file=quoter(buffer,chan,self.path)
                await ctx.send(file=file, embed=embed)


    @commands.cooldown(1,5,commands.BucketType.user)
    @commands.command()
    async def magik(self,ctx:commands.Context):
        with ctx.channel.typing():
            messages=[]
            async for message in ctx.channel.history(limit=50,around=datetime.now()):
                messages.append(message)
            with ThreadPoolExecutor() as executor:
                future=await self.localloop.run_in_executor(executor,image_url_fetcher,messages)
            buffer=future

            with ThreadPoolExecutor() as executor:
                future=await self.localloop.run_in_executor(executor,do_magik,buffer,self.path)
                embed,image_file=future
                await ctx.send(file=image_file)

    # pfp stuff
    @commands.cooldown(1,5,commands.BucketType.user)
    @commands.command()
    async def widepfp(self,ctx:commands.Context,usermention="asdasd"):
        with ctx.channel.typing():
            message=ctx.message
            user,is_user,is_channel=util.mentioner(self.bot,ctx,message,usermention,False)
            with ThreadPoolExecutor() as executor:
                future=executor.submit(image_url_fetcher,user.avatar_url,bypass=True)
            buffer=future.result()
                
            with ThreadPoolExecutor() as executor:
                future=await self.localloop.run_in_executor(executor,make_wide,buffer,self.path)
                embed,image_file=future
                await ctx.send(file=image_file)

    @commands.cooldown(1,5,commands.BucketType.user)
    @commands.command()
    async def pfp(self,ctx,usermention="ass"):
        message=ctx.message
        user,is_user,is_channel=util.mentioner(self.bot,ctx,message,usermention,False)
        with ThreadPoolExecutor() as executor:
            future=await self.localloop.run_in_executor(executor,image_downloader,user.avatar_url,os.path.join(self.path,"pfp.png"))
            image_file=discord.File(os.path.join(self.path,"pfp.png"), filename="pfp.png")
            await ctx.send(file=image_file)

    @commands.cooldown(1,5,commands.BucketType.user)
    @commands.command()
    async def pfpmagik(self,ctx,usermention="nonetti"):
        with ctx.channel.typing():
            message=ctx.message
            user,is_user,is_channel=util.mentioner(self.bot,ctx,message,usermention,False)
            with ThreadPoolExecutor() as executor:
                future=executor.submit(image_url_fetcher,user.avatar_url,bypass=True)
            buffer=future.result()
                
            with ThreadPoolExecutor() as executor:
                future=await self.localloop.run_in_executor(executor,do_magik,buffer,self.path)
                embed,image_file=future
                await ctx.send(file=image_file)
    
    # general image stuff
    @commands.cooldown(1,5,commands.BucketType.user)
    @commands.command()
    async def deepfry(self,ctx:commands.Context):
        with ctx.channel.typing():
            messages=[]
            async for message in ctx.channel.history(limit=50,around=datetime.now()):
                messages.append(message)
            with ThreadPoolExecutor() as executor:
            # get image urls from message history
                future=await self.localloop.run_in_executor(executor,image_url_fetcher,messages)
            buffer=future

            with ThreadPoolExecutor() as executor:
                future=await self.localloop.run_in_executor(executor,deepfried,buffer,self.path)
                embed,image_file=future
                await ctx.send(file=image_file)
        
    @commands.cooldown(1,5,commands.BucketType.user)
    @commands.command()
    async def wide(self,ctx:commands.Context):
        with ctx.channel.typing():
            messages=[]
            async for message in ctx.channel.history(limit=50,around=datetime.now()):
                messages.append(message)
            with ThreadPoolExecutor() as executor:
                future=await self.localloop.run_in_executor(executor,image_url_fetcher,messages)
                
            buffer=future
            with ThreadPoolExecutor() as executor:
                future=await self.localloop.run_in_executor(executor,make_wide,buffer,self.path)
                embed,image_file=future
                await ctx.send(file=image_file)
    

