from typing import Optional
import discord
import random
import os
import asyncio
import yt_dlp
import logging
from bs4 import BeautifulSoup
import re
from requests_html import HTMLSession

from discord.ext import commands
from dotenv import load_dotenv
from pytube import Playlist

# Logger config
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',  
)

logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',  
)

def run_bot():
    load_dotenv()
    TOKEN = os.getenv("DISCORD_TOKEN")

    PREFIX = ";"
    intents = discord.Intents.default()
    intents.message_content = True
    client = commands.Bot(command_prefix=PREFIX, intents=intents)
    # Remove the default "help" command
    client.remove_command("help")

    queues = {}
    voice_clients = {}
    YTDL_OPTIONS = {"format": "bestaudio/best", "outtmpl": "%(extractor)s-%(id)s-%(title)s-%(qhash)s.%(ext)s", "quiet": True}
    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn -filter:a "volume=1.0"'}

    ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

    @client.event
    async def on_ready():
        logging.info("The bot is now online!")
        print(f"{client.user} is now online!")

    @client.event
    async def on_guild_remove():
        queues.clear()
        logging.info("Bot removed from server.")

    async def play_next(ctx):
        if queues[ctx.guild.id] != []:
            url = queues[ctx.guild.id].pop(0)
            logging.info(f"Playing the next song - {url}")
            await play(ctx, url)

    def displayTime(duration):
        return f"Length: {duration // 3600:02}:{(duration % 3600) // 60:02}:{duration % 60:02}"

    async def displayNextSongs(ctx):
        next_songs = queues[ctx.guild.id][:10]

        loop = asyncio.get_event_loop()
        info = []
        for url in next_songs:
            try:
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
                info.append({data["title"]: data["duration"]})
                logging.info(f"Songs coming up next: {data['title']} - {data['duration']}")
            except Exception as e:
                logging.info(f"Could not fetch information about {url}")
                info.append({"Could not fetch information about this song!": "N/A"})

        # Display the titles in the channel
        queue_embed = discord.Embed(title=f"**{len(queues[ctx.guild.id])}** songs in queue. Coming Up Next...", description="***** Here are the next 10 songs... *****", color=discord.Color.random())

        for song_info in info:
            for title, duration in song_info.items():
                time = displayTime(duration)
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
            logging.error(e)

        try:
            if ctx.voice_client.is_playing():
                # Queues stores songs for each voice channel it's in
                if ctx.guild.id not in queues:
                    queues[ctx.guild.id] = []
                queues[ctx.guild.id].append(url)
                logging.info(f"{url} added to queue.")
                await ctx.channel.send("Song added to the queue.")
            else:
                # Allows the bot to run and play music at the same time
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))

                song = data["url"]
                title = data["title"]
                duration = data["duration"]
                player = discord.FFmpegOpusAudio(song, **FFMPEG_OPTIONS)
                
                logging.info(f"Currently playing {title}")
                await ctx.channel.send(f"Currently playing **{title}** -- {displayTime(duration)}")
                voice_clients[ctx.guild.id].play(player, after= lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), client.loop))
        except Exception as e:
            print(e)
            logging.error(e)

    @client.command(name="pause")
    async def pause(ctx):
            try:
                logging.info("Pausing music bot")
                await ctx.channel.send(f"Pasuing...")
                voice_clients[ctx.guild.id].pause()
            except Exception as e:
                print(e)
                logging.error(e)
    
    @client.command(name="resume")
    async def resume(ctx):
            try:
                logging.info("Resuming music playing")
                await ctx.channel.send(f"Resuming...")
                voice_clients[ctx.guild.id].resume()
            except Exception as e:
                print(e)
                logging.error(e)

    @client.command(name="leave")
    async def leave(ctx):
        try:
            logging.info("Bot disconnecting")
            await ctx.channel.send(f"Disconnecting...")
            voice_clients[ctx.guild.id].stop()

            if ctx.guild.id in queues:
                queues[ctx.guild.id].clear()

            await voice_clients[ctx.guild.id].disconnect()
            del voice_clients[ctx.guild.id]
        except Exception as e:
            print(e)
            logging.error(e)

    @client.command(name="shuffle")
    async def shuffle(ctx):
        try:
            logging.info("Shuffling queue")
            random.shuffle(queues[ctx.guild.id])
            await displayNextSongs(ctx)
            await ctx.channel.send("Queue shuffled")
        except Exception as e:
            print(e)
            logging.error(e)

    @client.command(name="queue")
    async def queue(ctx):
        try:
            if not ctx.guild.id in queues or len(queues) == 0:
                logging.info("Displaying queue now")
                await ctx.channel.send("The queue is empty!")
            else:
                await ctx.channel.send("Hold on! I am trying my best...")
                await displayNextSongs(ctx)
 
        except Exception as e:
            print(e)
            logging.error(e)

    @client.command(name="skip")
    async def skip(ctx, count: Optional[int] = 1):
        if isinstance(count, int):
            if count is None:
                count = 1

            if count > 0:
                try:
                    queues[ctx.guild.id] = queues[ctx.guild.id][count:]
                    voice_clients[ctx.guild.id].stop()
                    logging.info(f"Skipping {count} song(s)")
                    await ctx.channel.send(f"Skipping {count} song(s)")
                    await displayNextSongs(ctx)
                except Exception as e:
                    print(e)
                    logging.error(e)
            else:
                await ctx.channel.send("Cannot skip 0 songs!")
                logging.error("Cannot skip 0 songs!")
        else:
            await ctx.channel.send("Please input a valid number!")
            logging.error("Passed count is not a valid integer")
            
    @client.command(name="clearQ")
    async def clearQ(ctx):
        try:
            if ctx.guild.id in queues:
                song_count = len(queues[ctx.guild.id])
                queues[ctx.guild.id].clear()
                logging.info("Clearing queue")
                await ctx.channel.send(f"{song_count} songs are removed from the queue.")
            else:
                await ctx.channel.send("The queue is empty!")
        except Exception as e:
            print(e)
            logging.error(e)

    @client.command(name="playlist")
    async def playlist(ctx, playlistUrl):
        try:
            pl = Playlist(playlistUrl)
            
            for i in pl.videos:
                if ctx.guild.id not in queues:
                    queues[ctx.guild.id] = []
                queues[ctx.guild.id].append(i.watch_url)
            
            logging.info(f"Playlist added to queue - {len(queues)} song(s) in queue")
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
            logging.error(e)

    @client.command(name="lyrics")
    async def lyrics(ctx, *, title: str = None):
        def getInfo(entry):
            songName = entry.find(class_="fw-bold songlist-title").text
            artist = entry.find(class_='sp-none fw-bold').text
            lyrics = re.sub('\u3000', "\n", entry.find(class_='d-block pc-utaidashi').text)
            return (songName, artist, lyrics)

        try:
            # Connect to the voice channel you are in
            voice_client = await ctx.author.voice.channel.connect()
            voice_clients[voice_client.guild.id] = voice_client
        except Exception as e:
            print(e)
            logging.error(e)

        if not title:
            await ctx.channel.send(f"No lyrics available")
            return
        
        try:
            session = HTMLSession()
            url = f"https://www.uta-net.com/search/?Keyword={title}"
            response = session.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Limit the search result to the top page only
                top_res = soup.find_all(class_="songlist-table-body")[:1]
                for elem in top_res:
                    # Limit the search result to first 10 results
                    entries = elem.find_all(class_='border-bottom')[:10]
                    if len(entries) == 1:
                        for entry in entries:
                            songName, artist, lyrics = getInfo(entry)
                            lyrics_embed = discord.Embed(title=f"**Lyrics of {songName} from {artist}**", description=lyrics, color=discord.Color.random())
                            await ctx.channel.send(embed=lyrics_embed)
                    else:
                        select_embed = discord.Embed(title=f"Select the lyrics of the song you would like to see by typing the corresponding number below", color=discord.Color.random())

                        map = {}
                        for i, entry in enumerate(entries, start=1):
                            emoji = "\U0001F51F" if i == 10 else f"{i}\u20E3"
                            map[emoji] = getInfo(entry)
                            select_embed.add_field(name=f"{emoji}: {map[emoji][0]} - {map[emoji][1]}", value='', inline=False)
                        msg = await ctx.channel.send(embed=select_embed)

                        for i in range(1, len(map) + 1):
                            if i == 10:
                                await msg.add_reaction("\U0001F51F")
                            else:
                                await msg.add_reaction(f"{i}\u20E3")

                        def check(reaction, user):
                            return user == ctx.author and reaction.message.id == msg.id and str(reaction.emoji) in map

                        try:
                            reaction, _ = await client.wait_for('reaction_add', check=check)
                            await msg.delete()
                            songName, artist, lyrics = map[reaction.emoji]
                            lyrics_embed = discord.Embed(title=f"**Lyrics of {songName} from {artist}**", description=lyrics, color=discord.Color.random())
                            await ctx.channel.send(embed=lyrics_embed)
                        except asyncio.TimeoutError:
                            print("Timeout: No reaction received in 60 seconds.")
                    
            else:
                await ctx.channel.send("No lyrics available")

        except Exception as e:
            print(e)
            logging.error(e)

    @client.command(name="help")
    async def help(ctx):
        try:
            help_embed = discord.Embed(title="Bot Help", description=f"This is the list of available commands. \n The current prefix is  **{PREFIX}**",color=discord.Color.random())
            help_embed.add_field(name="`clearQ`", value="Clears the queue.", inline=False)
            help_embed.add_field(name="`help`", value="Opens up the current menu  .", inline=False)
            help_embed.add_field(name="`leave`", value="Leaves the voice channel.", inline=False)
            help_embed.add_field(name="`pause`", value="Pauses the current playing song.", inline=False)
            help_embed.add_field(name="`play`", value="Plays a song given a url from YouTube.", inline=False)
            help_embed.add_field(name="`playlist`", value="Adds all the songs in a YouTube playlist to the queue.", inline=False)
            help_embed.add_field(name="`queue`", value="Shows next 5 songs in the queue.", inline=False)
            help_embed.add_field(name="`resume`", value="Resumes playing the paused song.", inline=False)
            help_embed.add_field(name="`shuffle`", value="Shuffles the current queue.", inline=False)    
            help_embed.add_field(name="`skip`", value="Skips the provided number of songs.", inline=False)    
            help_embed.add_field(name="`lyrics`", value="Display the lyrics of a song.", inline=False)    

            await ctx.channel.send(embed=help_embed)
        except Exception as e:
            print(e)
            logging.error(e)

    @client.command(name="ping")
    async def ping(ctx):
        logging.info("pong")
        await ctx.channel.send("pong")

    client.run(TOKEN)

if __name__ == "__main__":
    run_bot()