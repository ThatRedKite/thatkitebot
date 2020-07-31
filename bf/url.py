import  requests
from random import choice
from bs4 import BeautifulSoup
import asyncio
import discord
import aiohttp

async def xml_sequence_parse(session:aiohttp.ClientSession,payload:dict,sourceurl:str,attr:str,updatevalue:str, islist:bool=False):
    urls=[] # list of gathered urls
    for x in range(0,10): # update the :updatevalue: from 0 to 10
        payload.update({updatevalue:x}) 
        async with session.get(sourceurl, params=payload) as r:
            soup=BeautifulSoup(await r.text(), "lxml") # parse XML
            for post in soup.find_all("post"): # find every :post:
                sample=dict(post.attrs)[attr] # get every post with the post_attribute :attr:
                if sample != None: # append sample to :urls: when it is not empty
                    urls.append(sample)
                else:
                    continue # just do nothing
    if islist is False: 
        try:
            result=choice(urls) #choose a random entry of :urls:
            if result != None: 
                return result #return the randomly chosen entry if it is not None
        except IndexError:
            pass    # when an index error occurs, nothing will happen (unlikely but possible)
    if islist is True:
        return urls        # returns the outlist list

async def monosodiumglutamate(session,payload:dict, updatevalue:str):
    urls=[] # initialize the list of URLs 
    url="https://www.e621.net/posts.json" 
    headers={"User-Agent": "ThatKiteBot/1.9 (from luio950)"} #set user agent because this API is weird
    for x in range(2): # do that stuff twice
        payload.update({updatevalue:x}) # change the "page"
        async with session.get(url, headers=headers, params=payload) as r:
            contentdict=await r.json()
            for x in contentdict["posts"]:
                if x != None:
                    urls.append(x["file"]["url"]) # get the file URL and append it to the list
                else:
                    break
        asyncio.sleep(0.51) # avoid exceeding the rate limit of the API (pretty crude fix, i know)
    return urls

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
