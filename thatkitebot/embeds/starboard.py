#  Copyright (c) 2019-2023 ThatRedKite and contributors
import io

import aiohttp
from discord import Embed, Message, Color, File

from thatkitebot.base.image_stuff import get_image_url


async def generate_embed(message: Message, count, star_emoji, return_file=False, aiohttp_session=None):
    embed = Embed(title=f"{message.author.name}",
                          description=f"**Click [here]({message.jump_url}) to Jump to the message**")
    try:
        url, embed_type = await get_image_url(message, video=True, gifv=True)
    except TypeError:
        url, embed_type = None, None

    is_image = embed_type in ("rich", "image")

    content = message.clean_content or ""
    if content and content != url:
        embed.description += f"\n\n{content}"

    elif content and url in content:
        content_type = "image" if is_image else "video"
        replaced_content = content.replace(url, f"[{content_type} url]({url})")
        embed.add_field(name="​", value=replaced_content, inline=False)

    embed.set_thumbnail(url=message.author.avatar.url)
    embed.add_field(name="​", value=f"{count} - {star_emoji}'s")
    embed.color = Color.gold()
    embed.timestamp = message.created_at

    if return_file and aiohttp_session and url:
        async with aiohttp_session.get(url) as resp:
            resp: aiohttp.ClientResponse
            file = File(fp=io.BytesIO(await resp.read()), filename=f"{message.id}.{resp.content_type.split('/')[1]}")
            return embed, file

    return embed, None
