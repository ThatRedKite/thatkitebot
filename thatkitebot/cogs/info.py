import os
import re
import json
import random
from pathlib import Path
from typing import Literal

import aiofiles
import discord_emoji
import discord
from discord.ext import commands
from discord.ui import Select, View, Button, Modal, InputText
from discord.commands import Option, SlashCommandGroup

from thatkitebot.base.util import PermissonChecks as pc
from thatkitebot.embeds.info import *

class Config:
    def __init__(self, bot, data_dir):
        self.bot = bot
        self.data_dir = data_dir

    def exists(self, guild):
        """Check if guild config file exists."""
        return Path(self.data_dir, f"info/{guild.id}.json").exists();

    async def get_default(self):
        """Retrieve default config."""
        async with aiofiles.open(os.path.join(self.data_dir, "info/info.json"), "r") as f:
            return json.loads(await f.read())

    async def load_default(self, guild):
        """Load default config for guild."""
        await self.update(guild, await self.get_default())

    async def update(self, guild, config):
        """Update guild config."""
        async with aiofiles.open(os.path.join(self.data_dir, f"info/{guild.id}.json"), "w") as f:
            await f.write(json.dumps(config))

    async def get(self, guild):
        """Get config json file"""
        try:
            async with aiofiles.open(os.path.join(self.data_dir, f"info/{guild.id}.json"), "r") as f:
                return json.loads(await f.read())
        except FileNotFoundError:
            default = await self.get_default()
            await self.update(guild, default)
            return await self.get(guild)

    async def size(self, guild):
        """Get an amount of entries in config file"""
        config_file = await self.get(guild)
        return len(config_file)

    async def get_sections(self, ctx: discord.AutocompleteContext):
        """Autocomplete function for section names."""
        config = await self.config.get(ctx.interaction.guild)
        return [f"{id + 1}. {section['title']}" for id, section in enumerate(config) if section['title'].lower().startswith(ctx.value.lower())]


class InfoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config(bot, bot.data_dir)

    @commands.slash_command(name="info")
    async def info(self, ctx: discord.ApplicationContext, 
                    section: Option(str, "Pick a section!", required=False, autocomplete=Config.get_sections) = None, # type: ignore
                    disable_navigation: Option(bool, "Disable navigation", required=False) = False): # type: ignore
        """
        Sends YT channels, documents, books etc. related to chosen science topic arranged in convenient way.
        """

        # load default config if not already done
        await self.load_defaults(ctx.guild)

        config_file = await self.config.get(ctx.guild)

        if disable_navigation and not section:
            await ctx.respond("Specify a section to disable navigation!", ephemeral=True)
            return
        
        if section:
            navigation = await NavigationView.create(ctx.guild, self.config, toggle = disable_navigation, buttons= True)
            section_id = await Utility.retrive_section_id(section, len(config_file))
            embed = await get_embed(section_id, config_file)
            await ctx.respond(embed = embed, content = None, view=navigation)
            return

        navigation = await NavigationView.create(ctx.guild, self.config, toggle = disable_navigation)
        await ctx.respond("Choose a section!", view=navigation)


    ###### Group commands ######

    info_settings = SlashCommandGroup(
        "info-settings",
        "Settings for /info command",
        checks=[pc.mods_can_change_settings]
    )

    @info_settings.command(name="add-section")
    async def new_section(self, ctx: discord.ApplicationContext,
                          name: Option(str, "Choose a name!", required=True, max_lenght=256),
                          emoji: Option(str, "Choose an emoji! (e.g :lightbulb:)", required=True),
                          color: Option(str, "Choose a color! (hex e.g. 0x123456)", required=False) = None):
        """
        Create new section in /info command
        """
        config_file = await self.config.get(ctx.guild)

        # check if given string is valid discord emoji
        if not Utility.check_emoji(emoji=emoji):
            await ctx.respond("Invalid emoji!", ephemeral=True)
            return

        # if it's unicode emoji, convert it into string
        if discord_emoji.to_discord(emoji):
            emoji = f":{discord_emoji.to_discord(emoji, get_all=True)}:"

        # check if color format is valid
        if color:
            if not Utility.convert_hex(color):
                await ctx.respond("Invalid color format!", ephemeral=True)
                return
            color = Utility.convert_hex(color)

        else:
            color = int(Utility.gen_random_hex_color(), base=16)

        dictionary = {
            "title": f"{name}",
            "emoji": f"{emoji}",
            "color": f"{color}",
            "fields": [
                {
                    "name": "",
                    "value": "",
                    "inline": True
                }
            ],
            "footer": "false"
        }

        config_file.append(dictionary)
        await self.config.update(ctx.guild, config_file)

        await ctx.respond(f"Section {name} {emoji} has been created, now you can add a new field or edit existing one.")

    @info_settings.command(name="remove-section")
    async def remove_section(self, ctx, name: Option(str, "Pick a section!", required=True, autocomplete=Config.get_sections)):
        """Remove section in /info command"""
        config_file = await self.config.get(ctx.guild)

        id = await Utility.retrive_section_id(name, len(config_file))
        if id < 0:
            await ctx.respond("Incorrect section name!", ephemeral=True)
            return

        name = config_file[id]["title"]
        emoji = config_file[id]["emoji"]

        del config_file[id]

        await self.config.update(ctx.guild, config_file)
        await ctx.respond(f"Section {name} {emoji} has been removed.")

    @info_settings.command(name="edit-field")
    async def edit_field(self, ctx: discord.ApplicationContext,
                         section: Option(str, "Pick a section!", required=True, autocomplete=Config.get_sections),
                         option: Option(str, "Choose option.", required=True, choices=["edit", "remove", "add"])):
        """Add, edit or remove a field in section"""

        config_file = await self.config.get(ctx.guild)

        empty_field = {
            "name": "",
            "value": "",
            "inline": True
        }

        # check if "option" input is valid
        if option not in {"edit", "remove", "add"}:
            await ctx.respond("Incorrect option!", ephemeral=True)
            return

        # check if given section name has valid id
        id = await Utility.retrive_section_id(section, len(config_file))
        if id < 0:
            await ctx.respond("Incorrect section name!", ephemeral=True)
            return

        # add empty field to config
        if option == "add":
            config_file[id]["fields"].append(empty_field)
            new_field_id = len(config_file[id]["fields"]) - 1

            # prepare modal for user to edit field
            await self.config.update(ctx.guild, config_file)
            config_file = await self.config.get(ctx.guild)
            modal = FieldModal(title=f"Editing new field {discord_emoji.to_uni(":pencil:")}",
                               config_file=config_file, section_id=id,
                               field_id= new_field_id, bot=self.bot)

            await ctx.send_modal(modal)
            return

        # check if there are any fields to edit/remove
        if len(config_file[id]["fields"]) == 0:
            await ctx.respond("There is no fields to edit/remove!")
            return

        # prepare dropdown list of existing fields to edit/remove
        view = await EditFieldsView.create(self.bot, ctx.guild, self.config, id, option)

        await ctx.respond(view=view)


    @info_settings.command(name="edit-section")
    async def edit_section(self, ctx: discord.ApplicationContext,
                            section: Option(str, "Pick a section!", required=True, autocomplete=Config.get_sections)):
        """Change name, emoji, footer or color of a given section"""
        config_file = await self.config.get(ctx.guild)

        section_id = await Utility.retrive_section_id(section, len(config_file))

        if section_id < 0:
            await ctx.respond("Incorrect section name!", ephemeral=True)
            return

        modal = EditSectionModal(self.config, config_file, section_id, title = "Edit Section")
        await ctx.send_modal(modal)

    @info_settings.command(name="factory-reset")
    async def factory_reset(self, ctx):
        """Factory reset of all the sections in /info """
        modal = FactoryResetModal(title="Factory Reset!", config=self.config)
        await ctx.send_modal(modal)


    # TODO it's just temporary debug function    
    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """Error handler for the cog."""
        await ctx.send(f"{error}")

    @commands.Cog.listener(name="on_guild_join")
    async def load_defaults(self, guild):
        """Load default config file when bot joins guild."""
        if not self.config.exists(guild):
            await self.config.load_default(guild)


###### Views ######

