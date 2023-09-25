import discord
import asyncio
import subprocess
from discord.ext import commands


async def units_converter(expression: str, target_unit: str = "") -> (float, str):
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
    
    # Parse the output to get the numerical value and unit.
    # We expect output in the format: "value unit"
    parts = stdout.decode().strip().split()
    
    # Extract the numerical value and unit
    value = float(parts[0])
    unit = " ".join(parts[1:])

    if target_unit:
        unit = target_unit
    
    return value, unit

class UnitsCommands(commands.Cog, name="Units Commands"):
    """
    This cog exposes the units utility as a set of commands.
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


    # TODO fix stuff like "feet" -> "m"
    # convert m/s² to m/s^2 and so on
    # add message tokenizer and auto converter
    # get formula for converting units
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

        # Run the units command asynchronously
        value, unit = await units_converter(expression, target_unit)
        
        # Construct the response
        response = f"**{expression}** = **{value} {unit}**"
        
        # Send the response
        await ctx.followup.send(response)



def setup(bot):
    bot.add_cog(UnitsCommands(bot))