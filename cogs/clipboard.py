import discord
import asyncio
from discord.ext import commands
from datetime import datetime
from main import randomHexGen, db, get_prefix
    
class clipboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = db
        
    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        print("clipboard is Ready")
        
    # Create Note (Step-by-step, Interactive) Command Group
    @commands.group()
    async def note(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(f"Please specify what you'd like to do. \nEx: `{ctx.prefix}note create` \nSee `{ctx.prefix}note help` for a list of examples!")
        
    # Create Quick (Faster Method) Command Group
    @commands.group()
    async def quick(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(f"Please specify what you'd like to do. \nEx: `{ctx.prefix}quick create` \nSee `{ctx.prefix}quick help` for a list of examples!")
    
#➥ create_note
    @note.command()
    async def create_note(self, ctx, title, content, tags, timestamp):
        connection = await self.db.acquire()
        async with connection.transaction():
            query = """ WITH notes_insert AS (
                        INSERT INTO notes (title, content, user_id, date_created, date_modified)
                        VALUES ($1, $2, $3, $5, $5)
                        RETURNING note_id
                        )
                        INSERT INTO notes_tags (note_id, title, tags)
                        VALUES ((SELECT note_id FROM notes_insert), $1, $4);
                    """  
            user_id = str(ctx.author.id)
            await self.db.execute(query, title, content, user_id, tags, timestamp)
        await self.db.release(connection)
        await ctx.send("Database updated!")
    
##

➥ Quick create_note
    @quick.command()
    async def qmake(self, ctx, title, tags):
        await ctx.send("What would you like to remember?")
        def check(msg):
            return msg.author == ctx.author and ctx.channel == msg.channel
        try: 
            msg = await self.bot.wait_for('message', timeout = 400, check = check)
            timestamp = datetime.utcnow()
            embed = discord.Embed(
                title = title,
                color = randomHexGen(), # Make this an option to set default to random
                timestamp = timestamp
            )
            embed.add_field(name="Category: " + tags, value = msg.content)
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
            await ctx.send("Saving Note...") # Make this a reaction too
            await ctx.send(embed = embed)
        except asyncio.TimeoutError:
            return await ctx.send("You took too long, try again!", delete_after = 5) 
        await self.create_note(ctx, title, msg.content, tags, timestamp)             
#

#➥ Full Interactive make_note
    @note.command(aliases=["create"])
    async def make(self, ctx):
        await ctx.send("Hello. What would you like the title of your note to be?")
        def check(msg):
            return msg.author == ctx.author and ctx.channel == msg.channel
        
        try: 
            title = await self.bot.wait_for('message', timeout = 50, check = check)
        except asyncio.TimeoutError:
            return await ctx.send("You took too long, try again!", delete_after = 5)
            
        await ctx.send(f"Awesome, title is `{title.content}`. What would you like to remember?\n" + 
                       f"You can type `{ctx.prefix}cancel` to cancel the note making process.")
        
    # Inserting Content
        try: 
            msg = await self.bot.wait_for('message', check = check, timeout = 400)
        except asyncio.TimeoutError:
            return await ctx.send("You took too long, try again!", delete_after = 5)
        if msg.content == f'{ctx.prefix}cancel':
            await ctx.send("Canceling...", delete_after = 2)
        else:
            await ctx.send("Would you like to label your note with any categories? Ex: Shopping, Homework, CS101...")
            try: 
                tags = await self.bot.wait_for('message', check = check, timeout = 100) #allow for no tags
                timestamp = datetime.utcnow()
                embed = discord.Embed(
                    title = title.content,
                    color = randomHexGen(), # Make this an option to set default to random
                    timestamp = timestamp
                )
                embed.add_field(name="Category: " + tags.content, value = msg.content)
                embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
                await ctx.send("Does this look about right to you? y/n") # Make this a reaction too
                await ctx.send(embed = embed)
            except asyncio.TimeoutError:
                return await ctx.send("You took too long, try again!", delete_after = 5)
            
            await self.create_note(ctx, title.content, msg.content, tags.content, timestamp)
##

#➥ Cancel is a real command I swear
    @commands.command()
    async def cancel(self, ctx):
        print("Canceled note")

##

#➥ del_note
    @note.command()
    async def del_note(self, ctx, title):
        bypass_owner_check = ctx.author.id == self.bot.owner_id
        clause = 'title = $1'
        
        if bypass_owner_check:
            args = [title]
        else:
            user_id = str(ctx.author.id)
            args = [title, user_id]
            user_clause = f'{clause} AND user_id = $2'
            
        query = f'DELETE FROM notes WHERE {user_clause} RETURNING note_id;'
        deleted = await self.db.fetchrow(query, *args)
        print(deleted)
        
        args.append(deleted[0])
        await self.db.execute(query, *args)
        await ctx.send("Note Deleted!")
##

#➥ Quick Delete Note
    # @note.command(aliases=["delete"])
    # async def remove(self, ctx, title):
    #     await self.del_note(ctx, title)

#➥ Interactive Delete by Title
    @note.command(aliases=["delete"])
    async def remove(self, ctx, argument = None):
        if argument is None:
            await ctx.send("What is the name of the note you would like to delete?")
            
            def check(msg):
                return msg.author == ctx.author and ctx.channel == msg.channel

            try:
                title = await self.bot.wait_for('message', timeout = 30, check = check)
            except asyncio.TimeoutError:
                return await ctx.send('You took too long. Try again!')
            
            await ctx.send(f"Just to confirm, you are deleting your note titled {title.content} (y/n)")
            await self.del_note(ctx, title.content)
##

            
def setup(bot):
    bot.add_cog(clipboard(bot))