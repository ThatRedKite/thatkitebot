#  Copyright (c) 2023 diminDDL, ThatRedKite and contributors

from discord import Embed
from thatkitebot.base.util import EmbedColors

async def gen_help_embed() -> Embed:
    embed = Embed(title="Units help")
    embed.color = EmbedColors.unique_blue
    embed.add_field(name="Description: ", value=(
        "* Units is a program that converts between different units of measurement and evacuates expressions with them.\n"
        "* This instance has a modified syntax and replaces common units with the correct expressions.\n"
        "* For example `km/h` will become `km/hour` because units treats `h` as the Plank constant.\n"
        "* More information can be found [here](https://linux.die.net/man/1/units).\n"
        "* If you want to use the original syntax without the replacements, simply put either individual variables or the entire expression into square brackets,\n example: `5 [h] * 3m/s`"), inline=False)
    embed.add_field(name="Syntax: ", value="```/units [expression] [target unit (optional)]```", inline=False)
    embed.add_field(name="Example: ", value="```/units '1 meter' 'feet'```", inline=False)
    return embed



async def gen_embed(expression: str, value: float, unit: str, unit_def: str) -> Embed:
    embed = Embed(title="Units result",
                  description="**Click [here](https://linux.die.net/man/1/units) to learn more**")

    embed.color = EmbedColors.unique_blue

    if unit_def:
        embed.add_field(name="Definition: ", value=f"```{' '.join(unit_def.split())}```", inline=False)
    else:
        embed.add_field(name="Expression: ", value=f"```{' '.join(expression.split())}```", inline=False)
        embed.add_field(name="Result: ", value=f"```{value} {' '.join(unit.split())}```", inline=False)

    embed.set_footer(text="Use square brackets to use original units syntax.\nExample: 'h' = 'hour', but '[h]' = 'h'.")

    return embed


async def gen_error_embed(expression: str, error_str: str) -> Embed:
    embed = Embed(title="Error")

    embed.color = EmbedColors.traffic_red

    embed.add_field(name="Expression: ", value=f"```{' '.join(expression.split())}```", inline=False)
    embed.add_field(name="Error: ", value=f"```{error_str}```", inline=False)

    embed.set_footer(text="Check your expression, and try again.\nUse help command for more info.")

    return embed
    