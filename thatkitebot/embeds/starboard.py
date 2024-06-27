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

from discord import Embed, Message, Color, File

from thatkitebot.base.image_stuff import get_embed_urls
from thatkitebot.base.url import get_avatar_url
#endregion

#region main code
async def generate_embed(message: Message, count: int, star_emoji, return_file=False, aiohttp_session=None) -> tuple[Embed,File]:
    embed = Embed(
        title=f"{message.author.name}",
        description=f"**[Click here to Jump to the message]({message.jump_url})**",
    )


    content = message.clean_content or ""

    # bools to ensure only one image or video has been set
    set_image = False
    set_video = False

    video_file = None

    for url, content_type in get_embed_urls(message, video_enabled=True, gifv=True):
        
        if not (url or content_type):
            break

        if content:
            # only content is an image url
            if url in content:
                content = content.replace(url, f"[{content_type} url]({url})")

            # check if any text content present
            if url and content == url and content_type == "image":
                if not set_image:
                    embed.set_image(url=url)
                    set_image = True
                elif content_type == "video":
                    set_video = True
                
            # content contains an url and additional text
            elif url and url in content:
                if content_type == "image" and not set_image:
                    embed.set_image(url=url)
                    set_image = True
                elif content_type == "video":
                    set_video = True
                
            # if the url does not appear in the content, the url is likely an attachment
            elif url and url not in content:
                if content_type == "image" and not set_image:
                    embed.set_image(url=url)
                    set_image = True

                elif content_type == "video":
                    set_video = True
                
        # no content but we have an url. Must be an attachment with no extra text.
        elif not content and content_type == "image":
            if not set_image:
                embed.set_image(url=url)
                set_image = True  

        elif content_type == "video":
            if not set_video:
                set_video = True

        if return_file and aiohttp_session and url and set_video:
            async with aiohttp_session.get(url) as resp:
                content_type: str = resp.content_type.split('/')[1]

                # thanks, Apple
                content_type = content_type.replace("quicktime", "mov")
                video_file = File(fp=io.BytesIO(await resp.read()), filename=f"{message.id}.{content_type}")

    if content:
        embed.add_field(name="​", value=content, inline=False)

    # download the profile picture to make that one guy shut up
    async with aiohttp_session.get(get_avatar_url(message.author)) as resp:
        pfp_file = File(fp=io.BytesIO(await resp.read()), filename=f"{message.author.id}.{resp.content_type.split('/')[1]}")
    
    embed.set_thumbnail(url=f"attachment://{message.author.id}.{resp.content_type.split('/')[1]}")
    embed.add_field(name="​", value=f"{count} - {star_emoji}'s")

    if count < 13:
        embed.color = int(hex(message.guild.id)[4:10],16)
    elif count > 13:
        embed.color = Color.gold()

    embed.timestamp = message.created_at

    # check if videos are present and the session is passed
    if return_file and video_file:
        return embed, pfp_file, video_file
    
    return embed, pfp_file, None
#endregion
