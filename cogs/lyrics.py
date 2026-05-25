import discord
from discord.ext import commands
import aiohttp
import logging

error_logger = logging.getLogger('discord')

class LyricsSelect(discord.ui.Select):
    def __init__(self, song_results, ctx):
        self.song_results = song_results
        self.ctx = ctx
        
        # Create the dropdown options from our search results
        options = []
        for i, song in enumerate(song_results):
            # Discord limits labels to 100 characters
            label = f"{song['trackName']} - {song['artistName']}"[:100]
            options.append(discord.SelectOption(
                label=label, 
                description=song.get('albumName', 'Unknown Album')[:100], 
                value=str(i) # Store the index to retrieve the data later
            ))

        super().__init__(placeholder="Select the correct song...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        # Ensure only the person who ran the command can use the dropdown
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This menu isn't for you!", ephemeral=True)
            return

        # Get the selected song based on the index
        selected_index = int(self.values[0])
        song = self.song_results[selected_index]
        
        lyrics = song['plainLyrics']
        
        # Discord embeds have a 4096 character limit for descriptions.
        if len(lyrics) > 4096:
            lyrics = lyrics[:4093] + "..."

        embed = discord.Embed(
            title=f"**{song['trackName']} - {song['artistName']}**", 
            description=lyrics, 
            color=discord.Color.random()
        )
        
        # Edit the original message to remove the dropdown and show the lyrics
        await interaction.response.edit_message(embed=embed, view=None)

class LyricsView(discord.ui.View):
    def __init__(self, song_results, ctx):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.add_item(LyricsSelect(song_results, ctx))

    async def on_timeout(self):
        # Disable the dropdown if the user takes too long
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(content="Time to select a song has expired.", view=self)
        except Exception:
            pass

class LyricsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="lyrics")
    async def lyrics(self, ctx, *, title: str = None):
        """Fetches the lyrics of the given song."""
        if not title:
            await ctx.send("Please provide a song title! Usage: `!lyrics [song name]`")
            return
        
        await ctx.typing()

        try:
            async with aiohttp.ClientSession() as session:
                url = "https://lrclib.net/api/search"
                params = {"q": title}
                
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        await ctx.send("Sorry, the lyrics service is currently unavailable.")
                        return
                    
                    data = await response.json()

            valid_results = [song for song in data if song.get('plainLyrics')]

            if not valid_results:
                await ctx.send(f"No lyrics found for `{title}`.")
                return

            # Limit to top 10 results for the dropdown
            top_results = valid_results[:10]

            if len(top_results) == 1:
                # If only one song is found, just send it directly
                song = top_results[0]
                lyrics = song['plainLyrics']
                
                if len(lyrics) > 4096:
                    lyrics = lyrics[:4093] + "..."
                    
                embed = discord.Embed(
                    title=f"**{song['trackName']} - {song['artistName']}**", 
                    description=lyrics, 
                    color=discord.Color.random()
                )
                await ctx.send(embed=embed)
            
            else:
                # If multiple songs are found, send the dropdown view
                view = LyricsView(top_results, ctx)
                view.message = await ctx.send(
                    f"Found multiple results for `{title}`. Please select one:", 
                    view=view
                )

        except Exception as e:
            error_logger.error(f"Error fetching lyrics: {e}")
            await ctx.send("An error occurred while fetching the lyrics.")

async def setup(bot):
    await bot.add_cog(LyricsCog(bot))