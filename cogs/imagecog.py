import re
import json
import discord
import asyncio
import typing
import subprocess
from bf import  util
from io import BytesIO
from os.path import join
from requests import get
from random import choice
from functools import partial
from datetime import datetime
from wand.display import display
from discord.ext import commands
from wand.image import Image as WandImage
from cogs.funstuffcog import mark
from PIL import Image, ImageDraw, ImageFont
from concurrent.futures import  ThreadPoolExecutor, ProcessPoolExecutor

def image_url_fetcher(messages,api_token:str=None,bypass=False,gif=False):
    if not bypass:
        # list of file types, supports regex syntax
        if not gif:
            filetypes=["png","webp","gif","jpe?g"]
        else:
            filetypes=["gif"]
        # some regex tomfuckery
        pattern_generated=f"^(https?://\S+({'|.'.join(filetypes)}))"
        tenorpattern="^https://tenor.com\S+-(\d+)$"
        if len(messages) > 0: 
            for message in messages:
                attachments=message.attachments
                if len(attachments) > 0:
                    donkey=re.findall(pattern_generated,attachments[0].url)
                    url, filetype=donkey[0]
                    break
                else:
                    donkey=re.findall(pattern_generated,message.clean_content)
                    tenor=re.findall(tenorpattern,message.clean_content)
                    if donkey is not None and len(donkey) > 0 and len(tenor) == 0:
                        url, filetype=donkey[0]
                        break
                    elif tenor is not None and len(tenor) > 0:
                        payload = {"key":api_token,"ids":int(tenor[0]),"media_filter":"minimal"}
                        r=get(url="https://api.tenor.com/v1/gifs",params=payload)
                        gifs=json.loads(r.content)
                        url=gifs["results"][0]["media"][0]["gif"]["url"]
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
    with WandImage(file=buffer) as im:
        i:WandImage=im.clone()
        i.transform(resize='300x300>')
        i.adaptive_sharpen(radius=50.0,sigma=10.32)
        i.modulate(saturation=800.00)
        i.noise("gaussian",attenuate=0.1)
        i.save(filename=join(path,"deepfried.png"))

    image_file=discord.File(join(path,"deepfried.png"), filename="deepfried.png")
    embed=discord.Embed()
    embed.set_image(url="attachment://deepfried.png")
    return embed, image_file

def do_magik(buffer:BytesIO,path):
    buffer.seek(0)
    with WandImage(file=buffer) as im:
        im.alpha_channel=True
        i:WandImage=im.clone()
        i.alpha_channel=True
        i.liquid_rescale(width=int(i.width*0.5), height=int(i.height*0.5), delta_x=1, rigidity=0)
        i.liquid_rescale(width=int(i.width*2.512), height=int(i.height*2.512), delta_x=2, rigidity=0)
        i.resize(im.width, im.height)
        i.save(filename=join(path,"magik.png"))

    image_file=discord.File(join(path,"magik.png"), filename="magik.png")
    embed=discord.Embed()
    embed.set_image(url="attachment://magik.png")
    return embed, image_file

def make_wide(buffer,path):
    buffer.seek(0)
    with WandImage(file=buffer) as img:
        im:WandImage=img.clone()
        im.resize(width=int(img.width * 3), height=int(img.height / 1.5))
        im.crop(left=int(im.width/4),top=1,right=(im.width-(int(im.width/4.3))),bottom=im.height)
        im.save(filename=join(path,"wide.png"))

    image_file=discord.File(join(path,"wide.png"), filename="wide.png")
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
        draw = ImageDraw.Draw(im)
        if im.size <=(512,512):
            a=1
        else:
            a=3
        x,y=im.size
        fontsize=int(x/(int(len(quotestring)/2)+a))
        font=ImageFont.truetype(join(path,"DejaVuSans.ttf"),fontsize)
        quotestring +=f"\n-{chan.name}"
        draw.text((4-a,(y-int(y/5))-a),quotestring,(0,0,0),font=font)
        draw.text((4+a,(y-int(y/5))+a),quotestring,(0,0,0),font=font)
        draw.text((4-a,(y-int(y/5))+a),quotestring,(0,0,0),font=font)
        draw.text((4+a,(y-int(y/5))-a),quotestring,(0,0,0),font=font)
        draw.text((4,(y-int(y/5))-a),quotestring, (255,255,555),font=font)
        im=im.convert("RGBA")
        path = join(path,"pfp_edit.png")
        im.save(path)

        file=discord.File(join(path),filename="pfp_edit.png")
        embed=discord.Embed()
        embed.set_image(url="attachment://pfp_edit.png")
        return embed,file

