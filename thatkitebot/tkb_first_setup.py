import redis
import yaml
from pathlib import Path
import os
settings = {}

r = redis.Redis(host="redis", db=0, charset="utf8", decode_responses=True)


def change_prefix(prefix):
    r.set("PREFIX", prefix)


def change_discordtoken(token):
    r.set("DISCORDTOKEN", token)


def change_tenortoken(token):
    r.set("TENORTOKEN", token)


def initial():
    try:
        with open("/app/data/init_settings.yml") as s:
            settings = yaml.safe_load(s.read())
            discordtoken = settings["discord_token"]
            tenortoken = settings["tenor_token"]
            prefix = settings["prefix"]
    except FileNotFoundError:
        initdict = {"discord_token": "", "tenor_token": "", "prefix": ""}
        with open("/app/data/init_settings.yml", "w") as s:
            yaml.dump(initdict, s)
        os.chown("/app/data/init_settings.yml", 1000, 1000)
        print(f"init_settings.yml not found!\n I created a blank one for you.")
        exit(255)

    change_prefix(prefix)
    change_discordtoken(discordtoken)
    change_tenortoken(tenortoken)
