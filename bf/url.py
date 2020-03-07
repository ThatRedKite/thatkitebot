import requests_async as requests
import random
from bs4 import BeautifulSoup

async def urlgetter(payload:dict,sourceurl:str,attr:str,updatevalue:str, islist:bool=False, length:int=0):
    urls = [] # list of gathered urls
    outlist = [] # list of the urls that will be output
    for x in range(0,10): # update the :updatevalue: from 0 to 10
        payload.update({updatevalue:x}) 
        with await requests.get(sourceurl, params=payload) as r:
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
            if islist is True and length != 0:
                try:
                    for x in range(length): # append x (where x = length) randomly chosen entries to outlist
                        outlist.append(random.choice(urls))
                except IndexError:
                    pass    # when an index error occurs, nothing will happen (unlikely but possible)
                finally:
                    return outlist        # returns the outlist list
                    