import toml
from pathlib import Path
import asyncio
import subprocess
import json

class Tomler:
    def __init__(self, dirname:str): 
        """handles different bot settings using the TOML file format"""
        # set the absolute path to the settingsz file
        self.path=Path(f"{dirname}/data/settings.json")
        # load the settings file and parse it
        if self.path.exists(): # check if the file exists
            with open(self.path, "rt") as stream:
                self.parsed:dict=json.loads(stream.read())
        else:
            raise FileNotFoundError

        self.tokens=self.parsed["tokens"]
        # the bot's token
        self.token=self.tokens["discordtoken"] 
        # the bot's prefix
        self.prefix=self.tokens["prefix"] 
        # the bot's settings
        self.settings_all=self.parsed["settings"]
        # the setting for a specific guild

    def update(self, data, guildid:int): 
        """ update a setting (not the token or prefix) """
        if type(data == dict):
            settings_local = self.parsed["settings"]
            try:
                settings_local[str(guildid)].update(data)
            except KeyError:
                if len(settings_local) == 0:
                    settings_local = {str(guildid):{
                        "busbr":False,
                        "nsfw":False,
                        "bomb":False}}
                    settings_local[guildid].update(data)
                else:
                    settings_local.update({str(guildid):{
                        "busbr":False,
                        "nsfw":False,
                        "bomb":False}})
                    settings_local[str(guildid)].update(data)
            finally:
                self.settings_all = settings_local
                self.parsed = {"tokens": self.tokens, "settings":self.settings_all}
                datanew=json.dumps(self.parsed,indent=2)
                with open(self.path,"wt") as stream:
                    stream.write(datanew)

