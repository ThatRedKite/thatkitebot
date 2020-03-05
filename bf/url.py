import requests_async as requests
import random
from bs4 import BeautifulSoup

async def r34(taglist:list):
    for x in range(0,1000):
        payload = {
        "page": "dapi",
        "s": "post",
        "q": "index",
        "pid": x
        }
        tagstring = " ".join(taglist)
        payload.update({"tags": tagstring})
        with await requests.get("https://rule34.xxx/index.php", params=payload) as r:
            soup = BeautifulSoup(r.text, "lxml")
            urls = []
            for post in soup.find_all("post"):
                post_attrs = dict(post.attrs)
                urls.append(post_attrs["sample_url"])
            try:
                result = random.choice(urls)
                if result != None:
                    return result 
                    break
            except IndexError:
                continue

async def yandere(taglist:list):
    for x in range(0,100):
        payload = {
        "page": x,
        "limit": 100,
        "tags": " ".join(taglist)
        }

        with await requests.get("https://yande.re/post.xml", params=payload) as r:
            soup = BeautifulSoup(r.text, "lxml")
            urls = []
            for post in soup.find_all("post"):
                post_attrs = dict(post.attrs)
                urls.append(post_attrs["sample_url"])
            try:
                result = random.choice(urls)
                if result != None:
                    return result 
                    break
            except IndexError:
                continue