def do_gmagik(inbuffer,path,dry=False,deepfry=False,wide=False):
    durations=[]
    positions=[]
    with Image.open(inbuffer) as img:
        with BytesIO() as buffer:
            with WandImage() as wand:
                for frame in range(img.n_frames):
                    img.seek(frame); im=img
                    if not dry:
                        im=im.convert("RGB")
                    positions.append(buffer.tell())
                    im.save(buffer,format="PNG",quality=0)
                    durations.append(img.info["duration"])
                    buffer.seek(positions[frame])
                    with WandImage(file=buffer) as im:
                        if not dry:
                            if not deepfry and not wide:
                                im.resize(
                                    width=int(im.width*0.5-frame/100),
                                    height=int(im.height*0.5-frame/100))
    
                                im.liquid_rescale(
                                    width=int(im.width*0.6),
                                    height=int(im.height*0.6),
                                    delta_x=1,
                                    rigidity=0)

                                im.liquid_rescale(
                                    width=int(im.width*1.932),
                                    height=int(im.height*1.931),
                                    delta_x=2,
                                    rigidity=0)

                                im.resize(
                                width=int(im.width*1.5),
                                height=int(im.height*1.5))

                            elif wide and not deepfry:
                                im.resize(width=int(img.width * 3), height=int(img.height / 1.5))
                                im.crop(left=int(im.width/4),top=1,right=(im.width-(int(im.width/4.3))),bottom=im.height)

                            elif deepfry and not wide:
                                im.transform(resize='300x300>')
                                im.adaptive_sharpen(radius=50.0,sigma=20.32)
                                im.modulate(saturation=900.00)
                                im.noise("gaussian",attenuate=0)

                        wand.sequence.append(im)
                        wand.sequence[frame].delay=int(durations[frame] / 10)
                wand.type="optimize"
                wand.save(filename=join(path,"gmagik.gif"))

    image_file=discord.File(join(path,"gmagik.gif"), filename="gmagik.gif")
    embed=discord.Embed()
    embed.set_image(url="attachment://gmagik.gif")
    return embed, image_file

