from ctypes import sizeof
import re
import discord
import argparse
from queue import Queue
import gc
from bf import  util
from io import BytesIO
from os.path import join
from random import choice
from functools import partial
from datetime import datetime
from discord.ext import commands
from wand.image import Image as WandImage
from cogs.funstuffcog import mark
from PIL import Image, ImageDraw, ImageFont, ImageFile
from concurrent.futures import  ThreadPoolExecutor, ProcessPoolExecutor

class NoExitParser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)

def deepfried(buffer,path):
    buffer.seek(0)
    with WandImage(file=buffer) as img:
        img.modulate(saturation=800.00)
        img.noise("gaussian",attenuate=0.1)
        with BytesIO() as outbuffer:
            img.save(file=outbuffer)
            outbuffer.seek(0)
            image_file=discord.File(outbuffer, filename="deepfried.png")
        
        buffer.close()
        del img,outbuffer
        embed=discord.Embed()
        embed.set_image(url="attachment://deepfried.png")
        return embed, image_file
    
def do_magik(buffer:BytesIO,path):
    buffer.seek(0)
    with WandImage(file=buffer) as i:
        i.alpha_channel=True
        height,width=i.height,i.width
        i.resize(width=int(i.width*3), height=int(i.height/1.2))
        i.liquid_rescale(width=int(i.width*0.5),height=int(i.height*0.5),delta_x=1,rigidity=0)
        i.liquid_rescale(width=int(i.width*2.512),height=int(i.height*2.512),delta_x=2,rigidity=0)

        i.resize(width, height)
        with BytesIO() as outbuffer:
            i.save(file=outbuffer)
            outbuffer.seek(0)
            image_file=discord.File(outbuffer, filename="magik.png")
        del i,outbuffer
        buffer.close()
        embed=discord.Embed()
        embed.set_image(url="attachment://magik.png")
        return embed, image_file

def make_wide(buffer,path):
    buffer.seek(0)
    with WandImage(file=buffer) as img:
        img.resize(width=int(img.width * 3), height=int(img.height / 1.7))
        img.crop(left=int(img.width/4),top=1,right=(img.width-(int(img.width/4.3))),bottom=img.height)
        with BytesIO() as outbuffer:
            img.save(file=outbuffer)
            outbuffer.seek(0)
            image_file=discord.File(outbuffer, filename="wide.png")

        embed=discord.Embed()
        embed.set_image(url="attachment://wide.png")
        buffer.close()
        del img,outbuffer
        return embed, image_file

def quoter(buffer,chan,path,quotestring):
    buffer.seek(0)
    with Image.open(buffer) as im:
        draw = ImageDraw.Draw(im)
        if im.size <=(512,512):
            outline_width=1
        else:
            outline_width=3
        x,y=im.size
        fontsize=int(x/(int(len(quotestring)/2)+outline_width))
        font=ImageFont.truetype(join(path,"DejaVuSans.ttf"),fontsize)
        quotestring +=f"\n-{chan.name}"
        draw.text((4-outline_width,(y-int(y/5))-outline_width),quotestring,(0,0,0),font=font)
        draw.text((4+outline_width,(y-int(y/5))+outline_width),quotestring,(0,0,0),font=font)
        draw.text((4-outline_width,(y-int(y/5))+outline_width),quotestring,(0,0,0),font=font)
        draw.text((4+outline_width,(y-int(y/5))-outline_width),quotestring,(0,0,0),font=font)
        draw.text((4,(y-int(y/5))-outline_width),quotestring, (255,255,555),font=font)
        im=im.convert("RGBA")
        
        with BytesIO() as outbuffer:
            im.save(outbuffer)
            del im,draw,x,y,fontsize,font,quotestring
            file=discord.File(outbuffer,filename="pfp_edit.png")
            embed=discord.Embed()
            embed.set_image(url="attachment://pfp_edit.png")
        buffer.close()
        del buffer
        return embed,file

