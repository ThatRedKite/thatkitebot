import discord

async def errormsg(ctx, msg:str):
            embed=discord.Embed(title="ERROR!", description=msg)
            embed.color=0xC1121C # set the color to "traffic red"
            with ctx.channel.typing():
                await ctx.send(embed=embed)
