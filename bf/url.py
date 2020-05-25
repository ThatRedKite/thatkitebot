import  requests
import random
from bs4 import BeautifulSoup
import asyncio
async def xml_sequence_parse(payload:dict,sourceurl:str,attr:str,updatevalue:str, islist:bool=False):
    urls = [] # list of gathered urls
    outlist = [] # list of the urls that will be output
    for x in range(0,10): # update the :updatevalue: from 0 to 10
        payload.update({updatevalue:x}) 
        with requests.get(sourceurl, params=payload) as r:
            soup = BeautifulSoup(r.text, "lxml") # parse XML
            for post in soup.find_all("post"): # find every :post:
                sample = dict(post.attrs)[attr] # get every post with the post_attribute :attr:
                if sample != None: # append sample to :urls: when it is not empty
                    urls.append(sample)
                else:
                    continue

    if islist is False: 
        try:
            result = random.choice(urls) #choose a random entry of :urls:
            if result != None: 
                return result #return the randomly chosen entry if it is not None
        except IndexError:
            pass    # when an index error occurs, nothing will happen (unlikely but possible)
    if islist is True:
            return urls        # returns the outlist list

async def monosodiumcarbonate(payload:dict, updatevalue:str):
    urls = []
    url = "https://www.e621.net/posts.json"
    headers = {"User-Agent": "ThatKiteBot/1.0 (from luio950)"}
    for x in range(0,2):
        payload.update({updatevalue:x})
        with requests.get(url, headers=headers, params=payload) as r:
            contentdict = r.json()
            for x in contentdict["posts"]:
                if x != None:
                    urls.append(x["file"]["url"])
                else:
                    break
        asyncio.sleep(1)

    return urls
            


