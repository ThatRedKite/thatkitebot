"""
MIT License

Copyright (c) 2020 ThatRedKite

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import json
import logging
from copy import deepcopy
from os import path
from pathlib import Path


class TokenError(Exception):
    pass


class TokenErrorCritical(Exception):
    pass


class Tomler:
    def __init__(self, dirname: str):
        logging.basicConfig(
            filename="{0}/test.log".format(dirname),
            level=logging.WARN,
            format="%(levelname)s|%(message)s| @ %(asctime)s")

        # set the absolute path to the settings file
        self.path = Path(path.join(dirname, "data/settings.json"))
        # load the settings file and parse it
        if self.path.exists():  # check if the file exists
            with open(self.path, "rt") as stream:
                self.parsed: dict = json.loads(stream.read())
        else:
            initdict = {"tokens": {"discordtoken": "", "prefix": "", "tenortoken": ""}, "settings": {}}
            with open(self.path, "wt") as stream:
                stream.write(json.dumps(initdict, indent=2))
                print(f"""
                Your settings.json file was created in {self.path}
                 , please enter your bot token and prefix there!
                 The program is now terminating""")
                exit(8)
        try:
            self.tokens = self.parsed["tokens"]
            # the bot's discord token
            self.token = self.tokens["discordtoken"]
            if len(self.token) == 0 or self.token is None:
                raise TokenErrorCritical("invalid discord token")

            # token for tenor
            self.tenortoken = self.tokens["tenortoken"]
            if len(self.tenortoken) == 0 or self.tenortoken is None:
                raise TokenError("invalid tenor token")

            # the bot's prefix
            self.prefix = self.tokens["prefix"]
            if len(self.prefix) == 0 or self.prefix is None:
                raise TokenErrorCritical("invalid prefix")

            # the bot's settings
            self.settings_all = self.parsed["settings"]
            # the settings for a specific guild

        except (KeyError, TokenErrorCritical, json.JSONDecodeError) as exc:
            logging.critical(f"{str(type(exc))}: {exc}")

            raise exc

        except TokenError as exc:
            print(TokenError)
            logging.warning(exc.message)

    def update(self, data, guildid: str):
        """ update a setting (not the token or prefix) """
        guildid = str(guildid)

        # re-read the contents of the settings file
        if self.path.exists():  # check if the file exists
            with open(self.path, "rt") as stream:
                self.parsed: dict = json.loads(stream.read())
                self.settings_all = self.parsed["settings"]

        # check if the right data type is supplied
        if type(data) == dict and len(data) > 0:
            try:
                self.settings_all[guildid].update(data)

            except KeyError:
                if len(self.settings_all) == 0:
                    self.settings_all = {
                        guildid: {
                            "busbr": False,
                            "nsfw": False,
                            "bomb": False}
                    }
                    self.settings_all[guildid].update(data)
                else:
                    self.settings_all.update({
                        guildid: {
                            "busbr": False,
                            "nsfw": False,
                            "bomb": False}
                    })
                    self.settings_all[guildid].update(data)

            finally:
                self.parsed = deepcopy({"tokens": self.tokens, "settings": self.settings_all})
                # put the data into the json 
                datanew = json.dumps(self.parsed, indent=2)

                with open(self.path, "wt") as stream:
                    stream.write(datanew)


class DataMan:
    def __init__(self):
        pass