class NavigationView(View):
    def __init__(self, config, config_file, buttons, dropdown, toggle):
        super().__init__(timeout = None)

        self.config = config 
        self.config_file = config_file

        # Current states of the view contents
        self.toggle = toggle
        self.state_buttons = buttons
        self.state_dropdown = dropdown
        self.current_embed_id = None

        if dropdown and not toggle:
            self.add_dropdown(config_file)
        if buttons and not toggle:
            self.add_buttons()

    @staticmethod
    async def create(guild, config: Config = None, buttons: bool=False, dropdown: bool= True, toggle: bool = False):
        return NavigationView(config, await config.get(guild), buttons, dropdown, toggle)

    def add_buttons(self):
        """Add navigation buttons."""
        prev = Button(emoji="⬅️", style=discord.ButtonStyle.gray, custom_id="prev")
        next = Button(emoji="➡️", style=discord.ButtonStyle.gray, custom_id="next")

        prev.callback = self.button_callback
        next.callback = self.button_callback

        self.add_item(prev)
        self.add_item(next)

    def add_dropdown(self, config_file):
        """Add dropdown with options."""
        options = []
        for id, section in enumerate(config_file):
            if discord_emoji.to_uni(section["emoji"]):
                options.append(discord.SelectOption(label=f'{id + 1}. {section["title"]}', emoji=discord_emoji.to_uni(section["emoji"]), value = f"{id}"))
            else:
                options.append(discord.SelectOption(label=f'{id + 1}. {section["title"]}', emoji=section["emoji"], value = f"{id}"))

        select = Select(
            placeholder='Select a section...', 
            min_values=1, 
            max_values=1, 
            options=options
        )

        select.callback = self.dropdown_callback

        self.add_item(select)

    async def button_callback(self, interaction: discord.Interaction):
        """Callback function for the next button."""
        max_id = await self.config.size(interaction.guild)

        if interaction.custom_id == "next":
            self.current_embed_id = (self.current_embed_id + 1) % max_id
        else:
            self.current_embed_id = (self.current_embed_id - 1) % max_id

        config_file = await self.config.get(interaction.guild)
        embed = await get_embed(self.current_embed_id, config_file)

        await interaction.response.edit_message(embed=embed, content=None, view = self)


    async def dropdown_callback(self, interaction: discord.Interaction):
        """Callback function for the dropdown selection."""
        self.current_embed_id = int(interaction.data["values"][0])
        config_file = await self.config.get(interaction.guild)

        embed = await get_embed(self.current_embed_id, config_file)

        if(self.toggle):
            self.disable_all_items
        else:
            if(not self.state_buttons): 
                self.add_buttons()
                self.state_buttons = True
            if(not self.state_dropdown): 
                self.add_dropdown(config_file)
                self.state_dropdown =  True

        await interaction.response.edit_message(embed=embed, content=None, view = self)

class EditFieldsView(View):
    def __init__(self, bot, config, config_file, id ,action):
        super().__init__(timeout = None)

        self.bot = bot
        self.config = config 
        self.config_file = config_file

        self.add_dropdown(config_file, id, action)

    @staticmethod
    async def create(bot, guild, config: Config, id, action: Literal["edit", "remove"]):
        return EditFieldsView(bot, config, await config.get(guild), id, action)

    def add_dropdown(self, config_file, id, action):
        """Add dropdown with options."""
        options = []
        for field_id, section in enumerate(config_file [id]["fields"]):
            options.append(discord.SelectOption(label=f'{id + 1}.{field_id + 1}. {section["name"]}'))

        select = Select(
            placeholder='Select a field...', 
            min_values=1, 
            max_values=1, 
            options=options
        )

        if(action == "remove"):
            select.callback = self.remove_field_callback
        if(action == "edit"):
            select.callback = self.edit_field_callback

        self.add_item(select)

    async def edit_field_callback(self, interaction: discord.Interaction):
        # get id and field id
        id = int(interaction.data["values"][0].split(".")[0]) - 1
        field_id = int(interaction.data["values"][0].split(".")[1]) - 1

        modal = FieldModal(title=f"Field editor :pencil:",
                           config_file=await self.config.get(interaction.guild), section_id=id, field_id=field_id,
                           bot=self.bot)

        await interaction.response.send_modal(modal)

    async def remove_field_callback(self, interaction: discord.Interaction):
        # get id and field id
        id = int(interaction.data["values"][0].split(".")[0]) - 1
        field_id = int(interaction.data["values"][0].split(".")[1]) - 1

        config_file = await self.config.get(interaction.guild)
        name = config_file[id]["title"]
        emoji = config_file[id]["emoji"]

        del config_file[id]["fields"][field_id]

        await self.config.update(interaction.guild, config_file)
        await interaction.response.edit_message(
            content=f"Field no. {field_id + 1} has been removed from section {name} {emoji}.", view=None)


###### Modals ######

