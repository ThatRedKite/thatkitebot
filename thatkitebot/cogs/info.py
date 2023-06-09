#  Copyright (c) 2019-2023 ThatRedKite and contributors

import discord
from discord.ext import commands
from discord.ui import Select, View, Button
from discord.commands import Option

from thatkitebot.embeds.info import *


class InfoCog(commands.Cog, name="Info"):
    def __init__(self, bot):
        self.bot: discord.Bot = bot
        self.current_embed = None

        self.dropdown_view = None
        self.main_view = None

        # a list of the buttons
        self.buttons = [
            Button(
                emoji="⬅️",
                style=discord.ButtonStyle.gray,
                custom_id="prev",
            ),
            Button(
                emoji="➡️",
                style=discord.ButtonStyle.gray,
                custom_id="next",

            )
        ]

        # give every button a callback
        for button in self.buttons:
            button.callback = self.button_callback

        # it doesn't accept emoji tags like :bulb:
        self.dropdown = Select(options=[
            discord.SelectOption(label="General Science", emoji="🔬"),
            discord.SelectOption(label="Chemistry", emoji="⚗️"),
            discord.SelectOption(label="Mathematics", emoji="🧮"),
            discord.SelectOption(label="Physics", emoji="🧲"),
            discord.SelectOption(label="Nature, Botany and Biology", emoji="🍀"),
            discord.SelectOption(label="Meteorology", emoji="⛈️"),
            discord.SelectOption(label="Astronomy and Rocketry", emoji="🔭"),
            discord.SelectOption(label="Geology and Geography", emoji="🌎"),
            discord.SelectOption(label="Engineering", emoji="🪛"),
            discord.SelectOption(label="Electronics", emoji="💡"),
            discord.SelectOption(label="Lasers", emoji="⛔"),
            discord.SelectOption(label="IT", emoji="💻"),
            ])

        self.dropdown.callback = self.dropdown_callback

        # a dict of all the different embeds
        self.embeds = {
            "General Science": general_science_embed(),
            "Chemistry": chemistry_embed(),
            "Mathematics": mathematics_embed(),
            "Physics": physics_embed(),
            "Nature, Botany and Biology": biology_embed(),
            "Meteorology": meteorology_embed(),
            "Astronomy and Rocketry": astronomy_embed(),
            "Geology and Geography": geography_embed(),
            "Engineering": engineering_embed(),
            "Electronics": electronics_embed(),
            "Lasers": lasers_embed(),
            "IT": it_embed(),
        }

        # for auto-completion
        self.section_names = [
            "General Science",
            "Chemistry", 
            "Mathematics", 
            "Physics",
            "Nature, Botany and Biology",
            "Meteorology", 
            "Astronomy and Rocketry",
            "Geology and Geography",
            "Engineering", 
            "Electronics", 
            "Lasers", 
            "IT"
        ]

    async def get_sections(self, ctx: discord.AutocompleteContext):
        return [section for section in self.section_names if section.lower().startswith(ctx.value.lower())]

    @commands.slash_command(name="info")
    async def info(self, ctx, section: Option(str, "Pick a section!", required=False, autocomplete=get_sections) = None):
        """
        Sends YT channels, documents, books, etc.
        """
        # setting up view for dropdown menu
        self.dropdown_view = View()
        self.dropdown_view.add_item(self.dropdown)

        # setting up view for embeds
        self.main_view = View()
        self.main_view.add_item(self.dropdown)
        for button in self.buttons: self.main_view.add_item(button)

        if section is not None:
            try:
                await ctx.respond(embed=self.embeds[section], view=self.main_view)
            except:
                await ctx.respond("Incorrect section name!", delete_after=5.0)
        else:
            await ctx.respond("Choose a section!", view=self.dropdown_view)

    async def button_callback(self, interaction: discord.Interaction):
        if interaction.custom_id == "next":
            next_embed = await self.get_next_embed()
            self.current_embed = next_embed
            return await interaction.response.edit_message(embed=next_embed, view=self.main_view, content=None)
        else:
            prev = await self.get_previous_embed()
            self.current_embed = prev
            return await interaction.response.edit_message(embed=prev, view=self.main_view, content=None)

    async def dropdown_callback(self, interaction: discord.Interaction):
        for key in self.embeds:
            if key in self.dropdown.values:
                self.current_embed = self.embeds[key]
                return await interaction.response.edit_message(embed=self.embeds[key], view=self.main_view, content=None)

    async def get_next_embed(self):
        next_embed = None
        arr = list(self.embeds.values())
        for i in range(len(arr)):
            if arr[i] == self.current_embed:
                try:
                    next_embed = arr[i+1]
                except:
                    next_embed = arr[0]

        return next_embed

    async def get_previous_embed(self):
        prev_embed = None
        arr = list(self.embeds.values())
        for i in range(len(arr)):
            if arr[i] == self.current_embed:
                try:
                    prev_embed = arr[i-1]
                except:
                    prev_embed = arr[len(arr)-1]
        
        return prev_embed


def setup(bot):
    bot.add_cog(InfoCog(bot))
