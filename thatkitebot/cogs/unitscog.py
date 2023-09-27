#  Copyright (c) 2023 diminDDL, ThatRedKite and contributors

import discord
import asyncio
import subprocess
import re
from discord.ext import commands

from thatkitebot.embeds.units import gen_embed

async def unicode_to_ascii_exponents(expression: str) -> str:
    """Convert unicode exponents to ASCII exponents."""
    unicode_to_ascii = {
        '⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4',
        '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9'
    }

    # return if the input expression is empty
    if not expression:
        return expression
    
    ascii_expressions = []
    i = 0
    while i < len(expression):
        char = expression[i]
        if char in unicode_to_ascii:
            ascii_expressions.append('^')
            ascii_expressions.append(unicode_to_ascii[char])
        elif char == '⁻':  # if the character is a unicode minus sign for negative exponents
            ascii_expressions.append('^')
            ascii_expressions.append('-')
            i += 1  # increment index to skip next character which should be the unicode exponent
            ascii_expressions.append(unicode_to_ascii.get(expression[i], expression[i]))  # append the exponent
        else:
            ascii_expressions.append(char)
        i += 1
    
    return ''.join(ascii_expressions)

async def units_expander(expression: str) -> str:
    """
    Used in order to turn user friendly units into units that units can understand.
    For example '3 m/s' will be turned into '3 meters/second'
    Degrees are also supported, so '3°' will be turned into '3 degrees'
    """
    lookup_table = {
        'm': 'meters',
        's': 'seconds',
        '°': 'degrees',
        'kg': 'kilograms',
        # add more units here
    }

    # Regex pattern to match a unit abbreviation bounded by word boundaries,
    # to prevent partial matches inside other words.
    unit_pattern = re.compile(r'\b(' + '|'.join(re.escape(key) for key in lookup_table.keys()) + r')\b')

    def unit_replacer(match):
        return lookup_table[match.group(0)]

    # Function to process text outside of square brackets
    def expand_units(text):
        return unit_pattern.sub(unit_replacer, text)

    # Regex pattern to match text inside square brackets
    bracket_pattern = re.compile(r'\[([^]]+)\]')

    # Function to process text inside square brackets
    def bracket_replacer(match):
        # Just remove the brackets, keep the text inside unchanged
        return match.group(1)

    # First, handle text inside square brackets
    expression = bracket_pattern.sub(bracket_replacer, expression)

    # Then, expand units in the rest of the text
    expanded_expression = expand_units(expression)
    return expanded_expression

async def units_expander(expression: str) -> str:
    """
    Used in orer to turn user firendly units into units that units can understand.
    For example '3 m/s' will be turned into '3 meters/second'
    Degrees are also supported, so '3°' will be turned into '3 degrees'
    """
    # TODO
    return expression

async def units_converter(expression: str, target_unit: str = "") -> (float, str, str):
    """Asynchronous wrapper for the units command."""
    
    # Construct the command to be executed.
    cmd = ["units", "-t", expression]
    
    if target_unit:
        cmd.append(target_unit)

    # Run the command asynchronously and capture the output.
    proc = await asyncio.create_subprocess_exec(*cmd,
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE)
    
    stdout, stderr = await proc.communicate()
    
    # Check for errors
    if proc.returncode != 0:
        raise ValueError(f"Error executing units: {stderr.decode().strip()}")
    
    output = stdout.decode().strip()

    # Check if a definition is being returned
    if "=" in output:
        # Return the unit definition as the third element in the tuple
        return None, None, output

    # Parse the output to get the numerical value and unit.
    # We expect output in the format: "value unit"
    parts = output.split()
    
    # Extract the numerical value and unit
    value = float(parts[0])
    unit = " ".join(parts[1:])
    
    if target_unit:
        return value, target_unit, None

    return value, unit, None

class UnitsCommands(commands.Cog, name="Units Commands"):
    """
    This cog exposes the units utility as a set of commands.
    You can input an entire expession full expression with units, like `c/2.4Ghz` will return `0.12491352 m`, or you can input a single unit, like "feet" and it will return the definition of that unit.
    You can use the target_unit parameter to convert the expression to a specific unit.
    SI prefixes are supported, so you can use "k" for kilo, "m" for milli, etc.
    *This is a slightly modified version of the units syntax, for example we convert C and F into Celsius and Fahrenheit respectively. If you want to use the original units syntax, put your expression or unit in square brackets: `3[C]` will be interpreted as `3 Columbs`.*
    """

    def __init__(self, bot):
        self.bot: commands.Bot = bot
    
    units_commands = discord.SlashCommandGroup(
        "units",
        "Units Commands"
    )

    #
    # --- Basic evaluation Commands ---
    #


    # TODO
    # convert m/s² to m/s^2 and so on
    # add message tokenizer and auto converter
    # get formula for converting units... likely can't be easily done though units
    @units_commands.command(name="evaluate", description="Evaluate a units expression")
    async def evaluate(self, 
            ctx: discord.ApplicationContext, 
            expression: discord.Option(
                str,
                description="The units expression to evaluate.",
                required=True
            ), 
            target_unit: discord.Option(
                str,
                description="The target unit to convert to (optional).",
                required=False
            )
    ):
        """Evaluate a units expression."""
        
        await ctx.defer()

        print("got:")
        print(expression)
        print(target_unit)

        ascii_expression = await unicode_to_ascii_exponents(expression)
        ascii_target_unit = await unicode_to_ascii_exponents(target_unit)

        print("converted:")
        print(ascii_expression)
        print(ascii_target_unit)

        value, unit, unit_def = await units_converter(expression, target_unit)

        embed = await gen_embed(expression, value, unit, unit_def)

        # Send the response
        await ctx.followup.send(embed=embed)



def setup(bot):
    bot.add_cog(UnitsCommands(bot))