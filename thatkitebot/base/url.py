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

#region Imports
import asyncio
import re
from io import BytesIO
from random import choice, choices
from random import randrange
import aiohttp
import discord
import xkcd
from bs4 import BeautifulSoup
from thatkitebot.base.exceptions import NoImageFoundException
from thatkitebot.base.util import EmbedColors as ec
#endregion

#region Regex Patterns
GIF_PATTERN = re.compile(r"(?i)(^https?://\S+.(?P<extension>gif))")  # only gif images
# detects PNG, JPEG, WEBP and GIF images
OTHER_PATTERN = re.compile(r"(?i)(^https?://\S+.(?P<extension>png|webp|gif|jpe?g))")
# gets the ID of a tenor GIF from its URL
TENOR_PATTERN = re.compile(r"(?i)^https://tenor.com\S+-(?P<id>\d+)$")
# pattern for
EMOJI_PATTERN = re.compile(r"(?i)<:(?P<name>\S+):(?P<id>\d+)>")

LINK_PATTERN = re.compile(r"(https?:\/\/[A-Za-z0-9\-._~!$&'()*+,;=:@\/?]+)")

def get_avatar_url(user: discord.User) -> str:
    if user.avatar:
        return user.avatar.url
    else:
        if user.discriminator == "0":
            return f"https://cdn.discordapp.com/embed/avatars/{(int(user.id) >> 22) % 6}.png"
        else:
            return f"https://cdn.discordapp.com/embed/avatars/{int(user.discriminator) % 5}.png"

async def get_fake_word(session, embedmode: bool = True) -> discord.Embed | tuple[str, str]:
    """
    Gets a word that does not exist from thisworddoesnotexist.com. Rarely works.
    """
    headers = {"User-Agent": "ThatkiteBot/4.0", "content-type": "text/html"}
    async with session.get("https://www.thisworddoesnotexist.com/", headers=headers) as r:  # get the website contents
        bs = BeautifulSoup(await r.text(), "html.parser")
        fake_word = bs.find(id="definition-word").string  # get the word
        syllables = bs.find(id="definition-syllables").string  # get the syllables
        definition = bs.find(id="definition-definition").string  # get the definition of the word
        if embedmode:
            if syllables:
                embed = discord.Embed(title=fake_word)
                embed.add_field(name=syllables.lstrip(), value=definition.lstrip())
            else:
                embed = discord.Embed(title=fake_word, description=definition.lstrip())
            if embed:
                return embed
        else:
            return fake_word, definition


async def get_inspirobot_url(session: aiohttp.ClientSession) -> discord.Embed:
    """
    Gets a random image from Inspirobot.
    """
    payload = {"generate": "true"}
    headers = {"User-Agent": "ThatkiteBot/4.0", "content-type": "text/html"}
    async with session.get("https://inspirobot.me/api", params=payload, headers=headers) as r:
        url = await r.text()
    embed = discord.Embed(title="A motivating quote from InspiroBot", color=ec.lime_green)
    embed.set_image(url=url)
    return embed


async def get_xkcd(args=None) -> discord.Embed | None:
    if args is not None:
        if "l" in str(args).lower() or "latest" in str(args).lower():
            comic = xkcd.getLatestComic()
        else:
            try:
                comic = xkcd.getComic(int(args))
            except:
                return None
    else:
        comic = xkcd.getRandomComic()
    embed = discord.Embed(title=f"{comic.title}", color=ec.blood_orange)
    embed.add_field(name="​", value=f"{comic.altText}")
    embed.set_image(url=f"{comic.imageLink}")
    return embed


async def get_contributor_json(session: aiohttp.ClientSession):
    headers = {"User-Agent": "ThatkiteBot/3.6", "content-type": "text/html"}
    async with session.get(
            f"https://api.github.com/repos/ThatRedKite/thatkitebot/contributors?q=contributions&order=desc",
            headers=headers) as r:
        if r.status == 200:
            jsonstr = await r.json()
        else:
            return None
    return jsonstr


async def get_tenor_image_url(aiohttp_session: aiohttp.ClientSession, url:str, token:str) -> str:
    """
    Downloads a tenor gif and returns the hash of the image.
    """
    # define the header and the payload:
    tenor = TENOR_PATTERN.findall(url)
    if not tenor:
        return None
    payload = {"key": token, "ids": int(tenor[0]), "media_filter": "minimal"}

    async with aiohttp_session.get(url="https://api.tenor.com/v1/gifs", params=payload) as r:
        gifs = await r.json()
        url = gifs["results"][0]["media"][0]["gif"]["url"]  # dictionary magic to get the url of the gif
        return url


    return None


async def get_image_urls(message: discord.Message, video: bool = False, gifv: bool = False) -> list[str]:
    # check if the message has an attachment or embed of the type "image"
    if message.attachments:
        return [attachment.url for attachment in message.attachments]

    if not message.embeds:
        raise NoImageFoundException

    embed_urls = []
    for embed in message.embeds:
        if embed.type == "image":
            # if it does, return the embed's url
            embed_urls.append(embed.url)
            continue
        # check if the message has an embed of the type "rich" and if it contains an image
        elif embed.type == "rich" and embed.image:
            embed_urls.append(embed.image.url)
            continue
        # check if the message has a video if the :video: argument is true
        elif embed.type == "video" and video:
            embed_urls.append(embed.url)
        # check if the message has a gif if the :gifv: argument is true
        elif embed.type == "gifv" and gifv:
            embed_urls.append(embed.url)
        else:
            # if it doesn't, return None
            raise NoImageFoundException

    return embed_urls


def get_embed_urls(message: discord.Message, video_enabled: bool = False, gifv: bool = False) -> (str | None, str | None): # type: ignore
    """
    clone of :get_image_urls but with different output format: [(url, embed_type), ...]
    """
    if message.attachments:
        for attachment in message.attachments:
            content_type = attachment.content_type
            if "image" in content_type:
                yield attachment.url, "image"

            elif "video" in content_type:
                yield attachment.url, "video"

    if not message.embeds:
        yield None, None
        return

    for embed in message.embeds:
        if embed.type == "image":
            # if it does, return the embed's url
            yield embed.url, "image"
            continue

        # check if the message has an embed of the type "rich" and if it contains an image
        elif embed.type == "rich" and embed.image:
            yield embed.image.url, "image"
            continue

        # check if the message has a video if the :video: argument is true
        elif embed.type == "video" and video_enabled:

            # --- special cases for different websites ---

            if embed.provider and embed.provider.name == "YouTube":
                # special case for youtube, ignore any videos, return video thumbnail instead
                yield embed.thumbnail.url, "image"
                continue


            yield embed.video.url, "video"
            continue

        # embeds where a thumbnail (if present) will be returned
        elif embed.type in ["link", "article"] and embed.thumbnail:
            yield embed.thumbnail.url, "image"
            continue

        # check if the message has a gif if the :gifv: argument is true
        elif embed.type == "gifv" and gifv:
            yield embed.url, "gifv"
            continue

        else:
            # if it doesn't, stop the generator
            yield None, None
            return

    return
