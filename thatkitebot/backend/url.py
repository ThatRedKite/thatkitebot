#  Copyright (c) 2019-2022 ThatRedKite and contributors

import asyncio
import re
from io import BytesIO
from random import choice, choices
from random import randrange
import aiohttp
import discord
import imageio
import xkcd
from bs4 import BeautifulSoup
from thatkitebot.backend.util import EmbedColors as ec

gifpattern = re.compile(r"(^https?://\S+.(?i)(gif))")  # only gif images
# detects PNG, JPEG, WEBP and GIF images
otherpattern = re.compile(r"(^https?://\S+.(?i)(png|webp|gif|jpe?g))")
# gets the ID of a tenor GIF from its URL
tenorpattern = re.compile(r"^https://tenor.com\S+-(\d+)$")

emoji_pattern = re.compile(r"<:\S+:\n+>")


async def imageurlgetter(session: aiohttp.ClientSession, history, token=None, gif=False):
    """
    Deprecated.
    """
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
                headers = {"User-Agent": "ThatkiteBot/3.6", "content-type": "application/json"}
                payload = {"key": token, "ids": int(tenor[0]), "media_filter": "minimal"}

                async with session.get(url="https://api.tenor.com/v1/gifs", params=payload, headers=headers) as r:
                    gifs = await r.json()
                    url = gifs["results"][0]["media"][0]["gif"]["url"]  # dictionary magic to get the url of the gif
                break  # break the loop, a valid url has been found

    return str(url)


async def imagedownloader(session: aiohttp.ClientSession, url: str):
    """
    Downloads an image from a given URL. Deprecated.
    """
    async with session.get(url) as r:
        with BytesIO(await r.read()) as ob:
            reader = imageio.get_reader(ob)
            ob.seek(0)
        return reader


async def r34url(session: aiohttp.ClientSession, tags, islist: bool = False, count: int = 1):
    """
    Gets a random image from r34 based on the tags.
    """
    urls = {}
    headers = {"User-Agent": "ThatkiteBot/3.6", "content-type": "application/xml"}
    payload = {"page": "dapi", "tags": tags, "s": "post", "q": "index", "limit": 100}
    for x in range(0, 10):  # update the :updatevalue: from 0 to 10
        payload.update(dict(pid=x))
        async with session.get(url="https://rule34.xxx/index.php", params=payload, headers=headers) as r:
            soup = BeautifulSoup(await r.text(), "lxml")  # parse XML

            for post in soup.find_all("post"):  # find every :post:
                urls.update({post.attrs.get("file_url"): int(post.attrs.get("score"))})

    so = sorted(urls.items(), key=lambda y: y[1], reverse=True)
    outlist = [discord.Embed(title="Here is an image from r34.xxx").set_image(url=url) for url, score in so]
    if islist and outlist:
        return choices(outlist, k=count)
    elif not islist and outlist:
        return choice(outlist)
    else:
        return []


async def monosodiumglutamate(session, tags):
    """
    Mono-sodium glutamate (MSG) is bad for your sanity.
    """
    urls = []  # initialize the list of URLs
    api_url = "https://www.e621.net/posts.json"
    payload = {"tags": tags, "limit": 320, "page": 0}
    # set user agent because this API is weird
    headers = {"User-Agent": "ThatkiteBot/3.6 (from luio950)", "content-type": "application/json"}
    for x in range(2):  # do that stuff twice
        payload.update({"page": x})  # change the "page"
        async with session.get(api_url, headers=headers, params=payload) as r:
            contentdict = await r.json()
            for x in contentdict["posts"]:
                if x:
                    urls.append((x["id"], x["file"]["url"]))  # get the file URL and append it to the list
                else:
                    break

        # avoid exceeding the rate limit of the API (pretty crude fix, i know)
        await asyncio.sleep(0.51)
    return urls


async def yanurlget(session, islist: bool = False, tags=None):
    """
    Gets a random image from yande.re based on the tags.
    """
    if tags is None:
        tags = list()
    urls = set()
    for x in range(10):
        payload = {"limit": 100, "tags": tags, "page": x}
        headers = {"User-Agent": "ThatkiteBot/3.6", "content-type": "application/json"}
        async with session.get(url="https://yande.re/post.json", params=payload, headers=headers) as r:
            jsoned = await r.json()
            for entry in jsoned:
                url = entry.get("jpeg_url", None)
                if url is not None:
                    urls.add(url)
    assert len(urls) > 0 and None not in urls
    if not islist:
        outurl = choice(list(urls))
        return outurl
    else:
        return list(urls)


async def word(session, embedmode: bool = True):
    """
    Gets a word that does not exist from thisworddoesnotexist.com. Rarely works.
    """
    headers = {"User-Agent": "ThatkiteBot/3.6", "content-type": "text/html"}
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


async def inspirourl(session: aiohttp.ClientSession):
    """
    Gets a random image from Inspirobot.
    """
    payload = {"generate": "true"}
    headers = {"User-Agent": "ThatkiteBot/3.6", "content-type": "text/html"}
    async with session.get("https://inspirobot.me/api", params=payload, headers=headers) as r:
        url = await r.text()
    embed = discord.Embed(title="A motivating quote from InspiroBot")
    embed.color = ec.lime_green
    embed.set_image(url=url)
    return embed


