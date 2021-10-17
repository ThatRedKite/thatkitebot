# ------------------------------------------------------------------------------
#  MIT License
#
#  Copyright (c) 2019-2021 ThatRedKite
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
#  documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
#  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
#  and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all copies or substantial portions of
#  the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
#  THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
#  TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
# ------------------------------------------------------------------------------


import asyncio
import re
from io import BytesIO
from random import choice, choices
import aiohttp
import discord
import imageio
from bs4 import BeautifulSoup
from .util import EmbedColors as ec


gifpattern = re.compile("(^https?://\S+.(?i)(gif))")  # only gif images
# detects PNG, JPEG, WEBP and GIF images
otherpattern = re.compile("(^https?://\S+.(?i)(png|webp|gif|jpe?g))")
# gets the ID of a tenor GIF from its URL
tenorpattern = re.compile("^https://tenor.com\S+-(\d+)$")

emoji_pattern = re.compile("<:\S+:\n+>")


async def imageurlgetter(session: aiohttp.ClientSession, history, token=None, gif=False):
    if gif:
        pattern = gifpattern
    else:
        pattern = otherpattern

    async for message in history:
        attachments = message.attachments
        if attachments:
            found_url = pattern.findall(attachments[0].url)
            if found_url:
                url, fe = found_url[0]
                break  # break the loop, a valid url has been found
        else:
            # found_url is a list of all urls the regex found,
            # this should only be one value, or no value at all
            found_url = pattern.findall(message.clean_content)
            # the tenor ID of the GIF.It only contains anything, if there actually is a tenor GIF
            tenor = tenorpattern.findall(message.clean_content)
            if found_url and not tenor:  # unpack the url and the file extension
                url, fe = found_url[0]
                break  # break the loop, a valid url has been found
            elif tenor:
                # define the header and the payload:
                headers = {"User-Agent": "ThatKiteBot/2.7.0", "content-type": "application/json"}
                payload = {"key": token, "ids": int(tenor[0]), "media_filter": "minimal"}

                async with session.get(url="https://api.tenor.com/v1/gifs", params=payload, headers=headers) as r:
                    gifs = await r.json()
                    url = gifs["results"][0]["media"][0]["gif"]["url"]  # dictionary magic to get the url of the gif
                break  # break the loop, a valid url has been found

    return str(url)


async def imagedownloader(session: aiohttp.ClientSession, url: str):
    async with session.get(url) as r:
        ob = BytesIO(await r.read())
        ob.seek(0)
        return imageio.get_reader(ob)


async def r34url(session: aiohttp.ClientSession, tags, islist: bool = False, count: int = 1):
    urls = {}
    outlist = list()
    headers = {"User-Agent": "ThatKiteBot/2.7.0", "content-type": "application/xml"}
    payload = {"page": "dapi", "tags": tags, "s": "post", "q": "index", "limit": 100}
    for x in range(0, 10):  # update the :updatevalue: from 0 to 10
        payload.update(dict(pid=x))
        async with session.get(url="https://rule34.xxx/index.php", params=payload, headers=headers) as r:
            soup = BeautifulSoup(await r.text(), "lxml")  # parse XML

            for post in soup.find_all("post"):  # find every :post:
                urls.update({post.attrs.get("file_url"): int(post.attrs.get("score"))})

    so = sorted(urls.items(), key=lambda x: x[1], reverse=True)
    for url, score in so:
        outlist.append(url)
    if islist and outlist:
        return choices(outlist, k=count)
    elif not islist and outlist:
        return choice(outlist)
    else:
        return []


async def monosodiumglutamate(session, tags):
    urls = []  # initialize the list of URLs
    api_url = "https://www.e621.net/posts.json"
    payload = {"tags": tags, "limit": 320, "page": 0}
    # set user agent because this API is weird
    headers = {"User-Agent": "ThatKiteBot/2.7.0 (from luio950)", "content-type": "application/json"}
    for x in range(2):  # do that stuff twice
        payload.update({"page": x})  # change the "page"
        async with session.get(api_url, headers=headers, params=payload) as r:
            contentdict = await r.json()
            for x in contentdict["posts"]:
                if x != None:
                    urls.append(x["file"]["url"])  # get the file URL and append it to the list
                else:
                    break

        # avoid exceeding the rate limit of the API (pretty crude fix, i know)
        await asyncio.sleep(0.51)
    return urls


async def yanurlget(session, islist: bool = False, tags=[]):
    urls = set()
    for x in range(10):
        payload = {"limit": 100, "tags": tags, "page": x}
        headers = {"User-Agent": "ThatKiteBot/2.7.0", "content-type": "application/json"}
        async with session.get(url="https://yande.re/post.json", params=payload, headers=headers) as r:
            jsoned = await r.json()
            for entry in jsoned:
                url = entry.get("jpeg_url", None)
                if url is not None:
                    urls.add(url)
    assert len(urls) > 0 and not None in urls
    if not islist:
        outurl = choice(list(urls))
        return outurl
    else:
        return list(urls)


async def word(session, embedmode: bool = True):
    headers = {"User-Agent": "ThatKiteBot/2.7.0", "content-type": "text/html"}
    async with session.get("https://www.thisworddoesnotexist.com/", headers=headers) as r:  # get the website contents
        bs = BeautifulSoup(await r.text(), "html.parser")
        word = bs.find(id="definition-word").string  # get the word
        syllables = bs.find(id="definition-syllables").string  # get the syllables
        definition = bs.find(id="definition-definition").string  # get the definition of the word
        if embedmode:
            if syllables:
                embed = discord.Embed(title=word)
                embed.add_field(name=syllables.lstrip(), value=definition.lstrip())
            else:
                embed = discord.Embed(title=word, description=definition.lstrip())
            if embed:
                return embed
        else:
            return word, definition


async def inspirourl(session:aiohttp.ClientSession):
    payload = {"generate": "true"}
    headers = {"User-Agent": "ThatKiteBot/2.7.0", "content-type": "text/html"}
    async with session.get("http://inspirobot.me/api", params=payload,headers=headers) as r:
        url = await r.text()
    embed = discord.Embed(title="A motivating quote from InspiroBot")
    embed.color = ec.lime_green
    embed.set_image(url=url)
    return embed
