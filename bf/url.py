import  requests
import random
from bs4 import BeautifulSoup
import asyncio
import discord

async def xml_sequence_parse(payload:dict,sourceurl:str,attr:str,updatevalue:str, islist:bool=False):
    urls=[] # list of gathered urls
    outlist=[] # list of the urls that will be output
    for x in range(0,10): # update the :updatevalue: from 0 to 10
        payload.update({updatevalue:x}) 
        with requests.get(sourceurl, params=payload) as r:
            soup=BeautifulSoup(r.text, "lxml") # parse XML
            for post in soup.find_all("post"): # find every :post:
                sample=dict(post.attrs)[attr] # get every post with the post_attribute :attr:
                if sample != None: # append sample to :urls: when it is not empty
                    urls.append(sample)
                else:
                    continue

    if islist is False: 
        try:
            result=random.choice(urls) #choose a random entry of :urls:
            if result != None: 
                return result #return the randomly chosen entry if it is not None
        except IndexError:
            pass    # when an index error occurs, nothing will happen (unlikely but possible)
    if islist is True:
            return urls        # returns the outlist list

async def monosodiumglutamate(payload:dict, updatevalue:str):
    urls=[] # initialize the list of URLs
    url="https://www.e621.net/posts.json" 
    headers={"User-Agent": "ThatKiteBot/0.9 (from luio950)"} #set user agent because this API is weird
    for x in range(2): # do that stuff twice
        payload.update({updatevalue:x}) # change the "page"
        with requests.get(url, headers=headers, params=payload) as r:
            contentdict=r.json()
            for x in contentdict["posts"]:
                if x != None:
                    urls.append(x["file"]["url"]) # get the file URL and append it to the list
                else:
                    break
        asyncio.sleep(1) # avoid exceeding the rate limit of the API (pretty crude fix, i know)
    return urls
            
async def word():
    r=requests.get("https://www.thisworddoesnotexist.com/").text #get the website contents
    bs=BeautifulSoup(r, "html.parser") 
    word=bs.find(id="definition-word").string # get the word
    syllables=bs.find(id="definition-syllables").string # get the syllables
    definition=bs.find(id="definition-definition").string # get the definition of the word
    if syllables:
        embed=discord.Embed(title=word)
        embed.add_field(name=syllables.lstrip(), value=definition.lstrip())
    else:
        embed=discord.Embed(title=word, description=definition.lstrip())
    if embed:
        return embed

 


 