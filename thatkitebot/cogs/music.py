#  Copyright (c) 2019-2023 ThatRedKite and contributors

import re
from datetime import timedelta

import discord
import wavelink

from discord.ext import commands

import thatkitebot
from thatkitebot.tkb_redis.settings import RedisFlags
from thatkitebot.tkb_redis.queue import RedisQueue


# an interaction class for selecting the song to play with selection buttons
class SongSelect(discord.ui.View):
    def __init__(self, ctx, songlist: list[wavelink.Track], player: wavelink.Player, enqueue: bool = True):
        super().__init__(timeout=30.0)
        self.ctx = ctx
        self.songlist = songlist
        self.player = player
        self.enqueue = enqueue
        self.redisqueue = RedisQueue(ctx.bot.redis_queue, str(ctx.guild.id), expire_after=timedelta(hours=2))

    async def play_song(self, interaction, tracklist: list[wavelink.Track], track_index: int = 0):
        if self.enqueue and self.redisqueue is not None:
            if not self.player.is_playing():
                # ignore the queue if the player is not playing anything
                print(tracklist)
                await self.player.play(tracklist[track_index], pause=False)
            else:
                data = f"{tracklist[track_index].uri}|{interaction.user.id}"
                await self.redisqueue.push(data)
                await interaction.message.edit(view=None, embeds=[], content=f"Added `{tracklist[track_index].title}` to the queue.")
        else:
            await self.player.play(tracklist[track_index])
            await interaction.message.edit(view=None, embeds=[], content=f"Playing `{self.songlist[track_index + 1].title}`")

    # check if the person interacting with the buttons is the same person who started the command
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user == self.ctx.author

    @discord.ui.button(label="1", style=discord.ButtonStyle.blurple)
    async def button1(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.play_song(interaction, self.songlist, 0)

    @discord.ui.button(label="2", style=discord.ButtonStyle.blurple)
    async def button2(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.play_song(interaction, self.songlist, 1)

    @discord.ui.button(label="3", style=discord.ButtonStyle.blurple)
    async def button3(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.play_song(interaction, self.songlist, 2)

    @discord.ui.button(label="4", style=discord.ButtonStyle.blurple)
    async def button4(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.play_song(interaction, self.songlist, 3)

    @discord.ui.button(label="5", style=discord.ButtonStyle.blurple)
    async def button5(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.play_song(interaction, self.songlist, 4)

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.red)
    async def stop(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.message.delete()


class MusicCog(commands.Cog, name="Music"):
    def __init__(self, bot):
        self.bot: thatkitebot.ThatKiteBot = bot
        self.settings_redis = self.bot.redis

    music = discord.SlashCommandGroup("music", "Music commands")

    async def cog_check(self, ctx):
        return await RedisFlags.get_guild_flag(self.settings_redis, ctx.guild.id, RedisFlags.MUSIC)

    # static method for getting the right voice channel
    @staticmethod
    async def get_voice_channel(ctx: discord.ApplicationContext, check_for_bot: bool = False):
        # check if voice commands are even enabled in the guild
        a = await RedisFlags.get_guild_flag(ctx.bot.redis, ctx.guild.id, RedisFlags.MUSIC)
        if not a:
            await ctx.interaction.followup.send("Music commands are disabled in this server.", ephemeral=True)
            return None, None

        if ctx.author.voice is None:
            await ctx.interaction.followup.send("You are not in a voice channel")
            return None, None

        user_voice_channel = ctx.author.voice.channel
        my_voice_channel = ctx.guild.me.voice.channel if ctx.guild.me.voice is not None else None
        # check if the bot is connected to a voice channel
        if check_for_bot and not my_voice_channel:
            # connect to the user's voice channel
            await user_voice_channel.connect(cls=wavelink.Player)
            return user_voice_channel, my_voice_channel

        if not check_for_bot and not my_voice_channel and my_voice_channel:
            return user_voice_channel, None

        if not check_for_bot and my_voice_channel is user_voice_channel:
            await ctx.interaction.followup.send("I'm already in your voice channel.")
            return None, None

        # check if the user is connected to the same voice channel as the bot
        if check_for_bot and user_voice_channel is not my_voice_channel:
            await ctx.interaction.followup.send("You are not connected to the same voice channel as me.")
            return None, None

        return my_voice_channel, user_voice_channel

    @music.command(name="connect", description="Connects the bot to a voice channel")
    async def _connect(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        # get the voice channel the user is connected to
        bot_voice_channel, user_voice_channel = await self.get_voice_channel(ctx)
        if not any((bot_voice_channel, user_voice_channel)):
            return

        # check if the bot has the necessary permissions to even join the channel
        if not user_voice_channel.permissions_for(ctx.guild.me).connect:
            await ctx.respond("I don't have the permissions to join that voice channel.")
            return

        """
        # check if the bot is already connected to the channel
        if voice_channel is ctx.guild.me.voice.channel:
            await ctx.respond(f"I'm already connected to {ctx.guild.me.voice.channel.mention}!")
            return
        # check if the user is trying to get the bot to join a different channel, return if so
        """
        if bot_voice_channel and ctx.guild.me.voice.channel is not user_voice_channel:
            await ctx.respond(f"I'm already connected to {ctx.guild.me.voice.channel.mention}! Please disconnect me from there first.")
            return

        # tconnect to the voice channel with wavelink
        await user_voice_channel.connect(cls=wavelink.Player)
        await ctx.interaction.followup.send(f"Connected to {user_voice_channel.mention}!")
        # if the bot is in debug mode, print a message to the console
        if self.bot.debug_mode:
            print(f"Connected to {user_voice_channel.name} in {ctx.guild.name}")

    @music.command(name="disconnect", description="Disconnects the bot from a voice channel")
    async def _music_disconnect(self, ctx: discord.ApplicationContext):
        # check if the bot is connected to a voice channel
        await ctx.defer()
        bot_voice_channel, _ = await self.get_voice_channel(ctx, check_for_bot=True)
        if not bot_voice_channel:
            return
        else:
            # get voice connection and disconnect
            await ctx.voice_client.disconnect(force=True)
            await ctx.interaction.followup.send(f"Disconnected from {bot_voice_channel.mention}!")
        # if the bot is in debug mode, print a message to the console
        if self.bot.debug_mode:
            print(f"Disconnected from {bot_voice_channel} in {ctx.guild.name}")

    @music.command(name="play", description="Plays a song from YouTube. Accepts a YouTube URL or a search query.")
    async def _play(
            self,
            ctx: discord.ApplicationContext,
            query: discord.Option(str, "The song to play. Can be a YouTube URL or a search query.", required=True),
            enqueue: discord.Option(bool, "Whether to enqueue the song or play it immediately.", required=False) = True
    ):
        await ctx.defer()
        # get the voice channel the bot is connected to
        voice_channel, user_vc = await self.get_voice_channel(ctx, check_for_bot=True)
        if not any((voice_channel, user_vc)):
            return

        # if there is no query, return
        if query is None:
            await ctx.respond("No search query or link provided.")
            return

        # get the voice connection for the channel
        voice_connection = ctx.voice_client
        song = None

        # use a regex to determine if the query is a YouTube link, if so do not search for it
        if re.match(r"^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+$", query):
            song = await wavelink.NodePool.get_node().get_tracks(wavelink.YouTubeTrack, query)
            await voice_connection.play(song[0])
            await ctx.respond(f"Playing `{song[0].title}`")
        # if the query is not a YouTube link, search for it on YouTube
        else:
            song = await wavelink.YouTubeTrack.search(query=query)
            embed = discord.Embed(title="Choose a song",
                                  description="Please choose a song by pressing the corresponding button.",
                                  color=0x00ff00)
            for i in range(5):
                embed.add_field(name=f"{i + 1}. {song[i].title}", value=f"Duration: {song[i].length}s", inline=False)
            await ctx.interaction.followup.send(
                embed=embed,
                view=SongSelect(ctx, song, voice_connection, enqueue=enqueue)
            )
        if not song:
            await ctx.respond("No results found.")
            return

    @music.command(name="stop", description="Stops the current song")
    async def _stop(self, ctx: discord.ApplicationContext):
        # get the voice channel the bot is connected to
        await ctx.defer()
        voice_channel, _ = await self.get_voice_channel(ctx, check_for_bot=True)
        if not any((voice_channel, _)):
            return

        # get the voice connection for the channel
        voice_connection = ctx.voice_client
        if not voice_connection.is_playing():
            await ctx.interaction.followup.send("I'm not playing anything!")
            return
        # stop the current song
        await ctx.voice_client.stop()
        # clear the queue
        queue = RedisQueue(self.bot.redis_queue, str(ctx.guild.id))
        await queue.clear()
        await ctx.interaction.followup.send("Stopped playback.")

    @music.command(name="skip", description="Skips the current song")
    async def _skip(self, ctx: discord.ApplicationContext):
        # get the voice channel the bot is connected to
        await ctx.defer()
        voice_channel, _ = await self.get_voice_channel(ctx, check_for_bot=True)
        if not any((voice_channel, _)):
            return

        if not ctx.voice_client.is_playing():
            await ctx.interaction.followup.send("I'm not playing anything!")
            return

        # get the voice connection for the channel
        voice_connection = ctx.voice_client
        # stop the current song
        await ctx.voice_client.stop()  # stopping without clearing the queue will cause the next song to play
        await ctx.interaction.followup.send("Skipped the current song.")

    @music.command(name="queue", description="Lists all the songs in the playback queue")
    async def _queue(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        queue = RedisQueue(self.bot.redis_queue, str(ctx.guild.id))
        await queue.update_length()  # update the length of the queue
        if len(queue) == 0:
            await ctx.interaction.followup.send("The queue is empty.")
            return
        embed = discord.Embed(title="Queue", description="The current queue.", color=0x00ff00)
        async for data in queue.output_generator_nondestructive():
            song, user_id = data.split("|")
            song = await wavelink.NodePool.get_node().get_tracks(wavelink.YouTubeTrack, song)

            embed.add_field(name=song[0].title, value=f"Duration: {int(song[0].length)}s", inline=False)
        await ctx.interaction.followup.send(embed=embed)

    @music.command(name="volume", description="Sets the volume of the bot (0-100)")
    async def _volume(self, ctx: discord.ApplicationContext, volume: discord.Option(int, max_value=100, min_value=0)):
        # get the voice channel the bot is connected to
        await ctx.defer()
        voice_channel, _ = await self.get_voice_channel(ctx, check_for_bot=True)
        if not any((voice_channel, _)):
            return
        # set the volume of the bot
        client: wavelink.Player = ctx.voice_client
        await client.set_volume(volume)
        await ctx.respond(f"Set volume to {volume}%")

    @music.command(name="pause", description="Pauses the current song. Resumes if the song is already paused.")
    async def _pause_music(self, ctx: discord.ApplicationContext):
        # get the voice channel the bot is connected to
        await ctx.defer()
        voice_channel, _ = await self.get_voice_channel(ctx, check_for_bot=True)
        if not any((voice_channel, _)):
            return
        # pause the current song
        if ctx.voice_client.is_paused():
            await ctx.voice_client.resume()
            return await ctx.interaction.followup.send("Resuming playback.")
        else:
            await ctx.voice_client.pause()
            return await ctx.interaction.followup.send("Pausing playback.")

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player: wavelink.Player, track: wavelink.Track, reason):
        if reason == "FINISHED" or "STOPPED":
            queue = RedisQueue(self.bot.redis_queue, str(player.guild.id))
            await queue.update_length()
            if len(queue) > 0:
                data = await queue.pop()
                new_track_id, user_id = data.split("|")
                new_song = (await wavelink.NodePool.get_node().get_tracks(wavelink.YouTubeTrack, new_track_id))[0]
                await player.play(new_song)
        else:
            print(reason)

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        print(f"Node {node.identifier} is ready!")

    @commands.Cog.listener()
    async def on_wavelink_node_error(self, node: wavelink.Node, error: Exception):
        print(f"Node {node.identifier} encountered an error: {error}")


def setup(bot):
    bot.add_cog(MusicCog(bot))
