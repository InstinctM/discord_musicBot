import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import discord
from discord.ext import commands
from logger import error_logger
from bs4 import BeautifulSoup
import re
from requests_html import HTMLSession
import asyncio
from main import voice_clients

class lyrics(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="lyrics")
    async def lyrics(self, ctx, *, title: str = None):
        '''
        Fetches the lyrics of the song of the given title from uta-net.

        Args:
        ctx (commands.Context)
        title (str): The title of the song, Defaults: None
        '''  
        def getInfo(entry):
            '''
            Retrieve the information of the song from BeautifulSoup.

            Args:
            entry (bs4.element.Tag): Song information retrieved using BeautifulSoup.

            Returns:
            A tuple containing the title of the song, name of artist and the lyrics of the song.
            '''  
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
            error_logger.error(e)

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
                            reaction, _ = await self.bot.wait_for('reaction_add', check=check)
                            error_logger.error(reaction)
                            await msg.delete()
                            songName, artist, lyrics = map[reaction.emoji]
                            lyrics_embed = discord.Embed(title=f"**Lyrics of {songName} from {artist}**", description=lyrics, color=discord.Color.random())
                            await ctx.channel.send(embed=lyrics_embed)
                        except asyncio.TimeoutError:
                            error_logger.error("Timeout: No reaction received in 60 seconds.")
                    
            else:
                await ctx.channel.send("No lyrics available")

        except Exception as e:
            print(e)
            error_logger.error(e)

async def setup(bot):
    await bot.add_cog(lyrics(bot))