import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import discord
from discord.ext import commands
from logger import error_logger

from macros import PREFIX

class general(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='help')
    async def help(self, ctx):
        '''
        Sends a Embed message to the text channel for users to view the usage of each command.

        Args:
        ctx (commands.Context)
        title (str): The title of the song, Defaults: None
        '''  
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
            error_logger.error(e)


async def setup(bot):
    await bot.add_cog(general(bot))