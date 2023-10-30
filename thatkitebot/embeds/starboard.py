#  Copyright (c) 2019-2023 ThatRedKite and contributors
import io

import aiohttp
from discord import Embed, Message, Color, File

from thatkitebot.base.image_stuff import get_image_url, get_embed_urls
from thatkitebot.base.url import get_avatar_url


async def generate_embed(message: Message, count, star_emoji, return_file=False, aiohttp_session=None):
    embed = Embed(
        title=f"{message.author.name}",
        description=f"**[Click here to Jump to the message]({message.jump_url})**"
    )


    content = message.clean_content or ""

    # bools to ensure only one image or video has been set
    set_image = False
    set_video = False

    for url, content_type in get_embed_urls(message, video=True, gifv=True):
        
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
                continue

            # content contains an url and additional text
            elif url and url in content:
                if content_type == "image" and not set_image:
                    embed.set_image(url=url)
                    set_image = True
                elif content_type == "video":
                    set_video = True
                continue

            # if the url does not appear in the content, the url is likely an attachment
            elif url and url not in content:
                if content_type == "image" and not set_image:
                    embed.set_image(url=url)
                    set_image = True
                continue

        # no content but we have an url. Must be an attachment with no extra text.
        elif not content and content_type == "image":
            if not set_image:
                embed.set_image(url=url)
                set_image = True
            continue

        elif not content and content_type == "video":
            if not set_video:
                set_video = True
        
    if content:
        embed.add_field(name="​", value=content, inline=False)
    embed.set_thumbnail(url=get_avatar_url(message.author))
    embed.add_field(name="​", value=f"{count} - {star_emoji}'s")
    embed.color = Color.gold()
    embed.timestamp = message.created_at

    # check if videos are present and the session is passed
    if return_file and aiohttp_session and url:
        # download and attach if it is a video
        if set_video:
            async with aiohttp_session.get(url) as resp:
                resp: aiohttp.ClientResponse
                file = File(fp=io.BytesIO(await resp.read()), filename=f"{message.id}.{resp.content_type.split('/')[1]}")
                return embed, file
        

    return embed, None
