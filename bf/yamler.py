from pathlib import Path
import asyncio
import subprocess
import json
from os import path
from copy import deepcopy
class Tomler:
    def __init__(self, dirname:str): 
        """handles different bot settings using the TOML file format"""
        # set the absolute path to the settingsz file
        self.path=Path(path.join(dirname,"data/settings.json"))
        # load the settings file and parse it
        if self.path.exists(): # check if the file exists
            with open(self.path, "rt") as stream:
                self.parsed:dict=json.loads(stream.read())
        else:
            initdict={"tokens":{"discordtoken":"", "prefix":""}, "settings":{}}
            with open(self.path, "wt") as stream:
                stream.write(json.dumps(initdict,indent=2))
                print(f"""
                Your settings.json file was created in {self.path}
                 , please enter your bot token and prefix there!
                 The program is now terminating""")
                exit(self,1)

        self.tokens=self.parsed["tokens"]
        # the bot's token
        self.token=self.tokens["discordtoken"] 
        # the bot's prefix
        self.prefix=self.tokens["prefix"] 
        # the bot's settings
        self.settings_all=self.parsed["settings"]
        # the setting for a specific guild

    def update(self, data, guildid:str): 
        """ update a setting (not the token or prefix) """
        guildid = str(guildid)

        # re-read the contents of the settings file
        if self.path.exists(): # check if the file exists
            with open(self.path, "rt") as stream:
                self.parsed:dict=json.loads(stream.read())
                self.settings_all=self.parsed["settings"]

        # check if the right data type is supplied
        if type(data == dict) and len(data) > 0:
            try:
                self.settings_all[guildid].update(data)
                
            except KeyError: 
                if len(self.settings_all) == 0:
                    self.settings_all = {guildid:{
                        "busbr":False,
                        "nsfw":False,
                        "bomb":False}}
                    self.settings_all[guildid].update(data)
                else:
                    self.settings_all.update({guildid:{
                        "busbr":False,
                        "nsfw":False,
                        "bomb":False}})
                    self.settings_all[guildid].update(data)

            finally:
                self.parsed = deepcopy({"tokens": self.tokens, "settings":self.settings_all})
                # put the data into the json 
                datanew=json.dumps(self.parsed,indent=2)

                with open(self.path,"wt") as stream:
                    stream.write(datanew)
