from random import choice, choices
from bs4 import BeautifulSoup
import asyncio
import discord
import aiohttp
import xmltodict

async def r34url(session:aiohttp.ClientSession,tags,islist:bool=False,count:int=1):
    urls={}
    outlist=list()
    payload={ "page": "dapi","tags": tags,"s": "post","q": "index","limit":100}
    for x in range(0,10): # update the :updatevalue: from 0 to 10
        payload.update(dict(pid=x))
        async with session.get(url="https://rule34.xxx/index.php", params=payload) as r:
            soup=BeautifulSoup(await r.text(), "lxml") # parse XML
            
            for post in soup.find_all("post"): # find every :post:
                urls.update({post.attrs.get("file_url"):int(post.attrs.get("score"))})

    so=sorted(urls.items(),key=lambda x:x[1],reverse=True)
    for url,score in so:
        outlist.append(url)
    if islist and outlist:
        return choices(outlist,k=count)
    elif not islist and outlist:
        return choice(outlist)
    else:
        return []

async def monosodiumglutamate(session,payload:dict, updatevalue:str):
    urls=[] # initialize the list of URLs 
    api_url="https://www.e621.net/posts.json" 
    headers={"User-Agent": "ThatKiteBot/1.9 (from luio950)"} #set user agent because this API is weird
    for x in range(2): # do that stuff twice
        payload.update({updatevalue:x}) # change the "page"
        async with session.get(api_url, headers=headers, params=payload) as r:
            contentdict=await r.json()
            for x in contentdict["posts"]:
                if x != None:
                    urls.append(x["file"]["url"]) # get the file URL and append it to the list
                else:
                    break
        asyncio.sleep(0.51) # avoid exceeding the rate limit of the API (pretty crude fix, i know)
    return urls

async def yanurlget(session,islist:bool=False,tags=[]):
    urls=set()
    for x in range(10):
        payload={"limit": 100,"tags": tags,"page":x}
        async with session.get(url="https://yande.re/post.json",params=payload) as r:
            jsoned=await r.json()
            for entry in jsoned:
                url=entry.get("jpeg_url", None)
                if url is not None:
                    urls.add(url)
    assert len(urls)>0 and not None in urls
    if not islist:
        outurl=choice(list(urls))
        return outurl
    else:
        return list(urls)
        

async def word(session,embedmode:bool=True):
    async with session.get("https://www.thisworddoesnotexist.com/") as r: #get the website contents
        bs=BeautifulSoup(await r.text(), "html.parser") 
        word=bs.find(id="definition-word").string # get the word
        syllables=bs.find(id="definition-syllables").string # get the syllables
        definition=bs.find(id="definition-definition").string # get the definition of the word
        if embedmode:
            if syllables:
                embed=discord.Embed(title=word)
                embed.add_field(name=syllables.lstrip(), value=definition.lstrip())
            else:
                embed=discord.Embed(title=word, description=definition.lstrip())
            if embed:
                return embed
        else:
            return word,definition