class image_stuff(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot=bot
        self.path=bot.tempdir
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
                buffer = await self.localloop.run_in_executor(executor,partial(
                    image_url_fetcher,
                    messages=chan.avatar_url,
                    bypass=True))

                if len(generated_list) > 0:
                        quotestring=choice(generated_list)
                        embed,file=await self.localloop.run_in_executor(executor,quoter,buffer,chan,self.path,quotestring)
                await ctx.send(file=file, embed=embed)

    @commands.cooldown(1,5,commands.BucketType.user)
    @commands.command()
    async def magik(self,ctx:commands.Context):
        with ctx.channel.typing():
            messages=[]
            async for message in ctx.channel.history(limit=50,around=datetime.now()):
                messages.append(message)

            with ThreadPoolExecutor() as executor:
                buffer=await self.localloop.run_in_executor(executor,image_url_fetcher,messages)
                future=await self.localloop.run_in_executor(executor,do_magik,buffer,self.path)
                embed,image_file=future
                await ctx.send(file=image_file)

    @commands.cooldown(1,5,commands.BucketType.user)
    @commands.command()
    async def widepfp(self,ctx:commands.Context,usermention="asdasd"):
        with ctx.channel.typing():
            message=ctx.message
            user,is_user,is_channel=util.mentioner(self.bot,ctx,message,usermention,False)
            with ThreadPoolExecutor() as executor:
                buffer=await self.localloop.run_in_executor(executor,partial(
                    image_url_fetcher,
                    messages=user.avatar_url,
                    bypass=True))
                embed,image_file=await self.localloop.run_in_executor(executor,make_wide,buffer,self.path)
                await ctx.send(file=image_file)

    @commands.cooldown(1,5,commands.BucketType.user)
    @commands.command()
    async def pfp(self,ctx,usermention="ass"):
        message=ctx.message
        user,is_user,is_channel=util.mentioner(self.bot,ctx,message,usermention,False)
        with ThreadPoolExecutor() as executor:
            future=await self.localloop.run_in_executor(executor,image_downloader,user.avatar_url,join(self.path,"pfp.png"))
            image_file=discord.File(join(self.path,"pfp.png"), filename="pfp.png")
            await ctx.send(file=image_file)

    @commands.cooldown(1,5,commands.BucketType.user)
    @commands.command()
    async def pfpmagik(self,ctx,usermention="nonetti"):
        with ctx.channel.typing():
            message=ctx.message
            user,is_user,is_channel=util.mentioner(self.bot,ctx,message,usermention,False)
            with ThreadPoolExecutor() as executor:
                buffer=await self.localloop.run_in_executor(executor,partial(
                    image_url_fetcher,
                    messages=user.avatar_url,
                    bypass=True))

                embed,image_file=await self.localloop.run_in_executor(executor,do_magik,buffer,self.path)
                await ctx.send(file=image_file)
    
    @commands.cooldown(1,5,commands.BucketType.user)
    @commands.command()
    async def deepfry(self,ctx:commands.Context):
        with ctx.channel.typing():
            messages=[]
            async for message in ctx.channel.history(limit=50,around=datetime.now()):
                messages.append(message)
                
            with ThreadPoolExecutor() as executor:
            # get image urls from message history
                buffer=await self.localloop.run_in_executor(executor,image_url_fetcher,messages)
                embed,image_file=await self.localloop.run_in_executor(executor,deepfried,buffer,self.path)
                await ctx.send(file=image_file)
        
    @commands.cooldown(1,5,commands.BucketType.user)
    @commands.command()
    async def wide(self,ctx:commands.Context):
        with ctx.channel.typing():
            messages=[]
            async for message in ctx.channel.history(limit=50,around=datetime.now()):
                messages.append(message)

            with ThreadPoolExecutor() as executor:
                buffer=await self.localloop.run_in_executor(executor,image_url_fetcher,messages)
                embed,image_file=await self.localloop.run_in_executor(executor,make_wide,buffer,self.path)
                await ctx.send(file=image_file)
    

    @commands.cooldown(1,5,commands.BucketType.user)
    @commands.command()
    async def gmagik(self,ctx:commands.Context,mode:str=""):
        if mode.lower() == "deepfry":
            deepfry=True
            wide=False
        elif mode.lower() == "wide":
            deepfry=False
            wide=True
        else:
            deepfry=False
            wide=False    

        with ctx.channel.typing():
            messages=[]
            async for message in ctx.channel.history(limit=50,around=datetime.now()):
                messages.append(message)

            with ThreadPoolExecutor() as executor:
                buffer=await self.localloop.run_in_executor(executor,partial(
                    image_url_fetcher,
                    gif=True,
                    messages=messages,
                    api_token=self.bot.tom.tenortoken))
                embed,image_file=await self.localloop.run_in_executor(executor,partial(
                    do_gmagik,
                    buffer,
                    self.path,
                    deepfry=deepfry,
                    wide=wide))
                await ctx.send(file=image_file)