import discord


def gen_embed(self):
    embed = discord.Embed(
        title="Lasers of all powers can pose a serious risk to your eyes.",
        description=("5mW is the safety limit where your blink reflex should save you from any damage.\n"
                     "Anything above that can cause **permanent eye damage** faster than you can blink or in the worst case: **permanent blindness**."
                     )
        )

    embed.set_thumbnail(
        url="https://cdn.discordapp.com/attachments/909159696798220400/912036244073115658/14429.png")

    embed.add_field(
        name="\nLaser safety equipment can be found here: ",
        value=("[Laserglow](https://www.laserglow.com/product/AGF-Laser-Safety-Goggles)\n"
               "[Kentek](https://www.kenteklaserstore.com/products/eyewear/laser-safety-eyewear)\n"
               "[Lasertack](https://lasertack.com/en/laser-safety-glasses)\n"
               "[Thorlabs](https://www.thorlabs.com/newgrouppage9.cfm?objectgroup_id=762)"),
        inline=False
    )

    embed.add_field(
        name="\nOther trustworthy brands include:",
        value=("Honeywell, Glendale, Sperian,\n"
               "Newport/MKS, Edmund Optics, Laservision/Uvex,\n"
               "Laserglow, NoIR (LaserShield)\n"
               "\nFeel free to ask if a brand not listed is trustworthy."),
        inline=False
    )

    embed.add_field(
        name="\n*Anything* from Amazon, AliExpress, Wish is **__unsafe!__**",
        value="If you wish to see for the rest of your life, **__do not use them!__**",
        inline=True
    )

    embed.add_field(
        name="\nWhat is OD?",
        value=("OD stands for *Optical density*. It’s the fraction of light (of a certain wavelength) that gets through the goggles,expressed in powers of 10.\n"
               "OD1 means that *10%* of the light that hits the goggles gets through.\n"
               "OD2 means *1%*,\n"
               "OD3 is *0.1%*, and so on."),
        inline=False
    )

    embed.add_field(
        name="\nWhat is the wavelength or nm?",
        value=(f"The wavelength in nanometers (nm) corresponds to the color.\n"
               f"If you are not sure the wavelength but you know the color,\n"
               f"you can ask someone, do `{self.bot.command_prefix}laser color (color)` or refer to `+spectrum`."),
        inline=True
    )
    return embed
