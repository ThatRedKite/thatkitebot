import toml
from pathlib import Path
import asyncio
import subprocess
class Tomler:
    def __init__(self, dirname:str): 
        """handles different bot settings using the TOML file format"""
        # set the absolute path to the settingsz file
        self.path=Path(f"{dirname}/data/settings.toml")
        # load the settings file and parse it
        if self.path.exists(): # check if the file exists
            with open(self.path, "rt") as stream:
                self.parsed:dict=toml.loads(stream.read())
        else:
            raise FileNotFoundError

        self.tokens=self.parsed["tokens"]
        # the bot's token
        self.token=self.tokens["discordtoken"] 
        # the bot's prefix
        self.prefix=self.tokens["prefix"] 
        # the bot's settings
        self.settings=self.parsed["settings"] 

    def update(self, data): 
        """ update a setting (not the token or prefix) """
        if type(data == dict): 
            self.settings.update(data)
        self.parsed = {"tokens": self.tokens, "settings": self.settings}
        if self.path.exists(): 
            with open(self.path, "wt") as stream: 
                stream.write(toml.dumps(self.parsed))
        