async def tpdne(session: aiohttp.ClientSession):
    """
    Gets a random image from thispersondoesnotexist.com.
    """
    headers = {"User-Agent": "ThatkiteBot/3.6", "content-type": "text/html"}
    async with session.get('https://thispersondoesnotexist.com/image', headers=headers) as r:
        if r.status == 200:
            img = await r.read()
            file = discord.File(BytesIO(img), filename="person.jpg")
            embed = discord.Embed(title="A person generated by an AI from: thispersondoesnotexist.com")
            embed.set_image(url="attachment://person.jpg")
    return file, embed


async def tcdne(session: aiohttp.ClientSession):
    """
    Gets a random image from thiscatdoesnotexist.com.
    """
    headers = {"User-Agent": "ThatkiteBot/3.6", "content-type": "text/html"}
    async with session.get('https://thiscatdoesnotexist.com/', headers=headers) as r:
        if r.status == 200:
            img = await r.read()
            file = discord.File(BytesIO(img), filename="cat.jpg")
            embed = discord.Embed(title="A cat generated by an AI from: thiscatdoesnotexist.com")
            embed.set_image(url="attachment://cat.jpg")
    return file, embed


async def tadne(session: aiohttp.ClientSession):
    """
    Gets a random image from thisartworkdoesnotexist.com.
    """
    headers = {"User-Agent": "ThatkiteBot/3.6", "content-type": "text/html"}
    async with session.get('https://thisartworkdoesnotexist.com/', headers=headers) as r:
        if r.status == 200:
            img = await r.read()
            file = discord.File(BytesIO(img), filename="art.jpg")
            embed = discord.Embed(title="Art generated by an AI from: thisartworkdoesnotexist.com")
            embed.set_image(url="attachment://art.jpg")
    return file, embed


async def twdne(session: aiohttp.ClientSession):
    """
    Gets a random image from thiswaifudoesnotexist.com.
    """
    headers = {"User-Agent": "ThatkiteBot/3.6", "content-type": "text/html"}
    max_value = 100000
    min_value = 10000
    irand = randrange(min_value, max_value)
    irand = str(irand)
    async with session.get(f"https://www.thiswaifudoesnotexist.net/example-{irand}.jpg", headers=headers) as r:
        if r.status == 200:
            img = await r.read()
            file = discord.File(BytesIO(img), filename="waifu.jpg")
            embed = discord.Embed(title="A waifu generated by an AI from: thiswaifudoesnotexist.net")
            embed.set_image(url="attachment://waifu.jpg")
    return file, embed


async def tfdne(session: aiohttp.ClientSession):
    """
    Gets a random image from thisfursonadoesexist.com.
    """
    headers = {"User-Agent": "ThatkiteBot/3.6", "content-type": "text/html"}
    max = 99999
    min = 0
    fixed_length = 5
    irand = randrange(min, max)
    irand = str(irand)
    if len(irand) < fixed_length:
        padding = fixed_length - len(irand)
        irand = "0" * padding + irand
    async with session.get(f"https://thisfursonadoesnotexist.com/v2/jpgs-2x/seed{irand}.jpg",
                           headers=headers) as r:
        if r.status == 200:
            img = await r.read()
            file = discord.File(BytesIO(img), filename="fur.jpg")
            embed = discord.Embed(title="An image generated by an AI from: thisfursonadoesnotexist.com")
            embed.set_image(url="attachment://fur.jpg")
    return file, embed


async def tvdne(session: aiohttp.ClientSession):
    headers = {"User-Agent": "ThatkiteBot/3.6", "content-type": "text/html"}
    max_value = 19999
    min_value = 1
    fixed_length = 7
    irand = randrange(min_value, max_value)
    irand = str(irand)
    if len(irand) < fixed_length:
        padding = fixed_length - len(irand)
        irand = "0" * padding + irand
    async with session.get(
            f"https://thisvesseldoesnotexist.s3-us-west-2.amazonaws.com/public/v2/fakes/{irand}.jpg",
            headers=headers) as r:
        if r.status == 200:
            img = await r.read()
            file = discord.File(BytesIO(img), filename="vessel.jpg")
            embed = discord.Embed(title="A fake vessel generated by an AI from: thisvesseldoesnotexist.com")
            embed.set_image(url="attachment://vessel.jpg")
    return file, embed


async def _xkcd(args=None):
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
    embed = discord.Embed(title=f"{comic.title}")
    embed.add_field(name="​", value=f"{comic.altText}")
    embed.set_image(url=f"{comic.imageLink}")
    embed.color = ec.blood_orange
    return embed

async def _contributorjson(session: aiohttp.ClientSession):
    headers = {"User-Agent": "ThatkiteBot/3.6", "content-type": "text/html"}
    async with session.get(
            f"https://api.github.com/repos/ThatRedKite/thatkitebot/contributors?q=contributions&order=desc",
            headers=headers) as r:
        if r.status == 200:
            jsonstr = await r.json()
        else:
            return None
    return jsonstr