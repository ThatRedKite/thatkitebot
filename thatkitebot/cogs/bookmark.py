#  Copyright (c) 2019-2023 ThatRedKite and contributors

import discord
from discord.ext import commands, pages
from redis import asyncio as aioredis

from thatkitebot.base.util import list_chunker, link_from_ids
from thatkitebot.base.exceptions import NoBookmarksException


async def get_bookmarks(redis: aioredis.Redis, user: discord.User):
    # assemble the key for accessing the hash
    hash_key = f"bookmarks:{user.id}"

    # check if the user actually has any bookmarks
    if not await redis.exists(hash_key):
        raise NoBookmarksException

    # the hash might actually exist without any entries (for example if the user deleted all entries manually)
    # in that case we also have to return too
    if await redis.hlen(hash_key) == 0:
        raise NoBookmarksException

    # now we simply iterate through all the keys in the hash
    async for bookmark in redis.hscan_iter(hash_key, "*"):
        yield bookmark


class BookmarkModal(discord.ui.Modal):
    def __init__(self, redis: aioredis.Redis, message: discord.Message, ctx: discord.ApplicationContext, *args, **kwargs):
        self.redis = redis
        self.message = message
        self.ctx = ctx
        # python class black magic
        super().__init__(*args, **kwargs)
        # add the Comment text box
        self.add_item(discord.ui.InputText(
            label="Add a Comment for the bookmark",
            style=discord.InputTextStyle.singleline,
            max_length=50
        ))

    async def callback(self, interaction: discord.Interaction):
        hash_key = f"bookmarks:{self.ctx.interaction.user.id}"
        entry_key = f"{self.ctx.interaction.guild_id}:{self.ctx.interaction.channel_id}:{self.message.id}"
        comment = self.children[0].value.lstrip().rstrip()
        await self.redis.hset(hash_key, entry_key, comment)

        # await add_bookmark(self.redis, interaction, self.message, )
        await interaction.response.send_message("I added the message to your bookmarks", ephemeral=True)


class ConfirmDeleteModal(discord.ui.Modal):
    def __init__(self, redis: aioredis.Redis, *args, **kwargs):
        self.redis = redis
        super().__init__(*args, **kwargs)
        self.add_item(discord.ui.InputText(
            label="THIS ACTION CANNOT BE UNDONE!️",
            style=discord.InputTextStyle.singleline,
            placeholder="Press the button below, to proceed.",
            max_length=0,
            required=False
        ))

    async def callback(self, interaction: discord.Interaction):
        hash_key = f"bookmarks:{interaction.user.id}"
        await self.redis.delete(hash_key)
        await interaction.response.send_message("Your bookmarks have been cleared", ephemeral=True)


class DeletionSelectView(discord.ui.View):
    def __init__(self, redis: aioredis.Redis, keys: list, comments: list, ctx, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.redis = redis
        self.keys = keys
        self.comments = comments
        self.ctx = ctx

        self.select = discord.ui.Select(
            min_values=1,
            max_values=1,
            options=[discord.SelectOption(label=comment) for comment in comments],
            placeholder="The bookmark you want to delete",
        )

        self.select.callback = self.select_callback

        self.add_item(self.select)

    async def select_callback(self, interaction: discord.Interaction):
        selected = self.select.values[0]
        index = self.comments.index(selected)
        key = self.keys[index]
        hash_key = f"bookmarks:{interaction.user.id}"
        await self.redis.hdel(hash_key, key)
        await interaction.response.send_message("Successfully deleted the bookmark", ephemeral=True)


class BookmarkCog(commands.Cog, name="Bookmarks"):
    def __init__(self, bot):
        self.bot = bot
        self.redis: aioredis.Redis = bot.redis_bookmarks

    bm = discord.SlashCommandGroup("bookmarks", "Bookmarks")

    @discord.message_command(name="Bookmark Message", description="Description")
    async def _add(self, ctx: discord.ApplicationContext, msg: discord.Message):
        """Bookmarks a message for you."""
        modal = BookmarkModal(self.redis, msg, ctx, title="Bookmark Comment")
        await ctx.send_modal(modal)

    @bm.command(name="clear", description="Deletes all bookmarks")
    async def _clear(self, ctx: discord):
        modal = ConfirmDeleteModal(self.redis, title="Do you really want to delete all bookmarks?")
        await ctx.send_modal(modal)

    @bm.command(name="list", description="Description")
    async def _list(self, ctx: discord.ApplicationContext):
        # initialize two empty lists for fields and the pages
        fields = []
        page_list = []
        try:
            async for ids, comment in get_bookmarks(self.redis, ctx.user):
                # split the key into the IDs required to assemble the reference link
                id_list = ids.split(":")

                # assemble the link from the IDs
                link = link_from_ids(guild_id=id_list[0], channel_id=id_list[1], message_id=id_list[2])

                # add a field containing the note and the link to the embed
                fields.append((f"'{comment}'", f"[link]({link})"))

        except NoBookmarksException:
            # stop with a message if the user has no bookmarks
            return await ctx.response.send_message("You don't have any bookmarks!", ephemeral=True)

        # split the list of fields into lists with a max size of 5
        for fields in list_chunker(fields, 5):
            # generate an embed
            embed = discord.Embed(title="Your bookmarks", description="** **")

            # add the fields to the embed
            for name, value in fields:
                embed.add_field(name=name, value=value, inline=False)

            # turn the Embed into a Page and add it to the page list
            page_list.append(pages.Page(embeds=[embed]))

        # initialize the Paginator with the pages
        paginator = pages.Paginator(pages=page_list, loop_pages=True)

        # start the paginator thing
        await paginator.respond(ctx.interaction, ephemeral=True)

    @bm.command(name="delete", description="Deletes a bookmark")
    async def _delete(self, ctx):
        await ctx.defer()
        try:
            # initialize two empty lists intended to store the comments and the keys
            comments = []
            keys = []

            async for key, comment in get_bookmarks(self.redis, ctx.user):
                keys.append(key)
                comments.append(comment)

        except NoBookmarksException:
            return await ctx.followup.send("You don't have any bookmarks!", ephemeral=True)

        await ctx.followup.send("Pick the bookmark you want to delete:", view=DeletionSelectView(
            self.redis,
            keys,
            comments,
            ctx
        ), ephemeral=True)


def setup(bot):
    bot.add_cog(BookmarkCog(bot))
