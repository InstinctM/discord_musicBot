import discord
from discord.ext import commands
import random
import os
import asyncio
import yt_dlp
from dotenv import load_dotenv
from pytube import Playlist

def run_bot():
    load_dotenv()
    TOKEN = os.getenv("DISCORD_TOKEN")
    intents = discord.Intents.default()
    intents.message_content = True
    client = commands.Bot(command_prefix="!", intents=intents)
    # Remove the default "help" command
    client.remove_command("help")

    queues = {}
    voice_clients = {}
    YTDL_OPTIONS = {"format": "bestaudio/best"}
    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn -filter:a "volume=1.0"'}

    ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

    @client.event
    async def on_ready():
        print(f"{client.user} is now online!")

    @client.event
    async def on_guild_remove():
        queues.clear()

    async def play_next(ctx):
        if queues[ctx.guild.id] != []:
            url = queues[ctx.guild.id].pop(0)
            await play(ctx, url)

    async def displayNextSongs(ctx):
        next_songs = queues[ctx.guild.id][:5]

        loop = asyncio.get_event_loop()
        info = []
        for url in next_songs:
            try:
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
                info.append({data["title"]: data["duration"]})
            except Exception as e:
                info.append({"Could not fetch information about this song!": "N/A"})

        # Display the titles in the channel
        queue_embed = discord.Embed(title=f"**{len(queues[ctx.guild.id])}** songs in queue. Coming Up Next...", description="***** Here are the next 5 songs... *****", color=discord.Color.random())

        for song_info in info:
            for title, duration in song_info.items():
                time = f"Length: {duration // 3600:02}:{(duration % 3600) // 60:02}:{duration % 60:02}"
                queue_embed.add_field(name=title, value=time, inline=False)
        await ctx.channel.send(embed=queue_embed)

    @client.command(name="play")
    async def play(ctx, url):
        try:
            # Connect to the voice channel you are in
            voice_client = await ctx.author.voice.channel.connect()
            voice_clients[voice_client.guild.id] = voice_client
        except Exception as e:
            print(e)

        try:
            if ctx.voice_client.is_playing():
                # Queues stores songs for each voice channel it's in
                if ctx.guild.id not in queues:
                    queues[ctx.guild.id] = []
                queues[ctx.guild.id].append(url)
                await ctx.channel.send("Song added to the queue.")
            else:
                # Allows the bot to run and play music at the same time
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))

                song = data["url"]
                title = data["title"]
                player = discord.FFmpegOpusAudio(song, **FFMPEG_OPTIONS)

                await ctx.channel.send(f"Currently playing **{title}**")
                voice_clients[ctx.guild.id].play(player, after= lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), client.loop))
        except Exception as e:
            print(e)

    @client.command(name="pause")
    async def pause(ctx):
            try:
                await ctx.channel.send(f"Pasuing...")
                voice_clients[ctx.guild.id].pause()
            except Exception as e:
                print(e)
    
    @client.command(name="resume")
    async def resume(ctx):
            try:
                await ctx.channel.send(f"Resuming...")
                voice_clients[ctx.guild.id].resume()
            except Exception as e:
                print(e)

    @client.command(name="leave")
    async def leave(ctx):
        try:
            await ctx.channel.send(f"Disconnecting...")
            voice_clients[ctx.guild.id].stop()

            if ctx.guild.id in queues:
                queues[ctx.guild.id].clear()

            await voice_clients[ctx.guild.id].disconnect()
            del voice_clients[ctx.guild.id]
        except Exception as e:
            print(e)

    @client.command(name="shuffle")
    async def shuffle(ctx):
        try:
            random.shuffle(queues[ctx.guild.id])
            await displayNextSongs(ctx)
            await ctx.channel.send("Queue shuffled")
        except Exception as e:
            print(e)

    @client.command(name="queue")
    async def queue(ctx):
        try:
            if not ctx.guild.id in queues or len(queues) == 0:
                await ctx.channel.send("The queue is empty!")
            else:
                await ctx.channel.send("Hold on! I am trying my best...")
                await displayNextSongs(ctx)
 
        except Exception as e:
            print(e)

    @client.command(name="skip")
    async def skip(ctx):
        try:
            voice_clients[ctx.guild.id].stop()
            await ctx.channel.send("Skipping the current song...")  
        except Exception as e:
            print(e)
        
    @client.command(name="clearQ")
    async def clearQ(ctx):
        try:
            if ctx.guild.id in queues:
                queues[ctx.guild.id].clear()
                await ctx.channel.send(f"{len(queues)} songs are removed from the queue.")
            else:
                await ctx.channel.send("The queue is empty!")
        except Exception as e:
            print(e)

    @client.command(name="playlist")
    async def playlist(ctx, playlistUrl):
        try:
            pl = Playlist(playlistUrl)
            
            for i in pl.videos:
                if ctx.guild.id not in queues:
                    queues[ctx.guild.id] = []
                queues[ctx.guild.id].append(i.watch_url)
            
            await ctx.channel.send(f"{len(pl.videos)} songs added to the queue.")

            # If a playlist is supplied and the bot in not in any voice channels
            voice_client = ctx.voice_client
            if not voice_client or not voice_client.is_connected():
                voice_client = await ctx.author.voice.channel.connect()
                voice_clients[ctx.guild.id] = voice_client

            if not voice_client.is_playing():
                await play_next(ctx)

        except Exception as e:
            print(e)

    @client.command(name="help")
    async def help(ctx):
        try:
            help_embed = discord.Embed(title="Bot Help", description= "This is the list of available commands.",color=discord.Color.random())
            help_embed.add_field(name="clearQ", value="Clears the queue.", inline=False)
            help_embed.add_field(name="leave", value="Leaves the voice channel.", inline=False)
            help_embed.add_field(name="pause", value="Pauses the current playing song.", inline=False)
            help_embed.add_field(name="play", value="Plays a song given a url from YouTube.", inline=False)
            help_embed.add_field(name="playlist", value="Adds all the songs in a YouTube playlist to the queue.", inline=False)
            help_embed.add_field(name="queue", value="Shows next 5 songs in the queue.", inline=False)
            help_embed.add_field(name="resume", value="Resumes playing the paused song.", inline=False)
            help_embed.add_field(name="shuffle", value="Shuffles the current queue.", inline=False)    
            help_embed.add_field(name="skip", value="Skips the current playing song.", inline=False)    

            await ctx.channel.send(embed=help_embed)
        except Exception as e:
            print(e)

    client.run(TOKEN)

run_bot()