#  Copyright (c) 2019-2023 ThatRedKite and contributors

from discord import Embed, Color

# prepares embed by given section id
async def get_embed(id: int, config_file):
    section_config = config_file[id] 

    embed = Embed(title = f'{section_config["title"]} {section_config["emoji"]}', color = Color(int(section_config["color"])))

    for field in section_config["fields"]:
        embed.add_field(
            name=field["name"], 
            value=field["value"],
            inline=field["inline"]
        )

    if section_config["footer"] != "false":
        embed.set_footer(text=section_config["footer"])

    return embed