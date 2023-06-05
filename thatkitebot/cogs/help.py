# Copyright (c) 2019-2022 ThatRedKite and contributors
#  Copyright (c) 2021 dunnousername

import discord
from discord.ext import commands, pages

from thatkitebot.base.util import list_chunker
import random

# thanks to dunnousername  for this help command. It was originally used in the styrobot discord bot
info = {
    'repo': 'https://github.com/ThatRedKite/thatkitebot',
    'name': 'ThatKiteBot'
}


class BetterHelpCommand(commands.HelpCommand):
    """
    Custom help command for the bot.
    """

    async def send_embed(self, embed: discord.Embed):
        embed.color = discord.Colour.random()
        await self.get_destination().send(embed=embed)

    async def send_embeds_paginated(self, embeds: list[discord.Embed]):
        paginator = pages.Paginator(pages=embeds, show_disabled=False, loop_pages=True)
        await paginator.send(self.context, self.context.channel)
        #await self.get_destination().send(embed=embed)

    def blank_line(self, embed):
        embed.add_field(name='_ _', value='_ _', inline=False)

    def signature(self, command: commands.Command):
        out = [command.qualified_name]
        params = command.clean_params or {}
        for name, param in params.items():
            # slightly copied from discord.py
            greedy = isinstance(param.annotation, commands.converter.Greedy)
            if param.default is not param.empty:
                should_print = param.default if isinstance(param.default, str) else param.default is not None
                if should_print:
                    out.append(f'[{name}={param.default}]{"..." if greedy else ""}')
                else:
                    out.append(f'[{name}]')
            elif param.kind == param.VAR_POSITIONAL:
                out.append(f'<{name}...>')
            elif greedy:
                out.append(f'[{name}]...')
            else:
                out.append(f'<{name}>')
        return ' '.join(out)

    async def send_bot_help(self, mapping):
        embed_pages = []    # list to store the pages in

        cogs = [(cog, await self.filter_commands(mapping[cog])) for cog in mapping.keys()]  # get all cogs
        cogs = [x for x in cogs if len(x[1]) > 0]  # ignore cogs without commands

        for cog, cmds in cogs:
            e = discord.Embed(title=info['name'])  # create the embed

            e.add_field(name='Contribute at', value=info['repo'], inline=False)  # include the repo in the header
            e.add_field(name='For help about a specific command use:', value='`+help <command>`', inline=False)
            e.color = self.context.bot.user.color

            if len(cmds) > 10:
                print("oh no")
                cmd_chunks = list(list_chunker(cmds, int(len(cmds) / 2)))  # split the command list into multiple lists
                for cmd_chunk in cmd_chunks:
                    h = "\n".join([cmd.name for cmd in cmd_chunk])
                    if cog is None:
                        e.add_field(name='builtin', value=h, inline=True)
                    else:
                        e.add_field(name=cog.qualified_name, value=h, inline=True)

            else:
                h = '\n'.join([cmd.name for cmd in cmds]) # add the commands
                if cog is None:
                    e.add_field(name='builtin', value=h, inline=True)
                else:
                    e.add_field(name=cog.qualified_name, value=h, inline=True)

            e.set_footer(text='Made with ❤️\nUse `+help <command>` to get detailed help about a specific command.')
            embed_pages.append(e)

        await self.send_embeds_paginated(embed_pages)

    async def send_cog_help(self, cog: commands.Cog):
        e = discord.Embed(title=cog.qualified_name)
        e.add_field(name='Cog', value=cog.qualified_name, inline=True)
        e.add_field(name='`in_code`', value=f'`{cog.__class__.__name__}`', inline=True)
        e.add_field(name='Commands', value='_ _', inline=False)
        for cmd in await self.filter_commands(cog.get_commands()):
            e.add_field(name=cmd, value=(cmd.help or '[no help]'), inline=False)
        await self.send_embed(e)

    async def send_group_help(self, group: commands.Group):
        e = discord.Embed(title=group.qualified_name)
        e.add_field(name='Command Group', value=group.qualified_name, inline=True)
        e.add_field(name='Help', value=(group.help or '[no help]'), inline=False)
        e.add_field(name='Subcommands', value='_ _', inline=False)
        for command in await self.filter_commands(group.commands):
            command: commands.Command
            e.add_field(name=self.signature(command), value=(command.help or '[no help]'), inline=False)
        await self.send_embed(e)

    async def send_command_help(self, command: commands.Command):
        e = discord.Embed(title=(command.qualified_name or command.name))
        e.add_field(name='Name', value=(command.qualified_name or command.name), inline=False)
        e.add_field(name='Signature', value=(self.signature(command)), inline=False)
        e.add_field(name='Help', value=(command.help or '[no help]'), inline=False)
        if len(command.aliases) != 0:
            e.add_field(name='Synonyms', value=('`' + "`, `".join(command.aliases) + '`' or '[no help]'), inline=False)
        await self.send_embed(e)


class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        help_command = BetterHelpCommand()
        help_command.cog = self
        self.bot.help_command = help_command


def setup(bot):
    bot.add_cog(HelpCog(bot))
