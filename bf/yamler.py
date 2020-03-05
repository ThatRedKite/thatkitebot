import yaml
from pathlib import Path
import asyncio
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

    def initialize(self, initdict):
        file = Path(self.path)
        if not file.exists() and len(initdict) > 0:
            self.write(data=initdict)

