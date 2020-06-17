import discord


async def errormsg(ctx, msg:str):
            embed = discord.Embed(title="ERROR!", description=msg)
            embed.color = 0xC1121C # set the color to "traffic red"
            with ctx.channel.typing():
                await ctx.send(embed=embed)

def typeguesser(setting, value):
    setting = str(setting).lower()
    value = str(value).lower()

    if len(setting) > 0:
        first = setting[0]
    
    if first == "i":
        return int(value)

    elif first == "s":
        return str(value)

    elif first == "f":
        return float(value)
    
    elif first == "b":
        if value in ('yes', 'y', 'true', 't', '1', 'enable', 'on'):
            return True
        elif value in ('no', 'n', 'false', 'f', '0', 'disable', 'off'):
            return False