import random
from bs4 import BeautifulSoup
import requests

def urlgetter(tag:str, tag2):

    randpid = random.randint(1, 5)

    payload = {
            "page": "dapi",
            "s": "post",
            "q": "index",
            "pid": randpid

    }

    if len(tag2) > 0:
        tags = " ".join([tag, tag2])
        payload.update({"tags": tags})
    else:
        payload.update({"tags": tag})

    r = requests.get("https://rule34.xxx/index.php", params=payload)
    soup = BeautifulSoup(r.text, "lxml")
    urls = []
    for post in soup.find_all("post"):
        post_attrs = dict(post.attrs)
        urls.append(post_attrs["sample_url"])
        
    return(random.choice(urls))
