import discord
import asyncio
from discord.ext import commands
import datetime
    
class clipboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        print("clipboard is Ready")

    @commands.command()
    async def make(self, ctx):
        await ctx.send("Hello. What would you like the title of your note to be?")
        def check(msg):
            return msg.author == ctx.author and ctx.channel == msg.channel

        try: 
            title = await self.bot.wait_for('message', timeout = 30, check = check)
            query = """SELECT 1 FROM notes WHERE user_id = $1 AND LOWER(title) = $2;"""
            row = await ctx.db.fetchrow(query, ctx.guild.get_member(int), title.lower())
        
        except asyncio.TimeoutError:
            return await ctx.send("You took too long, try again!")
        
            
def setup(bot):
    bot.add_cog(clipboard(bot))