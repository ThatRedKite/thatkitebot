# ------------------------------------------------------------------------------
#  MIT License
#
#  Copyright (c) 2019-2021 ThatRedKite
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
#  documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
#  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
#  and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all copies or substantial portions of
#  the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
#  THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
#  TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
# ------------------------------------------------------------------------------

from discord.ext import commands
from wand.image import Image as WandImage
from wand.color import Color as WandColor
import discord
from io import BytesIO


def wavelength_to_rgb(wavelength, gamma=0.98):

    '''This converts a given wavelength of light to an
    approximate RGB color value. The wavelength must be given
    in nanometers in the range from 380 nm through 750 nm
    (789 THz through 400 THz).
    Based on code by Dan Bruton
    http://www.physics.sfasu.edu/astro/color/spectra.html
    '''

    wavelength = float(wavelength)
    if 380 <= wavelength <= 440:
        attenuation = 0.3 + 0.7 * (wavelength - 380) / (440 - 380)
        R = ((-(wavelength - 440) / (440 - 380)) * attenuation) ** gamma
        G = 0.0
        B = (1.0 * attenuation) ** gamma
        if 405 <= wavelength < 430:
            R = R * (wavelength / 310)
    elif 440 <= wavelength <= 490:
        R = 0.0
        G = ((wavelength - 440) / (490 - 440)) ** gamma
        B = 1.0
    elif 490 <= wavelength <= 510:
        R = 0.0
        G = 1.0
        B = (-(wavelength - 510) / (510 - 490)) ** gamma
    elif 510 <= wavelength <= 580:
        R = ((wavelength - 510) / (580 - 510)) ** gamma
        G = 1.0
        B = 0.0
    elif 580 <= wavelength <= 645:
        R = 1.0
        G = ((-(wavelength - 645) / (645 - 580)) ** gamma) * 0.9
        B = 0.0
    elif 645 <= wavelength <= 750:
        attenuation = 0.3 + 0.7 * (750 - wavelength) / (750 - 645)
        R = (1 * attenuation) ** gamma
        G = 0.0
        B = 0.0
    else:
        R = 0.0
        G = 0.0
        B = 0.0
    R *= 255
    G *= 255
    B *= 255
    return int(R), int(G), int(B)


class LaserCog(commands.Cog, name="Laser commands"):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.cooldown(5, 10, commands.BucketType.channel)
    @commands.command(aliases=["autism"])
    async def spectrum(self, ctx):
        embed = discord.Embed(title="Visible Light Spectrum")
        embed.set_image(url="https://cdn.discordapp.com/attachments/909159696798220400/912041066218283068/kitespectrum_t1.png")
        await ctx.send(embed=embed)

    @commands.cooldown(1, 10, commands.BucketType.channel)
    @commands.group()
    async def laser(self, ctx):
        if not ctx.subcommand_passed:
            await self.goggles(ctx)

    @laser.command(aliases=["glasses", "safety"])
    async def goggles(self, ctx):
        embed = discord.Embed(title="Lasers of all powers can pose a serious risk to your eyes.",
                              description="""5mW is the safety limit where your blink reflex should save you from any damage.
                               Anything above that can cause permanent eye damage faster than you can blink and the worse case, permanent blindness.""")
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/909159696798220400/912036244073115658/14429.png")
        embed.add_field(name="\nLaser safety equipment can be found here: ",
                        value="[Laserglow](https://www.laserglow.com/product/AGF-Laser-Safety-Goggles)\n"
                              "[Lasertack](https://lasertack.com/en/laser-safety-glasses)\n"
                              "[Thorlabs](https://www.thorlabs.com/newgrouppage9.cfm?objectgroup_id=762)",
                        inline=False)
        embed.add_field(name="\nOther trusted brands include",
                        value="Honeywell, Glendale, Sperian,"
                              "Newport/MKS, Thorlabs, Laservision/Uvex,"
                              "Laserglow, NoIR (LaserShield)",
                        inline=False)
        embed.add_field(name="\nAnything from Amazon, AliExpress, Wish is **__unsafe!__**",
                        value="If you wish to see for the rest of your life, **__do not use them!__**", inline=True)
        embed.add_field(name="\nWhat is OD?",
                        value="""OD stands for *Optical density*.
                        It’s the fraction of light (of a certain wavelength) that gets through the goggles,expressed in powers of 10.
                        OD1 means that *10%* of the light that hits the goggles gets through.
                        OD2 means *1%*,
                        OD3 is *0.1%*, and so on.""",
                        inline=False)
        embed.add_field(name="\nWhat is the wavelength or nm?",
                        value=f"""The wavelength in nanometers (nm) corresponds to the color.
                         If you are not sure the wavelength but you know the color,
                         you can ask someone, do `{self.bot.command_prefix}laser color (color)` or refer to `+spectrum`.""",
                        inline=True)
        embed.set_footer(text=f"For a more in depth explanation, use {self.bot.command_prefix}laser safety")
        await ctx.send(embed=embed)

    @laser.command()
    async def color(self, ctx, color: str):
        color = int(color.lower().replace("nm", ""))
        new_color = wavelength_to_rgb(color)
        with WandImage(width=256, height=256, background=WandColor(f"rgb{new_color}")) as colorimg:
            b = colorimg.make_blob(format="jpeg")
        file = discord.File(BytesIO(b), filename="color.jpeg")
        embed = discord.Embed(title=f"Approximated color for {color}nm")
        embed.set_image(url="attachment://color.png")
        embed.set_footer(text="this is not 100% accurate\n since your monitor,"
                              "eyes and other factors play a role\n but"
                              "it is as close as it can get")
        await ctx.send(file=file, embed=embed)


def setup(bot):
    bot.add_cog(LaserCog(bot))
