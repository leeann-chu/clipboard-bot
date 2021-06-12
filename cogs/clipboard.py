import discord
import asyncio
import re
from discord.ext import commands
from datetime import datetime
from main import randomHexGen, db, get_prefix

def formatContent(data):
    items = (re.sub('- |-|• |•', '', data))
    itemList = items.split("\n")
    itemString = "\n• ".join(itemList)
    return "• " + itemString

#➥ Setting up Cog   
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
##
    
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

#➥ Full Interactive make_note
    @note.command(aliases=["create"])
    async def make(self, ctx, *, args = None):
        if args is not None:
            #➥ given Title and Tags
            try: 
                args = args.split(' | ')
                title = args[0]
                tag = args[1]
            except IndexError:
                await ctx.send(f"You forgot the seperator `|`. `{ctx.prefix}note make <Title> | <Tags>`")
                return     
            ##
        else:
            await ctx.send("What would you like the title of your note to be?" + 
                           f"\nYou can type `{ctx.prefix}cancel` at any point to cancel the note making process.")
            title = await self.waitCheck(ctx, 50)
            if title is None: return
                
            await ctx.send(f"Would you like to label your note with any categories? Shopping, Homework, CS101...")
            tag = await self.waitCheck(ctx, 50)
            if tag is None: return
        
        await ctx.send ("What would you like to remember?")
        msg = await self.waitCheck(ctx, 400)
        if msg is None: return
        await self.make_embed(ctx, title, tag, msg)
##
#➥ Make Note Embed
    @note.command()
    async def make_embed(self, ctx, title, tag, msg):
        timestamp = datetime.utcnow()
        embed = discord.Embed(
            title = title,
            color = randomHexGen(), # Make this an option to set default to random
            timestamp = timestamp
        )
        embed.add_field(name="Category: " + tag, value = msg)
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
        embed.set_footer(text="React with ❌ or ✅")
        await ctx.send("Does this look about right to you?")
        yn = await ctx.send(embed = embed)
        confirmation = await self.reactCheck(ctx, yn, 50, reactions = ['<:cancel:851278899270909993>', '<:confirm:851278899832684564>'])
        if confirmation == "y":
            await self.create_note(ctx, title, msg, tag, timestamp)      
##

#➥ waitfor command
    @note.command()
    async def waitCheck(self, ctx, timeout):
        def check(msg):
            return msg.author == ctx.author and ctx.channel == msg.channel
        try: 
            msg = await self.bot.wait_for('message', timeout = timeout, check = check)            
            if msg.content == f'{ctx.prefix}cancel':
                await ctx.channel.purge(limit=1)
                await ctx.send("Canceled", delete_after = 2)
                return None
            else:
                return msg.content
            
        except asyncio.TimeoutError:
            return await ctx.send("You took too long, try again!", delete_after = 5)          
##
#➥ reaction command
    @note.command()
    async def reactCheck(self, ctx, msg, timeout, reactions):
        for emoji in reactions:
            await msg.add_reaction(emoji)

        def check(reaction, user):
            return str(reaction.emoji) in reactions and user != self.bot.user

        try:
            reaction, user = await self.bot.wait_for('reaction_add', check = check, timeout = timeout)
            if str(reaction) == reactions[0]:
                await ctx.channel.purge(limit = 1)
                await ctx.send("Canceled", delete_after = 2)
                return 'n'
            else:
                await msg.clear_reactions() 
                return 'y'
                  
        except asyncio.TimeoutError:
            await ctx.send("You did not respond in time!")
            await msg.clear_reactions()
                
##        

#➥ Cancel is a real command I swear
    @commands.command()
    async def cancel(self, ctx):
        print("Canceled note")
##
    
#➥ del_note by noteId
    @note.command()
    async def del_noteId(self, ctx, note_id):
        await self.db.execute(f'DELETE FROM notes WHERE note_id={note_id};')
        await ctx.send("Note successfully deleted!")
##
#➥ get_noteId by title
    @note.command()
    async def get_noteId(self, title):
        query = f"SELECT note_id FROM notes WHERE title='{title}';"
        rows = await self.db.fetch(query)
        return rows
