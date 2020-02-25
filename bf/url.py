import requests
import random
from bs4 import BeautifulSoup

def urlgetter(tag, tag2):
    for x in range(0,100):
        payload = {
        "page": "dapi",
        "s": "post",
        "q": "index",
        "pid": x
        }

        if len(tag2) > 0:
            tags = " ".join([tag,tag2])
            payload.update({"tags": tags})
        else:
            payload.update({"tags": tag})
        
        with requests.get("https://rule34.xxx/index.php", params=payload) as r:
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
