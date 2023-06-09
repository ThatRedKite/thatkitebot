#  Copyright (c) 2019-2023 ThatRedKite and contributors

from datetime import datetime

from discord import Embed

from thatkitebot.base.util import EmbedColors as ec


def gen_embed(self) -> Embed:
    embed = Embed(
        color=ec.purple_violet,
        title="ThatKiteBot Privacy Policy",
        description="ThatKiteBot is run by ThatRedKite#4842. This privacy policy will explain how this bot uses the personal data collected from you when you use it."
    )

    embed.add_field(
        name="What data does the bot collect?",
        value="The bot collects the following data:\n"
              "- Your Discord ID\n"
              "- Your Discord username\n"
              "- Your Discord avatar\n"
              "- Reactions you add to messages\n"
              "- Messages sent by you\n"
              "- Any other data you provide the bot with while using it's commands"
    )

    embed.add_field(
        name="How is the data collected?",
        value="The bot collects the data it needs to function. It does this only by using the Discord API.\n"
              "You directly provide the bot with most of the data we collect. The bot collects and processes the data when you:\n"
              "- Send a messages\n"
              "- Use a command\n"
              "- Use a reaction\n"
    )

    embed.add_field(
        name="How will your data be used?",
        value="The bot collects so that it can:\n"
              "- Process your commands\n"
              "- Provide Markov functionality\n"
              "- Understand the context of commands\n"
              "The data is not transferred to any third parties."
    )

    embed.add_field(
        name="How is your data stored?",
        value="The bot securely stores the data on a server in Nuremberg (Germany).\n"
              "- All message data is stored in RAM.\n"
              "- All message data is automatically deleted, when it is not needed anymore.\n"
              "- The RAM data is wiped whenever the bot is rebooted.\n"
              "- The only data that is permanently stored are Discord IDs, which are required for certain settings.\n"
    )

    embed.add_field(
        name="What are your data protection rights?",
        value="We would like to make sure you are fully aware of all of your data protection rights. Every user is entitled to the following:\n"
              "If you make a request, we have one month to respond to you. If you would like to exercise any of these rights, please contact ThatRedKite#4842 on Discord.\n"
    )

    embed.add_field(
        name="Your rights listed below:",
        inline=False,
        value="The right to *access* – You have the right to request us for copies of your personal data. We may charge you a small fee for this service.\n"
              "The right to *rectification* – You have the right to request that we correct any information you believe is inaccurate. You also have the right to request us to complete the information you believe is incomplete.\n"
              "The right to *erasure* – You have the right to request that we erase your personal data, under certain conditions.\n"
              "The right to *restrict processing* – You have the right to request that we restrict the processing of your personal data, under certain conditions.\n"
              "The right to *object to processing* – You have the right to object to our processing of your personal data, under certain conditions.\n"
              "The right to *data portability* – You have the right to request that we transfer the data that we have collected to another organization, or directly to you, under certain conditions.\n"
    )

    embed.set_thumbnail(url=str(self.bot.user.avatar.url))
    embed.set_footer(text=f"{self.bot.user.name} v{self.bot.version} this policy was last updated: ")
    embed.timestamp = datetime(2023, 1, 22, 12, 22, 0, 0)
    return embed
