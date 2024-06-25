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

    async def get(self, guild):
        """Get config json file"""
        try:
            async with aiofiles.open(os.path.join(self.data_dir, f"info/{guild.id}.json"), "r") as f:
                return json.loads(await f.read())
        except FileNotFoundError:
            default = await self.get_default()
            await self.update(guild, default)
            return await self.get(guild)

    async def update(self, guild, config):
        """Update guild config."""
        async with aiofiles.open(os.path.join(self.data_dir, f"info/{guild.id}.json"), "w") as f:
            await f.write(json.dumps(config))

    async def get_sections(self, ctx: discord.AutocompleteContext):
        """Autocomplete function for section names."""
        config = await self.get(ctx.interaction.guild)
        return [f"{id + 1}. {section['title']}" for id, section in enumerate(config) if section['title'].lower().startswith(ctx.value.lower())]



class NavigationView(View):
    def __init__(self, config_file = None, buttons: bool=False, dropdown: bool=True):
        super().__init__(timeout = None)
        if dropdown:
            self.add_dropdown(config_file)
        if buttons:
            self.add_buttons()

    def add_buttons(self):
        """Add navigation buttons."""
        prev = Button(emoji="⬅️", style=discord.ButtonStyle.gray, custom_id="prev")
        next = Button(emoji="➡️", style=discord.ButtonStyle.gray, custom_id="next")

        prev.callback = self.prev_button_callback
        next.callback = self.next_button_callback

        self.add_item(prev)
        self.add_item(next)

    def add_dropdown(self, config_file):
        """Add dropdown with options."""
        options = []
        for id, section in enumerate(config_file):
            if discord_emoji.to_uni(section["emoji"]):
                options.append(discord.SelectOption(label=f'{id + 1}. {section["title"]}', emoji=discord_emoji.to_uni(section["emoji"])))
            else:
                options.append(discord.SelectOption(label=f'{id + 1}. {section["title"]}', emoji=section["emoji"]))

        select = Select(
            placeholder='Select a section...', 
            min_values=1, 
            max_values=1, 
            options=options
        )

        select.callback = self.dropdown_callback

        self.add_item(select)

    async def prev_button_callback(self, interaction: discord.Interaction):
        """Callback function for the previous button."""
        await interaction.response.send_message("You selected prev button!")

    async def next_button_callback(self, interaction: discord.Interaction):
        """Callback function for the next button."""
        await interaction.response.send_message("You selected next button!")

    async def dropdown_callback(self, interaction: discord.Interaction):
        """Callback function for the dropdown selection."""
        await interaction.response.send_message("You selected a section!")



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
        
        config_file = await self.config.get(ctx.guild)
        navigation = NavigationView(config_file, buttons=False, dropdown=True)

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
