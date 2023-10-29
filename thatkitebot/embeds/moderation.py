from discord import Embed, Color, ClientException
from thatkitebot.base.util import EmbedColors as ec
from thatkitebot.base.util import link_from_ids


def gen_edit_warning(payload):
    warn_embed = Embed(
        title="Edit Warning",
        description=f"Message older than threshold has been edited: [Go to Message]({link_from_ids(payload.guild_id, payload.channel_id, payload.message_id)})",
        color=ec.traffic_red
    )

    # try to add a field with the new contents, don't if it fails
    try:
        warn_embed.add_field(name="New Message", value=f"""{payload.data['content']}""")
    except KeyError:
        pass
    except ClientException:
        pass

    return warn_embed