def do_gmagik(inbuffer,path,dry=False,deepfry=False,wide=False,speedup=False,caption:tuple=(False,"")):
    durations=Queue()
    positions=Queue()
    with Image.open(inbuffer) as img:
        with BytesIO() as buffer:
            with WandImage() as wand:
                for frame in range(img.n_frames):
                    img.seek(frame); im=img
                    im=im.convert("RGBA")
                    caption_bool,caption_text=caption
                    if caption_bool:
                        assert caption_text != ""
                        outline_width=3
                        W,H=im.size
                        font=ImageFont.truetype(join(path,"DejaVuSans.ttf"),size=52)
                        w,h=font.getsize(caption_text)
                        im=im.convert("RGBA")
                        draw=ImageDraw.Draw(im)
                        draw.text(((W-w)/2-outline_width,int((H-h)/1.15)-outline_width),caption_text,fill="black",font=font)
                        draw.text(((W-w)/2-outline_width,int((H-h)/1.15)+outline_width),caption_text,fill="black",font=font)
                        draw.text(((W-w)/2+outline_width,int((H-h)/1.15)-outline_width),caption_text,fill="black",font=font)
                        draw.text(((W-w)/2+outline_width,int((H-h)/1.15)+outline_width),caption_text,fill="black",font=font)
                        draw.text(((W-w)/2,int((H-h)/1.15)), caption_text, fill="white",font=font)
                        dry=True
                        
                    positions.put(buffer.tell())
                    im.save(buffer,format="GIF")
                    durations.put(img.info["duration"])
                    buffer.seek(positions.get())
                    with WandImage(file=buffer) as im:
                        if not dry:
                            if not deepfry and not wide:
                                
                                im.resize(
                                    width=int(im.width*0.7),
                                    height=int(im.height*0.7))
                                
                                im.liquid_rescale(
                                    width=int(im.width*0.5),
                                    height=int(im.height*0.5),
                                    delta_x=1,
                                    rigidity=0)

                                im.liquid_rescale(
                                    width=int(im.width*3.112),
                                    height=int(im.height*3.112),
                                    delta_x=2, rigidity=0)

                            elif wide and not deepfry:
                                im.resize(width=int(img.width * 3), height=int(img.height / 1.5))
                                im.crop(left=int(im.width/4),top=1,right=(im.width-(int(im.width/4.3))),bottom=im.height)

                            elif deepfry and not wide:
                                #im.adaptive_sharpen(radius=50.0,sigma=10.32)
                                im.modulate(saturation=500.00)
                                im.noise("random",attenuate=0.9)

                        wand.sequence.append(im)
                        if not speedup:
                            wand.sequence[frame].delay=int(durations.get() / 10)
                        else:
                            wand.sequence[frame].delay=int(round(durations.get() / 25))
                        gc.collect()
                        print(frame)
                        
                with BytesIO() as outbuffer:
                    wand.type="optimize"
                    wand.save(file=outbuffer)
                    outbuffer.seek(0)
                    image_file=discord.File(outbuffer, filename="gmagik.gif")
                    embed=discord.Embed()
                    embed.set_image(url="attachment://gmagik.gif")
                    gc.collect()
                    return embed, image_file
                    
