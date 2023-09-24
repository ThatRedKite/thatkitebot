#  Copyright (c) 2019-2023 ThatRedKite and contributors

from math import sin, atan
from io import BytesIO

import discord
import si_prefix
from discord.ext import commands
from wand.image import Image as WandImage
from wand.color import Color as WandColor

from thatkitebot.base import util
from thatkitebot.embeds.laser import gen_embed as safety_embed
from thatkitebot.calculators.electronics.exceptions import TooFewArgsError


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


def calculate_diffraction(p):
    if "lmm" in p:
        lmm = si_prefix.si_parse(p["lmm"])
    else:
        raise TooFewArgsError()
    if "l" in p:
        l = si_prefix.si_parse(p["l"])
    else:
        raise TooFewArgsError()
    if "d" in p:
        d = si_prefix.si_parse(p["d"])
    else:
        raise TooFewArgsError()
    res = 1 / lmm / 1000 * sin((atan(d / (2 * l))))
    return dict(res=si_prefix.si_format(res), Lmm=lmm, L=si_prefix.si_format(l), D=si_prefix.si_format(d))


class LaserCog(commands.Cog, name="Laser commands"):
    """
    Laser calculations and safety advice.
    """
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.cooldown(5, 10, commands.BucketType.channel)
    @commands.command(aliases=["autism"])
    async def spectrum(self, ctx):
        """
        Returns a picture of visible light spectrum.
        """
        embed = discord.Embed(title="Visible Light Spectrum")
        embed.set_image(
            url="https://media.discordapp.net/attachments/910895468001767484/913348594269036584/unknown.png")
        await ctx.send(embed=embed)

    @commands.cooldown(1, 5, commands.BucketType.channel)
    @commands.group()
    async def laser(self, ctx):
        """
        General command for laser related things.
        """
        if not ctx.subcommand_passed:
            await self.goggles(ctx)

    @laser.command(aliases=["glasses", "safety", "help"])
    async def goggles(self, ctx):
        """
        Returns laser safety information.
        """
        await ctx.send(embed=safety_embed(self))

    @laser.command()
    async def color(self, ctx, color: str):
        """
        Returns an approximation of light color given a wavelength.
        """
        color = int(color.lower().replace("nm", ""))
        new_color = wavelength_to_rgb(color)
        with WandImage(width=256, height=256, background=WandColor(f"rgb{new_color}")) as colorimg:
            b = colorimg.make_blob(format="jpeg")
        file = discord.File(BytesIO(b), filename="color.jpeg")

        embed = discord.Embed(title=f"Approximated color for {color}nm")

        embed.set_image(url="attachment://color.jpeg")

        embed.set_footer(
            text=("This is not 100% accurate since your monitor and\neyes play a role but this is as close as it can get.\n"
                  "If the color is black, it is considered invisible."
                  )
        )

        await ctx.send(file=file, embed=embed)

    @laser.command(aliases=["diff"])
    async def diffraction(self, ctx, *, args=None):
        """
        Calculates the wavelength of a laser using a diffraction grating. Run command for more information.
        """
        if not args:
            embed = discord.Embed(
                title="Diffraction Grating Equation",
                description="This is to calculate the wavelength of a laser using a diffraction grating"
            )

            embed.set_image(
                url="https://cdn.discordapp.com/attachments/909159696798220400/912064371205738566/kitething5fff.png"
            )

            embed.add_field(
                name="Measurements and information you need",
                value=("The diffraction grating's slits per mm (L/mm)\n"
                       "Distance from the diffraction grating to a wall (L) \n Distance between split beams (D) "
                       ),
                inline=False
            )

            embed.add_field(
                name="Use the bot for calculations.",
                value=f"You can use this command to do the calculation, for example: `{self.bot.command_prefix}laser diffraction lmm=1000 L=6.78 D=11.6`"
            )

            embed.set_footer(text="This command accepts SI prefixes.")
            await ctx.send(embed=embed)
        else:
            try:
                p = util.Parsing.parse_arguments_input(args)
                p = {k.lower(): v for k, v in p.items()}
                res = calculate_diffraction(p)
                embed = discord.Embed(title="Diffraction Grating Equation")
                embed.set_image(
                    url="https://cdn.discordapp.com/attachments/909159696798220400/912064371205738566/kitething5fff.png")
                embed.add_field(name="Values:", value=f"L/mm = {res['Lmm']}\nL = {res['L']}m\nD = {res['D']}m")
                embed.add_field(name="Wavelength value:", value="{}m".format(str(res["res"])))
                await ctx.send(embed=embed)
            except TooFewArgsError:
                await util.errormsg(ctx, "Not enough arguments to compute anything.")
                return


def setup(bot):
    bot.add_cog(LaserCog(bot))
