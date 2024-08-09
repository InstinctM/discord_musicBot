import discord
from discord.ext import commands
import os
import asyncio
import yt_dlp
from dotenv import load_dotenv

def run_bot():
    load_dotenv()
    TOKEN = os.getenv("DISCORD_TOKEN")
    intents = discord.Intents.default()
    intents.message_content = True
    client = commands.Bot(command_prefix="!", intents=intents)

    queues = {}
    voice_clients = {}
    YTDL_OPTIONS = {"format": "bestaudio/best"}
    ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn -filter:a "volume=1.0"'}

    @client.event
    async def on_ready():
        print(f"{client.user} is now online!")

    async def play_next(ctx):
        if queues[ctx.guild.id] != []:
            url = queues[ctx.guild.id].pop(0)
            await play(ctx, url)

    @client.command(name="play")
    async def play(ctx, url):
        try:
            # Connect to the voice channel you are in
            voice_client = await ctx.author.voice.channel.connect()
            voice_clients[voice_client.guild.id] = voice_client
        except Exception as e:
            print(e)

        try:
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

            if ctx.guild.id in queue:
                queues[ctx.guild.id].clear()

            await voice_clients[ctx.guild.id].disconnect()
            del voice_clients[ctx.guild.id]
        except Exception as e:
            print(e)

    @client.command(name="queue")
    async def queue(ctx, url):
        try:
            if ctx.guild.id not in queues:
                queues[ctx.guild.id] = []
            queues[ctx.guild.id].append(url)
            await ctx.channel.send("Added 1 song to the queue.")
        except Exception as e:
            print(e)

    @client.command(name="skip")
    async def skip(ctx):
        try:
            voice_clients[ctx.guild.id].stop()
            await ctx.channel.send("Skipping the current song...")  
            await play_next(ctx)
        except Exception as e:
            print(e)
        
    @client.command(name="clearQ")
    async def clearQ(ctx):
        try:
            if ctx.guild.id in queue:
                queues[ctx.guild.id].clear()
                await ctx.channel.send("Queue cleared!")
            else:
                await ctx.channel.send("The queue is empty!")
        except Exception as e:
            print(e)

    @client.command(name="help")
    async def help(ctx):
        try:
            help_embed = discord.Embed(title="List of Commands Available", color=discord.Color.random())
            help_embed.add_field(name="play", value="Plays a song given a url from YouTube.")
            help_embed.add_field(name="pause", value="Pauses the current playing song.")
            help_embed.add_field(name="resume", value="Resumes playing the paused song.")
            help_embed.add_field(name="leave", value="Leaves the voice channel.")
            help_embed.add_field(name="queue", value="Adds a single song to the queue.")
            help_embed.add_field(name="skip", value="Skips the current playing song.")    
            help_embed.add_field(name="clearQ", value="Clears the queue.")    
        except Exception as e:
            print(e)

    client.run(TOKEN)

run_bot()