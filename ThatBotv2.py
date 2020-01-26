import discord
import bottyfuncs as bf
from discord.ext import commands
import Cogs

version = "0.3 'coggy'"
tokens = bf.yamler.yamlhandle()
bot = commands.Bot(command_prefix=tokens["prefix"])

bot.add_cog(Cogs.funstuffcog.FunStuff(bot))
bot.add_cog(Cogs.utilitiescog.Utilities(bot))


bot.add_cog(Cogs.listenercog.Listeners(bot))

bot.add_cog(Cogs.sudocog.Sudostuff(bot))

bot.run(tokens["discordtoken"])


"""
MIT License

Copyright (c) 2020 ThatRedKite

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
SOFTWARE."""