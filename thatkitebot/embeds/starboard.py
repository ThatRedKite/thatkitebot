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

#region imports
import io
from random import randint

from discord import Embed, Message, Color, File, EmbedField, ButtonStyle
from discord import ui

from thatkitebot.base.image_stuff import get_embed_urls
from thatkitebot.base.url import get_avatar_url
#endregion

class StarboardEmbed(Embed):
    def __init__(self, message:Message, emoji: str, count: int):
        self.message = message
        self.emoji = emoji
        self.count = count
        self._video_url: str = ""
        self.url = None
        self.author = None
        self.footer = None
        self.image = None
        self.colour = Color.gold()
        self.timestamp = message.created_at
        self.type = "rich" 
        self._fields = []

        self._set_images = False
        self._set_video = False
        self._show_channel_name = False
        self._show_nickname = False
        
        self.title = f"{message.author.name}"
        if self._show_nickname and message.author.nick is not None:
            self.title += f" ({message.author.nick})"

        self.description=""
        #self.description = f"{message.jump_url}"

        self.append_field(self.gen_count_field())
        self.append_field(self.gen_count2_field())
        self.append_field(EmbedField(value="​ ", name="​", inline=True))

        if content_field := self.gen_content_field():
            self.append_field(content_field)

        self.set_footer(text=f"Id: {self.message.id}")
        

    def gen_content_field(self) -> EmbedField:
        # content string
        content = self.message.clean_content or ""
        # bools to ensure only one image or video has been set

        for url, content_type in get_embed_urls(self.message, video_enabled=True, gifv=True):
    
            if not (url or content_type):
                break

            if content:
                # only content is an image url
                if url in content:
                    content = content.replace(url, f"[{content_type} link]({url})")

                # check if any text content present
                if url and content == url and content_type == "image":
                    if not self._set_images:
                        self.set_image(url=url)
                        self._set_images = True
                    elif content_type == "video":
                        self._video_url = url
                        self._set_video = True
                    
                # content contains an url and additional text
                elif url and url in content:
                    if content_type == "image" and not self._set_images:
                        self.set_image(url=url)
                        self._set_images = True
                    elif content_type == "video":
                        self._video_url = url
                        self._set_video = True
                    
                # if the url does not appear in the content, the url is likely an attachment
                elif url and url not in content:
                    if content_type == "image" and not self._set_images:
                        self.set_image(url=url)
                        self._set_images = True

                    elif content_type == "video":
                        self._video_url = url
                        self._set_video = True
                    
            # no content but we have an url. Must be an attachment with no extra text.
            elif not content and content_type == "image":
                if not self._set_images:
                    self.set_image(url=url)
                    self._set_images = True  

            elif content_type == "video":
                if not self._set_video:
                    self._video_url = url
                    self._set_video = True

        if content:
            return EmbedField(name=f"​", value=content, inline=False)
        
        return None
        
    def gen_count_field(self) -> EmbedField:
        return EmbedField(name=self.emoji, value=f"{self.count}", inline=True)
    
    def gen_count2_field(self) -> EmbedField:
        if self._show_channel_name:
            return EmbedField(name="Original Message", value=f"{self.message.jump_url} ({self.message.channel.name})", inline=True)
        
        return EmbedField(name="Original Message", value=self.message.jump_url, inline=True)
        

    async def set_pfp(self, aiohttp) -> File:
        async with aiohttp.get(get_avatar_url(self.message.author)) as resp:
            self.set_thumbnail(url=f"attachment://{self.message.author.id}.{resp.content_type.split('/')[1]}")
            #self.set_footer(text=f"Id: {self.message.id}", icon_url=f"attachment://{self.message.author.id}.{resp.content_type.split('/')[1]}")
            return File(fp=io.BytesIO(await resp.read()), filename=f"{self.message.author.id}.{resp.content_type.split('/')[1]}")

    async def download_video(self, aiohttp) -> File:
        if not self._video_url:
            return None
        
        async with aiohttp.get(self._video_url) as resp:
            content_type: str = resp.content_type.split('/')[1]
            # thanks, Apple
            content_type = content_type.replace("quicktime", "mov")
            return File(fp=io.BytesIO(await resp.read()), filename=f"{self.message.id}.{content_type}")

#region main code
async def generate_embed(message: Message, count: int, star_emoji: str, return_file=False, aiohttp_session=None) -> tuple[StarboardEmbed,File]:
    embed = StarboardEmbed(message, star_emoji, count)
    
    if return_file:
        pfp_file = await embed.set_pfp(aiohttp_session)

        # check if videos are present and the session is passed
        if video_file := await embed.download_video(aiohttp_session):
            return embed, pfp_file, video_file
    
        return embed, pfp_file, None

    return embed, None, None
#endregion
