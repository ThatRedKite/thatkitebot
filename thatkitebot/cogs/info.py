import os
import re
import json
import random
from pathlib import Path

import aiofiles
import discord_emoji
import discord
from discord.ext import commands
from discord.ui import Select, View, Button
from discord.commands import Option, SlashCommandGroup

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
        config = await self.get(ctx.interaction.guild)
        return [f"{id + 1}. {section['title']}" for id, section in enumerate(config) if section['title'].lower().startswith(ctx.value.lower())]


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

        if dropdown:
            self.add_dropdown(config_file)
        if buttons:
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

        if disable_navigation and not section:
            await ctx.respond("Specify a section to disable navigation!", ephemeral=True)
            return
        
        navigation = await NavigationView.create(ctx.guild, self.config, toggle = disable_navigation)

        await ctx.respond("Choose a section!", view=navigation)
        
    # TODO it's just temporary debug function    
    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """Error handler for the cog."""
        await ctx.send(f"{error}")

    @commands.Cog.listener(name="on_guild_join")
    async def load_defaults(self, guild):
        """Load default config file when bot joins guild."""
        if not self.config.exists(guild):
            await self.config.load_default(guild)

def setup(bot):
    bot.add_cog(InfoCog(bot))