##
#➥ get_tag by title
    @note.command()
    async def get_tag(self, title):
        query = f"SELECT tags FROM notes_tags WHERE title='{title}';"
        rows = await self.db.fetch(query)
        return rows
##
#➥ get_content by title
    @note.command()
    async def get_content(self, ctx, title):
        bypass_owner_check = ctx.author.id == self.bot.owner_id
        clause = 'title = $1'
        if bypass_owner_check:
            args = [title]
        else:
            args = [title, str(ctx.author.id)]
            clause = f'{clause} AND user_id = $2'
            
        query = f'SELECT content FROM notes WHERE {clause};'
        return await self.db.fetch(query, *args)
##
    
#➥ del_note
    @note.command()
    async def del_note(self, ctx, title):
        contentRows = await self.get_content(ctx, title)
        #➥ Sending Note Options
        if len(contentRows) > 0:
            
            noteidRows = await self.get_noteId(title)
            note_id = [note_id for (note_id,) in noteidRows]
            
            tagRows = await self.get_tag(title)
            tags = [tags for (tags,) in tagRows]
            
            if len(contentRows) > 1:
                await ctx.send("You have multiple notes with this name! \nWhich would you like to delete?")
                         
            embed = discord.Embed(
                title = "Selected Note(s) to be Deleted",
                description = "Enter a number to choose",
                color = randomHexGen()
            )
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/519350010706395157/850574601623961640/full_cross.png")
            embed.set_footer(text="React with ❌ to cancel option selection")
            
            content = [content for (content,) in contentRows]
            optionList = [":one:", ":two:", ":three:", ":four:", ":five:", ":six:", ":seven:", ":eight:", ":nine:"]
            for noteContent, option, tag in zip(content, optionList, tags):
                embed.add_field(name = "Option: " + option + "\nCategory: " + tag, value = formatContent(noteContent))
        
        #➥ Allow to wait for both a message AND a reaction
            yn = await ctx.send(embed = embed) 
            cancel = '<:cancel:851278899270909993>'
            await yn.add_reaction(cancel)
            #➥ Individual Checks
            def checkEmoji(reaction, user):
                return str(reaction.emoji) in cancel and user != self.bot.user
            
            def checkMsg(msg):
                return msg.author == ctx.author and ctx.channel == msg.channel
            ##
            # asyncio magic?
            done, pending = await asyncio.wait([self.bot.wait_for('message', check = checkMsg), 
                                                self.bot.wait_for('reaction_add', check = checkEmoji)], 
                                                timeout = 20,
                                                return_when = asyncio.FIRST_COMPLETED)
            
            try:
                stuff = done.pop().result()
                try: 
                    selOption = int(stuff.content)
                    optionIndex = selOption - 1
                    try: 
                        selNote_id = note_id[optionIndex]
                        await self.del_noteId(ctx, selNote_id)
                    except IndexError:
                        await ctx.send("Choose a number from the options presented!", delete_after = 3)
                    await yn.clear_reactions()
                except ValueError: 
                    await ctx.send("Please enter a number 1-9!", delete_after = 3) 
                    await yn.clear_reactions()
                
                except:
                    if stuff[0].emoji.name == 'cancel':
                        await ctx.channel.purge(limit = 1)
                        await ctx.send("Canceled", delete_after = 2)
                
            except KeyError:
                await ctx.send("You did not respond in time!")
                await yn.clear_reactions()
            except Exception as e: 
                print(e)                
                
            for future in done:
                print("more errors?")
                future.exception()
            for future in pending:
                future.cancel()
        ##            
        elif len(contentRows) == 0:
            await ctx.send("You do not own any note with this name!")
##

#➥ Interactive Delete by Title
    @note.command(aliases=["delete"])
    async def remove(self, ctx, title = None):
        if title is None:
            await ctx.send("What is the name of the note you would like to delete?")
            title = await self.waitCheck(ctx, 50)
            if title is None: return            
            
        await self.del_note(ctx, title)
##
            
def setup(bot):
    bot.add_cog(clipboard(bot))