#  Copyright (c) 2023 diminDDL, ThatRedKite and contributors

import discord
import asyncio
import subprocess
import re
from thatkitebot.embeds.units import gen_embed, gen_error_embed, gen_help_embed
from discord.ext import commands


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
    # if the expression is empty, return it
    if not expression:
        return expression

    lookup_table = {
        'h': 'hour',
        '°': 'degree',

        # likely redundant
        #'kg': 'kilogram',
        #'m': 'meters',
        #'s': 'seconds',
    }

    # Regex pattern to match a unit abbreviation bounded by word boundaries,
    # to prevent partial matches inside other words.
    unit_pattern = re.compile(r'\b(' + '|'.join(re.escape(key) for key in lookup_table.keys()) + r')\b')

    def unit_replacer(match):
        return lookup_table[match.group(0)]

    def expand_units(text):
        return unit_pattern.sub(unit_replacer, text)

    # Use findall to split the string into segments inside and outside square brackets
    segments = re.findall(r'(\[[^\]]+\])|([^\[\]]+)', expression)

    processed_segments = []
    for segment in segments:
        # For each segment, check if it starts with '[' (indicating it was inside square brackets)
        if segment[0] and segment[0].startswith('['):
            # If inside square brackets, just remove the brackets
            processed_segments.append(segment[0][1:-1])
        else:
            # Otherwise, expand the units
            processed_segments.append(expand_units(segment[1]))

    expanded_expression = ''.join(processed_segments)
    return expanded_expression

async def units_converter(expression: str, target_unit: str = "") -> (float, str, str, str):
    """Asynchronous wrapper for the units command."""
    
    # Construct the command to be executed.
    cmd = ["units", "-t", expression]
    
    if target_unit:
        cmd.append(target_unit)

    #print("running command:")
    #print(cmd)

    # Run the command asynchronously and capture the output.
    proc = await asyncio.create_subprocess_exec(*cmd,
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE)
    
    stdout, stderr = await proc.communicate()
    
    #print("got stdout:")
    #print(stdout)
    #print("got stderr:")
    #print(stderr)

    # Check for errors
    if len(stderr) != 0 or "error" in stdout.decode().strip().lower():
        #print("got error")
        return None, None, None, stdout.decode().strip()
    
    # Check for unknown units
    if "unknown" in stdout.decode().strip().lower():
        #print("got unknown")
        return None, None, None, stdout.decode().strip()
    
    output = stdout.decode().strip()

    # Check if a definition is being returned
    if "=" in output:
        # Return the unit definition as the third element in the tuple
        return None, None, output, None

    # Parse the output to get the numerical value and unit.
    # We expect output in the format: "value unit"
    parts = output.split()
    
    # Extract the numerical value and unit
    value = float(parts[0])
    unit = " ".join(parts[1:])
    
    if target_unit:
        return value, target_unit, None, None

    return value, unit, None, None

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

    @units_commands.command(name="help", description="Explain the units command")
    async def help(self,
            ctx: discord.ApplicationContext):
        """Explain the units command."""
        await ctx.defer()

        await ctx.followup.send(embed=await gen_help_embed())   

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

        #print("got:")
        #print(expression)
        #print(target_unit)

        ascii_expression = await unicode_to_ascii_exponents(expression)
        ascii_target_unit = await unicode_to_ascii_exponents(target_unit)

        #print("converted:")
        #print(ascii_expression)
        #print(ascii_target_unit)

        ascii_expression = await units_expander(ascii_expression)
        ascii_target_unit = await units_expander(ascii_target_unit)

        #print("expanded:")
        #print(ascii_expression)
        #print(ascii_target_unit)


        value, unit, unit_def, err = await units_converter(ascii_expression, ascii_target_unit)

        #print("post converted:")
        #print(value)
        #print(unit)
        #print(unit_def)
        #print(err)
        
        if err:
            embed = await gen_error_embed(ascii_expression, err)
        else:
            embed = await gen_embed(ascii_expression, value, unit, unit_def)

        # Send the response
        await ctx.followup.send(embed=embed)



def setup(bot):
    bot.add_cog(UnitsCommands(bot))