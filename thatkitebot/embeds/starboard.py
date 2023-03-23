import discord
from discord import Embed

from thatkitebot.base.image_stuff import get_image_url


async def generate_embed(message: discord.Message, count, star_emoji, return_file=False, aiohttp_session=None):
    embed = Embed(title=f"{message.author.name}",
                          description=f"**Click [here]({message.jump_url}) to Jump to the message**")
    try:
        url, embed_type = await get_image_url(message, video=False, gifv=True)
    except TypeError:
        url, embed_type = None, None

    if url and ("image" in embed_type or embed_type == "rich"):
        embed.set_image(url=url)
    elif url and "video" in embed_type:
        embed.add_field(name="[Video]", value=f"[Content]({url}) is a video which bots cannot display")

    content = message.clean_content or ""
    if content and content != url:
        embed.description += f"\n\n{content}"

    embed.set_thumbnail(url=message.author.avatar.url)
    embed.add_field(name="​", value=f"{count} - {star_emoji}'s")
    embed.color = discord.Color.gold()
    embed.timestamp = message.created_at
    if return_file and aiohttp_session:
        async with aiohttp_session.get(url) as resp:
            file = discord.File(await resp.read(), filename=f"{message.id}.{resp.content_type.split('/')[1]}")
            return embed, file

    return embed