class FieldModal(Modal):
    def __init__(self, bot, config_file, section_id, field_id, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.bot = bot
        self.config_file = config_file
        self.section_id = section_id
        self.field_id = field_id

        name = config_file[section_id]["fields"][field_id]["name"]
        contents = config_file[section_id]["fields"][field_id]["value"]
        inline = config_file[section_id]["fields"][field_id]["inline"]

        _title = InputText(
            label="Title",
            value=name if name != "" else "Example title 💡",
            placeholder="Think of an interesting title",
            max_length=256
        )

        _contents = InputText(
            label="Contents",
            value=contents if contents != "" else "[Example hyperlink](https://github.com/ThatRedKite/thatkitebot)",
            placeholder="Here you can type the contents of this field in your embed",
            style=discord.InputTextStyle.long,
            max_length=1024
        )

        _inline = InputText(
            label="In-line",
            value=inline if inline != "" else "true",
            placeholder="Type \"true\" or \"false\"",
            max_length=5
        )

        self.add_item(_title)
        self.add_item(_contents)
        self.add_item(_inline)

    async def callback(self, interaction: discord.Interaction):

        self.config_file[self.section_id]["fields"][self.field_id]["name"] = self.children[0].value  # set title of the field
        self.config_file[self.section_id]["fields"][self.field_id]["value"] = self.children[1].value  # set value of the field

        # Check if "inline" input value is correct
        inline_value = str(self.children[2].value).strip().lower()

        if inline_value in {"true", "false"}:
            self.config_file[self.section_id]["fields"][self.field_id]["inline"] = (inline_value == "true")
        else:
            await interaction.response.send_message("Invalid `in-line` value!", ephemeral=True)
            return

        # update config
        await self.bot.get_cog("InfoCog").config.update(interaction.guild, self.config_file)

        await interaction.response.send_message(
            f"Field with ID {self.field_id + 1} in section {self.config_file[self.section_id]['title']} has been changed.")

        
class FactoryResetModal(Modal):
    def __init__(self, config, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.config = config

        _decision = InputText(
            label="Are you sure? Type \"YES\" or \"NO\"",
            placeholder="It will **replace all of your sections!",
            max_length=3
        )

        self.add_item(_decision)

    async def callback(self, interaction: discord.Interaction):
        """Factory reset all the sections in /info """

        if self.children[0].value == "YES":
             # load default config
            default_config = await self.config.get_default()

            # replace the contents of the file with the default values
            await self.config.update(interaction.guild, default_config)

            await interaction.response.send_message(content="Default settings have been restored.", view=None)
        else:
            await interaction.response.send_message(content="Nothing has changed.", view=None)


class EditSectionModal(Modal):
    def __init__(self, config, config_file ,section_id,*args, **kwargs) -> None:
        self.section_id = section_id
        self.config = config
        super().__init__(*args, **kwargs)

        title = config_file[self.section_id]["title"]
        emoji = config_file[self.section_id]["emoji"]
        color = hex(config_file[self.section_id]["color"])
        footer = config_file[self.section_id]["footer"]


        self.add_item(InputText(label="Title", value = title, placeholder="Choose a title!", max_length=256, required=False))
        self.add_item(InputText(label="Emoji", value = emoji, placeholder="Choose an emoji! (e.g :lightbulb:)", required=False))
        self.add_item(InputText(label="Color", value = color, placeholder="Choose a color! (hex e.g. 0x123456)", required=False))
        self.add_item(InputText(label="Footer", value = footer, placeholder="Choose a footer!", max_length=2048, required=False))

    async def callback(self, interaction: discord.Interaction):
        title = self.children[0].value
        emoji = self.children[1].value
        color = self.children[2].value
        footer = self.children[3].value

        config_file = await self.config.get(interaction.guild)
        old_emoji = config_file[self.section_id]["emoji"]
        old_section_title = config_file[self.section_id]["title"]

        counter = 0

        config_file[self.section_id]["title"] = title
        config_file[self.section_id]["footer"] = footer

        if emoji:
            if not Utility.check_emoji(emoji):
                await interaction.response.send_message("Invalid emoji!", ephemeral=True)
                return

            if discord_emoji.to_discord(emoji):
                emoji = f":{discord_emoji.to_discord(emoji, get_all=True)}:"

            config_file[self.section_id]["emoji"] = emoji

        if color:
            if not Utility.convert_hex(color):
                await interaction.response.send_message("Invalid color format!", ephemeral=True)
                return
            
            config_file[self.section_id]["color"] = Utility.convert_hex(color)

        await self.config.update(interaction.guild, config_file)
        await interaction.response.send_message(f"Section {old_section_title} {old_emoji} has beed updated", ephemeral=True)

###### Utility ######

class Utility:
    # generate random 24 bit number
    @staticmethod
    def gen_random_hex_color():
        def get_int():
            return random.randint(0, 255)

        return f'0x{get_int():02X}{get_int():02X}{get_int():02X}'


    # check if given string is valid discord emoji
    @staticmethod
    def check_emoji(emoji):
        # Check if it's a standard emoji
        if len(emoji) == 1 and discord_emoji.to_discord(emoji, get_all=True):
            return True
        # Check if it's a custom Discord emoji (format: <name:id>)
        elif re.match(r"<:\w+:\d+>", emoji):
            return True
        # Check if it's a text emoji (format: :name:)
        elif discord_emoji.to_uni(emoji):
            return True
        else:
            return False

    @staticmethod
    def convert_hex(s):
        if s.startswith('#'):
            s = s[1:]
        try:
            val = int(s, 16)
            return val
        except ValueError:
            return None
    
    @staticmethod
    async def retrive_section_id(section_name, config_len):
        try:
            id = int(section_name.split(".")[0]) - 1
            if not (id >= 0 and id <= config_len):
                return -1
        except:
            return -1

        return id

def setup(bot):
    bot.add_cog(InfoCog(bot))
