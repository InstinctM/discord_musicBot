import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import discord
from discord.ext import commands
from logger import info_logger, error_logger
from main import queues, voice_clients

from typing import Optional
import discord
import random
import os
import asyncio
import yt_dlp

from macros import YTDL_OPTIONS, FFMPEG_OPTIONS
from pytube import Playlist

class music_player(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

    @commands.Cog.listener()
    async def on_ready(self):
        info_logger.info("The bot is now online!")
        print(f"{self.bot.user} is now online!")

    @commands.Cog.listener()
    async def on_guild_remove(self):
        queues.clear()
        info_logger.info("Bot removed from server.")

    async def play_next(self, ctx):
        '''
        Helper function that plays the next song in the queue. See the play function.
        Args:
        ctx (commands.Context)
        
        '''
        if queues[ctx.guild.id]:
            url = queues[ctx.guild.id].pop(0)
            info_logger.info(f"Playing the next song - {url}")
            await self.play(ctx, url)

    def displayTime(self, duration: int):
        '''
        Returns the time in H:M:S format for better readability.

        Args:
        duration (int): The duration of a song in seconds.

        Returns:
        A string representation of the duration in H:M:S for readbility. 
        '''
        return f"Length: {duration // 3600:02}:{(duration % 3600) // 60:02}:{duration % 60:02}"

    async def displayNextSongs(self, ctx: commands.Context):
        '''
        Sends an Embed message to the text channel to display the upcoming 5 songs to be played.

        Args:
        ctx (commands.Context)
        '''

        next_songs = queues[ctx.guild.id][:5]

        loop = asyncio.get_event_loop()
        info = []
        for url in next_songs:
            try:
                data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(url, download=False))
                info.append({data["title"]: data["duration"]})
                info_logger.info(f"Songs coming up next: {data['title']} - {data['duration']}")
            except Exception as e:
                error_logger.error(f"Could not fetch information about {url}")
                info.append({"Could not fetch information about this song!": "N/A"})

        # Display the titles in the channel
        queue_embed = discord.Embed(title=f"**{len(queues[ctx.guild.id])}** songs in queue. Coming Up Next...", description="***** Here are the next 10 songs... *****", color=discord.Color.random())

        for song_info in info:  
            for title, duration in song_info.items():
                time = self.displayTime(duration)
                queue_embed.add_field(name=title, value=time, inline=False)
        await ctx.channel.send(embed=queue_embed)

    @commands.command(name="play")
    async def play(self, ctx: commands.Context, url: str):
        '''
        Plays the song at the given url, or the next song in the queue.

        Args:
        ctx (commands.Context)
        url (str): The url of the song on Youtube or Youtube Music.
        
        '''

        # Check if the user is in a voice channel
        if ctx.author.voice is None:
            await ctx.send("You are not connected to a voice channel.")
            return

        try:
            if not discord.utils.get(self.bot.voice_clients, guild=ctx.guild):
                # Connect to the voice channel you are in
                voice_client = await ctx.author.voice.channel.connect()
                voice_clients[voice_client.guild.id] = voice_client
        except Exception as e:
            print(e)
            error_logger.error(e)

        try:
            if ctx.voice_client.is_playing():
                # Queues stores songs for each voice channel it's in
                if ctx.guild.id not in queues:
                    queues[ctx.guild.id] = []
                queues[ctx.guild.id].append(url)
                info_logger.info(f"{url} added to queue.")
                await ctx.channel.send("Song added to the queue.")
            else:
                # Allows the bot to run and play music at the same time
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(url, download=False))

                if data is None or "url" not in data or "title" not in data:
                    error_logger.error(f'The information for song with url: {url} cannot be extratcted')
                    await ctx.send("Could not retrieve song information. Please check the URL. If the problem persists, check the logs.")

                    if queues:
                        skip_suggest = discord.Embed(title=f"Do you want to skip to the next song? Pressing {"\u274C"} will clear the current queue.", color=discord.Color.random())
                        tick_emoji = "\u2714"
                        cross_emoji = "\u274C"
                        msg = await ctx.channel.send(embed=skip_suggest)

                        def check(reaction, user):
                            return user == ctx.author and reaction.message.id == msg.id and str(reaction.emoji) in (tick_emoji, cross_emoji)
                        
                        try:
                            reaction, _ = await self.bot.wait_for('reaction_add', check=check)
                            await msg.delete()
                            if reaction == tick_emoji:
                                await self.play_next(ctx)
                            else:
                                queues.clear()
                                await ctx.channel.send("Queue cleared. Add a new song using the play command or add a playlist using the playlist command.")
                            return
                        except asyncio.TimeoutError:
                            print("Timeout: No reaction received in 60 seconds.")
                    return

                song = data["url"]
                title = data["title"]
                duration = data["duration"]
                player = discord.FFmpegOpusAudio(song, **FFMPEG_OPTIONS)
                
                info_logger.info(f"Currently playing {title}")
                await ctx.channel.send(f"Currently playing **{title}** -- {self.displayTime(duration)}")
                voice_clients[ctx.guild.id].play(player, after= lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))
        except Exception as e:
            print(e)
            error_logger.error(e)

    @commands.command(name="pause")
    async def pause(self, ctx: commands.Context):
        '''
        Pause the current song.

        Args:
        ctx (commands.Context)
        '''        
        try:
            info_logger.info("Pausing music bot")
            await ctx.channel.send(f"Pasuing...")
            voice_clients[ctx.guild.id].pause()
        except Exception as e:
            print(e)
            error_logger.error(e)
    
    @commands.command(name="resume")
    async def resume(self, ctx):
        '''
        Resume playing the paused song.

        Args:
        ctx (commands.Context)
        '''       
        try:
            info_logger.info("Resuming music playing")
            await ctx.channel.send(f"Resuming...")
            voice_clients[ctx.guild.id].resume()
        except Exception as e:
            print(e)
            error_logger.error(e)

    @commands.command(name="leave")
    async def leave(self, ctx):
        '''
        Command to make the bot disconnect from the current voice channel. This also stops the current song from playing and clears the queue.

        Args:
        ctx (commands.Context)
        '''  
        try:
            info_logger.info("Bot disconnecting")
            await ctx.channel.send(f"Disconnecting...")
            voice_clients[ctx.guild.id].stop()

            if ctx.guild.id in queues:
                queues[ctx.guild.id].clear()

            await voice_clients[ctx.guild.id].disconnect()
            del voice_clients[ctx.guild.id]
        except Exception as e:
            print(e)
            error_logger.error(e)

    @commands.command(name="shuffle")
    async def shuffle(self, ctx):
        '''
        Shuffle the current queue.

        Args:
        ctx (commands.Context)
        '''  
        try:
            info_logger.info("Shuffling queue")
            random.shuffle(queues[ctx.guild.id])
            await self.displayNextSongs(ctx)
            await ctx.channel.send("Queue shuffled")
        except Exception as e:
            print(e)
            error_logger.error(e)

    @commands.command(name="queue")
    async def queue(self, ctx):
        '''
        Display the current song queue.

        Args:
        ctx (commands.Context)
        '''  
        try:
            if not ctx.guild.id in queues or len(queues) == 0:
                info_logger.info("Displaying queue now")
                await ctx.channel.send("The queue is empty!")
            else:
                await ctx.channel.send("Hold on! I am trying my best...")
                await self.displayNextSongs(ctx)
 
        except Exception as e:
            print(e)
            error_logger.error(e)

    @commands.command(name="skip")
    async def skip(self, ctx, count: Optional[int] = 1):
        '''
        Skip the current song, regardless whether it is being played currently.
        If count is provided, the bot skips the provided amount of songs in the queue instead of one.

        Args:
        ctx (commands.Context)
        count (int): An optional parameter that when supplied the bot skips 'count' number of songs, Defaults = 1.
        '''  

        if count < 1:
            await ctx.channel.send("Please input a valid number!")
            error_logger.error(f"Invalid count: {count}")
        else:
            try:
                voice_clients[ctx.guild.id].stop()
                queues[ctx.guild.id] = queues.get(ctx.guild.id, [])[count-1:]
                info_logger.info(f"Skipping {count} song(s)")
                await ctx.channel.send(f"⏭ Skipping {count} song(s)")
                # await self.displayNextSongs(ctx)
            except Exception as e:
                print(e)
                error_logger.error(e)
            
    @commands.command(name="clearQ")
    async def clearQ(self, ctx):
        '''
        Clears the current song queue.

        Args:
        ctx (commands.Context)
        '''  
        try:
            if ctx.guild.id in queues:
                song_count = len(queues[ctx.guild.id])
                queues[ctx.guild.id].clear()
                info_logger.info("Clearing queue")
                await ctx.channel.send(f"{song_count} songs are removed from the queue.")
            else:
                await ctx.channel.send("The queue is empty!")
        except Exception as e:
            print(e)
            error_logger.error(e)

    @commands.command(name="playlist")
    async def playlist(self, ctx, playlistUrl: str):
        '''
        Adds all songs in the given playlist url to the queue.

        Args:
        ctx (commands.Context)
        playlistUrl (str): The url to a Youtube playlist
        '''  
        try:
            pl = Playlist(playlistUrl)
            
            for i in pl.videos:
                if ctx.guild.id not in queues:
                    queues[ctx.guild.id] = []
                queues[ctx.guild.id].append(i.watch_url)
            
            info_logger.info(f"Playlist added to queue - {len(queues)} song(s) in queue")
            await ctx.channel.send(f"{len(pl.videos)} songs added to the queue.")

            # If a playlist is supplied and the bot in not in any voice channels
            voice_client = ctx.voice_client
            if not voice_client or not voice_client.is_connected():
                voice_client = await ctx.author.voice.channel.connect()
                voice_clients[ctx.guild.id] = voice_client

            if not voice_client.is_playing():
                await self.play_next(ctx)

        except Exception as e:
            print(e)
            error_logger.error(e)

async def setup(bot):
    await bot.add_cog(music_player(bot))