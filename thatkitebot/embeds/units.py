#  Copyright (c) 2023 diminDDL, ThatRedKite and contributors

from discord import Embed


async def gen_embed(expression :str, value: float, unit :str, unit_def :str) -> Embed:
    embed = Embed(title="Units result",
                          description="**Click [here](https://linux.die.net/man/1/units) to learn more**")

    if unit_def:
        embed.add_field(name="Definition: ", value=f"```{' '.join(unit_def.split())}```", inline=False)
    else:
        embed.add_field(name="Expression: ", value=f"```{' '.join(expression.split())}```", inline=False)
        embed.add_field(name="Result: ", value=f"```{value} {' '.join(unit.split())}```", inline=False)

    return embed