class image_stuff(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot=bot
        self.path=bot.tempdir

    async def image_url_fetcher(self,ctx,api_token:str=None,bypass=False,gif=False):
        if not bypass:
            if not gif:
                filetypes=["png","webp","gif","jpe?g"]
            else:
                filetypes=["gif"]
            tenorpattern=re.compile("^https://tenor.com\S+-(\d+)$")
            pattern_generated=re.compile(f"^(https?://\S+({'|.'.join(filetypes)}))")
            async for message in ctx.channel.history(limit=50,around=datetime.now()):
                attachments=message.attachments
                if len(attachments) > 0:
                    donkey=pattern_generated.findall(attachments[0].url)
                    if len(donkey) > 0:
                        url,filetype=donkey[0]
                        break
                    else:
                        continue
                else:
                    donkey=pattern_generated.findall(message.clean_content)
                    tenor=tenorpattern.findall(message.clean_content)
                    if donkey is not None and len(donkey) > 0 and len(tenor) == 0:
                        url, filetype=donkey[0]
                        del tenor,donkey,filetype
                        break
                    elif tenor is not None and len(tenor) > 0:
                        payload = {"key":api_token,"ids":int(tenor[0]),"media_filter":"minimal"}
                        async with self.bot.aiohttp_session.get(url="https://api.tenor.com/v1/gifs",params=payload) as r:
                            gifs= await r.json()
                        url=str(gifs["results"][0]["media"][0]["gif"]["url"])
                        assert url != ""
                        del tenor,donkey
                        break
        else:
            url=str(ctx)
        assert url != ""
        del tenorpattern,pattern_generated
        async with self.bot.aiohttp_session.get(url) as r:
            inbuffer=BytesIO(await r.read())
            if not gif:
                ImageFile.LOAD_TRUNCATED_IMAGES=True
                inbuffer.seek(0)
                with Image.open(inbuffer) as img:
                    outbuffer=BytesIO()
                    with img.convert("RGBA") as outimg:
                        outbuffer.seek(0)
                        outimg.save(outbuffer,"png")
                return outbuffer
            else:
                inbuffer.seek(0)
                gc.collect()
                return inbuffer

    async def captioner(self,buffer,text,size):
        buffer.seek(0)
        with Image.open(buffer) as img:
            outline_width=3

            W,H=img.size
            font=ImageFont.truetype(join(self.path,"DejaVuSans.ttf"),size=size)
            w,h=font.getsize(text)
            img=img.convert("RGB")
            draw=ImageDraw.Draw(img)
           
            draw.text(((W-w)/2-outline_width,int((H-h)/1.15)-outline_width),text,fill="black",font=font)
            draw.text(((W-w)/2-outline_width,int((H-h)/1.15)+outline_width),text,fill="black",font=font)
            draw.text(((W-w)/2+outline_width,int((H-h)/1.15)-outline_width),text,fill="black",font=font)
            draw.text(((W-w)/2+outline_width,int((H-h)/1.15)+outline_width),text,fill="black",font=font)

            draw.text(((W-w)/2,int((H-h)/1.15)), text, fill="white",font=font)
        
            with BytesIO() as outbuffer:
                img.save(outbuffer,"JPEG",quality=100)
                outbuffer.seek(0)
                file=discord.File(outbuffer,filename="caption.jpeg")
                embed=discord.Embed()
                embed.set_image(url="attachment://caption.jpeg")
                return embed,file

    @commands.cooldown(1,10,commands.BucketType.user)
    @commands.command()
    async def quote(self,ctx:commands.Context,user="dirnenspross123",old:int=100,new:int=100):
        with ctx.channel.typing():
            generated_list,chan=await mark(
                                        bot=self.bot,ctx=ctx,
                                        user=user,old=old,
                                        new=new,leng=5,
                                        leng2=30,mode="short")
            buffer=await self.image_url_fetcher(ctx=chan.avatar_url,bypass=True)
            with ProcessPoolExecutor() as executor:
                if len(generated_list) > 0:
                        quotestring=choice(generated_list)
                        embed,file=await self.bot.loop.run_in_executor(
                            executor,quoter,
                            buffer,chan,
                            self.path,quotestring)
            await ctx.send(file=file, embed=embed)
            del buffer,embed,file

    @commands.cooldown(1,10,commands.BucketType.user)
    @commands.command()
    async def magik(self,ctx:commands.Context):
        with ctx.channel.typing():
            buffer=await self.image_url_fetcher(ctx=ctx,api_token=self.bot.tom.tenortoken)
            with ProcessPoolExecutor() as executor:
                embed,image_file=await self.bot.loop.run_in_executor(None,do_magik,buffer,self.path)
            await ctx.send(file=image_file)
            del buffer,embed,image_file

    @commands.cooldown(1,10,commands.BucketType.user)
    @commands.command()
    async def widepfp(self,ctx:commands.Context,usermention="transfergesetz"):
        with ctx.channel.typing():
            message=ctx.message
            
            chan,is_user,is_channel=util.mentioner(self.bot,ctx,message,usermention,False)
            buffer = await self.image_url_fetcher(ctx=chan.avatar_url, bypass=True)
            with ThreadPoolExecutor() as executor:
                
                embed,image_file=await self.bot.loop.run_in_executor(executor,make_wide,buffer,self.path)
            await ctx.send(file=image_file)
            del buffer,embed,image_file

    @commands.cooldown(1,10,commands.BucketType.user)
    @commands.command()
    async def pfp(self,ctx,usermention="passatwind"):
        message=ctx.message
        chan,is_user,is_channel=util.mentioner(self.bot,ctx,message,usermention,False)
        buffer=await self.image_url_fetcher(ctx=chan.avatar_url, bypass=True)
        with ThreadPoolExecutor() as executor:
            buffer.seek(0)
            image_file=discord.File(buffer, filename="pfp.png")
        await ctx.send(file=image_file)
        del buffer,embed,image_file

    @commands.cooldown(1,10,commands.BucketType.user)
    @commands.command()
    async def pfpmagik(self,ctx,usermention="nonetti"):
        with ctx.channel.typing():
            message=ctx.message
            chan,is_user,is_channel=util.mentioner(self.bot,ctx,message,usermention,False)
            buffer=await self.image_url_fetcher(ctx=chan.avatar_url, bypass=True)
            with ProcessPoolExecutor() as executor:
                
                embed,image_file=await self.bot.loop.run_in_executor(executor,do_magik,buffer,self.path)
            await ctx.send(file=image_file)
            del buffer,embed,image_file
    
    @commands.cooldown(1,10,commands.BucketType.user)
    @commands.command()
    async def deepfry(self,ctx:commands.Context):
        with ctx.channel.typing():
            buffer=await self.image_url_fetcher(ctx=ctx,api_token=self.bot.tom.tenortoken)
            with ProcessPoolExecutor() as executor:
                embed,image_file=await self.bot.loop.run_in_executor(executor,deepfried,buffer,self.path)
            await ctx.send(file=image_file)
            del buffer,embed,image_file
        
    @commands.cooldown(1,10,commands.BucketType.user)
    @commands.command()
    async def wide(self,ctx:commands.Context):
        with ctx.channel.typing():
            buffer=await self.image_url_fetcher(ctx=ctx,api_token=self.bot.tom.tenortoken)
            with ProcessPoolExecutor() as executor:
                embed,image_file=await self.bot.loop.run_in_executor(executor,make_wide,buffer,self.path)
            await ctx.send(file=image_file)
            del buffer,embed,image_file
    
    @commands.cooldown(1,10,commands.BucketType.guild)
    @commands.command()
    async def gmagik(self,ctx:commands.Context,mode:str="",*,text:str=""):
        
        if mode.lower() == "deepfry":
            deepfry=True
            wide=False
            speedup=False
            dry=False
            caption=(False,text)

        elif mode.lower() == "wide":
            deepfry=False
            speedup=False
            wide=True
            dry=False
            caption=(False,text)

        elif mode.lower() == "speedup":
            deepfry=False
            wide=False
            speedup=True
            dry=True
            caption=(False,text)

        elif mode.lower() == "caption":
            deepfry=False
            wide=False  
            speedup=False  
            dry=True
            caption=(True,text)

        else:
            deepfry=False
            wide=False  
            speedup=False  
            dry=False
            caption=(False,text)

        with ctx.channel.typing():
            buffer=await self.image_url_fetcher(gif=True,ctx=ctx,api_token=self.bot.tom.tenortoken)
            with ProcessPoolExecutor() as executor:
                embed,image_file=await self.bot.loop.run_in_executor(None,partial(
                    do_gmagik,
                    buffer,
                    self.path,
                    deepfry=deepfry,
                    wide=wide,
                    speedup=speedup,
                    dry=dry,
                    caption=caption))
        await ctx.send(file=image_file)
        del buffer,embed,image_file
    
    @commands.command()
    async def caption(self,ctx,*,text:str=""):
        buffer=await self.image_url_fetcher(gif=False,ctx=ctx,api_token=self.bot.tom.tenortoken)
        embed,image_file=await self.captioner(buffer,text,size=64)
        await ctx.send(file=image_file)
        del buffer,embed,image_file
        