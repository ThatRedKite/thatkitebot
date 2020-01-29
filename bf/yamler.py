import yaml
from pathlib import Path

"""
def yamlhandle():
    file = Path("data/tokens.yml")
    
    if file.exists():
        with open(file, "r") as steam:
            a = yaml.safe_load(steam)
            return a
    else:
        empty = {
            "discordtoken": "",
            "sudoers": "",
            "token": ""
        }
        

        with open(file, "w") as dump:
            yaml.dump(empty,dump,default_flow_style=False)
            yamlhandle()


def yamlsave(file, data):
    with open(file, "w") as dump:
        yaml.dump(data, dump, default_flow_style=False)


def yamlload(file):
    file = Path(file)
    if file.exists():
        with open(file, "r") as stream:
            return yaml.safe_load(stream)
"""
class Yamler:
    def __init__(self, path):
        self.path = path

    def load(self):
        file = Path(self.path)
        if file.exists():
            with open(file, "r") as stream:
                a = yaml.safe_load(stream)
                return a

    def write(self, data):
        file = Path(self.path)
        if file.exists():
            with open(file, "w") as dump:
                yaml.dump(data, dump, default_flow_style=False)

    def initialize(self):
        file = Path(self.path)
        empty = {
            "discordtoken": "",
            "prefix": ""
        }
        if not file.exists():
            self.write(data=empty)

        