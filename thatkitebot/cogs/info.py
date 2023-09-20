#  Copyright (c) 2019-2023 ThatRedKite and contributors

import os
import re
import json
import random
from pathlib import Path
import discord_emoji
import aiofiles

import discord
from discord.ext import commands
from discord.ui import Select, View, Button
from discord.commands import Option, SlashCommandGroup

from thatkitebot.base.util import PermissonChecks as pc
from thatkitebot.embeds.info import *


# generate random 24 bit number
def gen_random_hex_color():
    def get_int():
        return random.randint(0, 255)

    return f'0x{get_int():02X}{get_int():02X}{get_int():02X}'


# check if given string is valid discord emoji
def check_emoji(emoji):
    emoji_regex = r"<\S+:\d+>"
    if len(emoji) == 1:
        return True
    elif re.match(emoji_regex, emoji):
        return True
    else:
        return False


def check_hex(hex):
    hex_regex = r"^0x[0-9a-fA-F]+$"
    if re.match(hex_regex, hex):
        return True

    return False


class FieldModal(discord.ui.Modal):
    def __init__(self, bot, config, section_id, field_id, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.bot = bot
        self.config = config
        self.section_id = section_id
        self.field_id = field_id

        name = config[section_id]["fields"][field_id]["name"]
        contents = config[section_id]["fields"][field_id]["value"]
        inline = config[section_id]["fields"][field_id]["inline"]

        _title = discord.ui.InputText(
            label="Title",
            value=name if name != "" else "Example title 💡",
            placeholder="Think of an interesting title",
            max_length=256
        )

        _contents = discord.ui.InputText(
            label="Contents",
            value=contents if contents != "" else "[Example hyperlink](https://github.com/ThatRedKite/thatkitebot)",
            placeholder="Here you can type the contents of this field in your embed",
            style=discord.InputTextStyle.long,
            max_length=1024
        )

        _inline = discord.ui.InputText(
            label="In-line",
            value=inline if inline != "" else "True",
            placeholder="True or False",
            max_length=5
        )

        self.add_item(_title)
        self.add_item(_contents)
        self.add_item(_inline)

    async def callback(self, interaction: discord.Interaction):

        self.config[self.section_id]["fields"][self.field_id]["name"] = self.children[0].value  # set title of the field
        self.config[self.section_id]["fields"][self.field_id]["value"] = self.children[
            1].value  # set value of the field

        # check if "inline" input value is correct
        if str(self.children[2].value).lower() == "true":
            self.config[self.section_id]["fields"][self.field_id]["inline"] = True
        elif str(self.children[2].value).lower() == "false":
            self.config[self.section_id]["fields"][self.field_id]["inline"] = False
        else:
            await interaction.response.send_message("Invalid `in-line` value!", ephemeral=True)
            return

        # update config
        await self.bot.get_cog("Info").update_config(interaction.guild, self.config)

        await interaction.response.send_message(
            f"Field with ID {self.field_id + 1} in section {self.config[self.section_id]['title']} has been changed.")


class InfoCog(commands.Cog, name="Info"):
    def __init__(self, bot):
        self.bot: discord.Bot = bot
        self.current_embed = None

        self.main_view = None

        self.buttons = [
            Button(
                emoji="⬅️",
                style=discord.ButtonStyle.gray,
                custom_id="prev"
            ),
            Button(
                emoji="➡️",
                style=discord.ButtonStyle.gray,
                custom_id="next",

            )
        ]

        for button in self.buttons: button.callback = self.button_callback

        ###### "Utility" functions ######

    # section list for autocompletion
    async def get_sections(self, ctx: discord.AutocompleteContext):
        return [f"{id + 1}. {section['title']}" for id, section in
                enumerate(await self.get_config(ctx.interaction.guild))
                if f"{id + 1}. {section['title']}".lower().startswith(ctx.value.lower())]

    # field edit options list for autocompletion 
    async def get_options(self, ctx: discord.AutocompleteContext):
        return [section for section in ["add", "edit", "remove"] if section.lower().startswith(ctx.value.lower())]

    # get config file
    async def get_config(self, guild):
        async with aiofiles.open(os.path.join(self.bot.data_dir, f"info/{guild.id}.json"), "r") as f:
            return json.loads("".join([line async for line in f]))

    # get default config file
    async def get_default_config(self):
        async with aiofiles.open(os.path.join(self.bot.data_dir, f"info/info.json"), "r") as f:
            return json.loads("".join([line async for line in f]))

    # update config file
    async def update_config(self, guild, data: dict):
        async with aiofiles.open(os.path.join(self.bot.data_dir, f"info/{guild.id}.json"), "w") as f:
            await f.write(json.dumps(data))

    # setting up view for main dropdown menu
    async def get_dropdown(self, guild):
        option_list = []
        for id, section in enumerate(await self.get_config(guild)):
            if discord_emoji.to_uni(
                    section["emoji"]):  # if it's standard emoji (e.g. :smile:) it has to be converted to unicode
                option_list.append(discord.SelectOption(label=f'{id + 1}. {section["title"]}',
                                                        emoji=discord_emoji.to_uni(section["emoji"])))
            else:
                option_list.append(discord.SelectOption(label=f'{id + 1}. {section["title"]}', emoji=section["emoji"]))

        return Select(options=option_list)

    # check if given section name has valid id and returns it if so     
    async def check_section_id(self, section, guild):
        config = await self.get_config(guild)
        try:
            id = int(section.split(".")[0]) - 1
            if not (id >= 0 and id < len(config)):
                return -1
        except:
            return -1

        return id

    ###### Commands ######   

    @commands.slash_command(name="info")
    async def info(self, ctx: discord.ApplicationContext,
                   section: Option(str, "Pick a section!", required=False, autocomplete=get_sections) = None,
                   disable_navigation: Option(bool, "True or False", required=False, name="disable-navigation") = None):
        """
        Sends YT channels, documents, books etc. related to chosen science topic arranged in convenient way.
        """

        # load default config if not already done
        await self.load_defaults(ctx.guild)

        # check if section is provided
        if disable_navigation and not section:
            await ctx.respond("If you want to disable navigation, you need to specify a section!", ephemeral=True)
            return

        # setting up view for embeds
        dropdown = await self.get_dropdown(ctx.guild)
        dropdown.callback = self.info_dropdown_callback

        dropdown_view = View()
        dropdown_view.add_item(dropdown)

        self.main_view = View()
        self.main_view.add_item(dropdown)
        for button in self.buttons: self.main_view.add_item(button)

        id = await self.check_section_id(section, ctx.guild)
        if section is not None:
            if id < 0:
                await ctx.respond("Incorrect section name!", ephemeral=True)
                return

            if disable_navigation:
                await ctx.respond(embed=await get_embed(id, await self.get_config(ctx.guild)))
            else:
                await ctx.respond(embed=await get_embed(id, await self.get_config(ctx.guild)), view=self.main_view)
        else:
            await ctx.respond("Choose a section!", view=dropdown_view)

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
        config = await self.get_config(ctx.guild)

        # check if given string is valid discord emoji
        if not check_emoji(emoji=emoji):
            await ctx.respond("Invalid emoji!", ephemeral=True)
            return

        # if it's unicode emoji, convert it into string
        if discord_emoji.to_discord(emoji):
            emoji = f":{discord_emoji.to_discord(emoji, get_all=True)}:"

        # check if color format is valid
        if color:
            if check_hex(color):
                color = int(color, base=16)
            else:
                await ctx.respond("Invalid color format!", ephemeral=True)
                return
        else:
            color = int(gen_random_hex_color(), base=16)

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

        config.append(dictionary)
        await self.update_config(ctx.guild, config)

        await ctx.respond(f"Section {name} {emoji} has been created, now you can add a new field or edit existing one.")

    @info_settings.command(name="remove-section")
    async def remove_section(self, ctx, name: Option(str, "Pick a section!", required=True, autocomplete=get_sections)):
        """Remove section in /info command"""
        config = await self.get_config(ctx.guild)

        id = await self.check_section_id(name, ctx.guild)
        if id < 0:
            await ctx.respond("Incorrect section name!", ephemeral=True)
            return

        name = config[id]["title"]
        emoji = config[id]["emoji"]

        del config[id]

        await self.update_config(ctx.guild, config)
        await ctx.respond(f"Section {name} {emoji} has been removed.")

    @info_settings.command(name="edit-field")
    async def edit_field(self, ctx: discord.ApplicationContext,
                         section: Option(str, "Pick a section!", required=True, autocomplete=get_sections),
                         option: Option(str, "Choose option.", required=True, autocomplete=get_options)):
        """Add, edit or remove a field in section"""

        config = await self.get_config(ctx.guild)

        empty_field = {
            "name": "",
            "value": "",
            "inline": True
        }

        # check if "option" input is valid
        if option != "edit" and option != "remove" and option != "add":
            await ctx.respond("Incorrect option!", ephemeral=True)
            return

        # check if given section name has valid id
        id = await self.check_section_id(section, ctx.guild)
        if id < 0:
            await ctx.respond("Incorrect section name!", ephemeral=True)
            return

        # add empty field to config
        if option == "add":
            config[id]["fields"].append(empty_field)

            # prepare modal for user to edit field
            await self.update_config(ctx.guild, config)
            modal = FieldModal(title=f"Editing new field :pencil:",
                               config=await self.get_config(ctx.guild), section_id=id,
                               field_id=len(config[id]["fields"]) - 1, bot=self.bot)

            await ctx.send_modal(modal)
            return

        # check if there are any fields to edit/remove
        if len(config[id]["fields"]) == 0:
            await ctx.respond("There is no fields to edit/remove!")
            return

        # prepare dropdown list of existing fields to edit/remove
        option_list = []
        for field_id, section in enumerate(config[id]["fields"]):
            option_list.append(discord.SelectOption(label=f'{id + 1}.{field_id + 1}. {section["name"]}'))

        dropdown = Select(options=option_list)

        # set callback function to dropdown list according to selected option
        if option == "edit":
            dropdown.callback = self.edit_field_dropdown_callback
        elif option == "remove":
            dropdown.callback = self.remove_field_dropdown_callback

        dropdown_view = View()
        dropdown_view.add_item(dropdown)

        await ctx.respond(view=dropdown_view)

    @info_settings.command(name="edit-section")
    async def edit_section(self, ctx: discord.ApplicationContext,
                           section: Option(str, "Choose a section", required=True, autocomplete=get_sections),
                           title: Option(str, "Choose a title!", max_lenght=256, required=False) = None,
                           emoji: Option(str, "Choose an emoji! (e.g :lightbulb:)", required=False) = None,
                           color: Option(str, "Choose a color! (hex e.g. 0x123456)", required=False) = None):
        """Change name, emoji or color of given section"""

        config = await self.get_config(ctx.guild)

        # count how many properties have been changed
        counter = 0

        # check if given section name has valid id  
        id = await self.check_section_id(section, ctx.guild)
        if id < 0:
            await ctx.respond("Incorrect section name!", ephemeral=True)
            return

        _emoji = config[id]["emoji"]
        _title = config[id]["title"]

        # check if every input is valid and if so - change them in config
        if title:
            config[id]["title"] = title
            counter += 1
        if emoji:
            # check if given string is valid discord emoji
            if not check_emoji(emoji):
                await ctx.respond("Invalid emoji!", ephemeral=True)
                return
            # if it's unicode emoji, convert it into string
            if discord_emoji.to_discord(emoji):
                emoji = f":{discord_emoji.to_discord(emoji, get_all=True)}:"

            config[id]["emoji"] = emoji
            counter += 1
        if color:
            try:
                color = int(color, base=16)
            except Exception as e:
                await ctx.respond("Invalid color format!", ephemeral=True)
                return

            config[id]["color"] = color
            counter += 1

        await self.update_config(ctx.guild, config)
        await ctx.respond(f"{counter} properties has been changed in {_title} {_emoji}")

    @info_settings.command(name="edit-footer")
    async def edit_footer(self, ctx, name: Option(str, "Pick a section!", required=True, autocomplete=get_sections),
                          footer: Option(str, required=True, max_lenght=2048)):
        """Edit section footer in /info command"""
        config = await self.get_config(ctx.guild)

        # check if given section name has valid id  
        id = await self.check_section_id(name, ctx.guild)
        if id < 0:
            await ctx.respond("Incorrect section name!", ephemeral=True)
            return

        # edit footer and update config
        config[id]["footer"] = footer
        await self.update_config(ctx.guild, config)

        await ctx.respond("Footer has been changed.")

    @info_settings.command(name="factory-reset")
    async def factory_reset(self, ctx):
        view = View()

        buttons = [
            Button(
                emoji="✅",
                style=discord.ButtonStyle.gray,
                custom_id="yes"
            ),
            Button(
                emoji="⛔",
                style=discord.ButtonStyle.gray,
                custom_id="no"
            )
        ]

        for button in buttons: button.callback = self.reset_callback
        for button in buttons: view.add_item(button)

        await ctx.respond("Are you sure? It will **replace all of your sections.**", view=view)

    ###### Callbacks ######   

    async def info_dropdown_callback(self, interaction: discord.Interaction):
        id = await self.check_section_id(interaction.data["values"][0], interaction.guild)
        self.current_embed = id
        await interaction.response.edit_message(embed=await get_embed(id, await self.get_config(interaction.guild)),
                                                view=self.main_view, content=None)

    async def edit_field_dropdown_callback(self, interaction: discord.Interaction):
        # get id and field id
        id = int(interaction.data["values"][0].split(".")[0]) - 1
        field_id = int(interaction.data["values"][0].split(".")[1]) - 1

        modal = FieldModal(title=f"Field editor :pencil:",
                           config=await self.get_config(interaction.guild), section_id=id, field_id=field_id,
                           bot=self.bot)

        await interaction.response.send_modal(modal)

    async def remove_field_dropdown_callback(self, interaction: discord.Interaction):
        # get id and field id
        id = int(interaction.data["values"][0].split(".")[0]) - 1
        field_id = int(interaction.data["values"][0].split(".")[1]) - 1

        config = await self.get_config(interaction.guild)
        name = config[id]["title"]
        emoji = config[id]["emoji"]

        del config[id]["fields"][field_id]

        await self.update_config(interaction.guild, config)
        await interaction.response.edit_message(
            content=f"Field no. {field_id} has been removed from section {name} {emoji}.", view=None)

    async def button_callback(self, interaction: discord.Interaction):
        config = await self.get_config(interaction.guild)
        max_id = len(config) - 1

        if interaction.custom_id == "next":
            self.current_embed += 1
            if self.current_embed > max_id:
                self.current_embed = 0
        else:
            self.current_embed -= 1
            if self.current_embed < 0:
                self.current_embed = max_id

        await interaction.response.edit_message(embed=await get_embed(self.current_embed, config), view=self.main_view,
                                                content=None)

    async def reset_callback(self, interaction: discord.Interaction):
        """Factory reset all the sections in /info """

        if interaction.custom_id == "no":
            await interaction.response.edit_message(content="Nothing has changed.", view=None)
        else:
            # load default config
            default_config = await self.get_default_config()

            # replace the contents of the file with the default values
            await self.update_config(interaction.guild, default_config)

            await interaction.response.edit_message(content="Default settings have been restored.", view=None)

    # this initializes default /info content for the guild the bot joins
    @commands.Cog.listener(name="on_guild_join")
    async def load_defaults(self, guild):
        # check if there already is a config for the guild present
        if not Path(os.path.join(self.bot.data_dir, "info", f"{guild.id}.json")).exists():
            # load default config
            default_config = await self.get_default_config()

            # make config file for a guild
            await self.update_config(guild, default_config)


def setup(bot):
    bot.add_cog(InfoCog(bot))
