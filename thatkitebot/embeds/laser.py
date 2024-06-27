#region License
"""
MIT License

Copyright (c) 2019-present The Kitebot Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
#endregion

from discord import Embed

#region main code
def gen_embed(self):
    embed = Embed(
        title="Lasers of all powers can pose a serious risk to your eyes.",
        description=(
            "5mW is the safety limit where your blink reflex *should* save you from any lasting damage.\n"
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
#endregion