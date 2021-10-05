import discord
import json
import asyncio
from discord.ext import commands
from cogs.menusUtil import *
from main import randomHexGen

class utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        print("utilities is Ready")

    #➥ Server prefix set command
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def prefix(self, ctx):
        await ctx.trigger_typing()        
        
        embed = discord.Embed(
            title = "Changing Server Prefix",
            description = f"The **current** standard prefix is `{ctx.prefix}`\n\nPlease enter the new prefix:",
            color = randomHexGen()
        )
        embed.set_footer(text="React with ❌ to close the menu!")
        prefixEmbed = await ctx.send(embed = embed)
        stuff = await self.bot.get_command('reactRespond')(ctx, prefixEmbed, 50, ['<:cancel:851278899270909993>'])        
        try: 
            newPrefix = stuff.content
            with open("data/prefixes.json", 'r') as f:
                prefixes = json.load(f) 
            prefixes[str(ctx.guild.id)] = newPrefix
            with open("data/prefixes.json", 'w') as f:
                json.dump(prefixes, f, indent = 4)
            await ctx.send(f"Successfully changed **standard prefix** to: `{newPrefix}`")
            
        except:
            if stuff[0].emoji.name == 'cancel':
                    await ctx.channel.purge(limit = 1)
                    await ctx.send("Canceled", delete_after = 2)
        
    @prefix.error
    async def prefix_error(self, ctx, error):
        member = ctx.message.author
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f"sorry {member.display_name}, you do not have permission edit server prefix!", delete_after = 3)
    ##

    #➥ Clear Command and Error
    @commands.command(aliases=["purge"])
    @commands.has_permissions(manage_guild=True)
    async def clear(self, ctx, amount: int = 10, override = None):      
        if override is None:  
            view = Confirm()
            msg = await ctx.send(f"Clear {amount} messages?", view = view)
            await view.wait()
            if view.value is None:
                return await ctx.send(f"Confirmation menu timed out!", delete_after = 3)
            elif view.value:
                if amount>501 or amount<0:
                    await msg.delete()
                    return await ctx.send("Invalid amount. Maximum is 500", delete_after = 3)
                await msg.delete()
                await ctx.channel.purge(limit = amount + 1)
                await ctx.send(f"Cleared {amount} messages!", delete_after = 3)
            else:
                await msg.delete()
                return await ctx.send(f"Confirmation menu canceled", delete_after = 3)
        else:
            await ctx.channel.purge(limit = amount + 1)
            await ctx.send(f"Cleared {amount} messages!", delete_after = 3)     

    @clear.error
    async def clear_error(self, ctx, error):
        member = ctx.message.author
        
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f"Sorry {member.display_name}, you do not have permission to clear messages!", delete_after = 3)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"{member.display_name}, you forgot to include the number of messages you wanted to ")
    ##  
    
    #➥ waitfor command
    @commands.command()
    @commands.is_owner()
    async def waitCheck(self, ctx, timeout):
        def check(msg):
            return msg.author == ctx.author and ctx.channel == msg.channel
        try: 
            msg = await self.bot.wait_for('message', timeout = timeout, check = check)            
            if msg.content == f'{ctx.prefix}cancel':
                await msg.delete()
                await ctx.send("Canceled", delete_after = 2)
                return None
            elif f"{ctx.prefix}" in msg.content:
                await ctx.send("Only one command allowed at a time")
                return None
            else:
                return msg.content
            
        except asyncio.TimeoutError:
            return await ctx.send("You took too long, try again!", delete_after = 5)          
##

def setup(bot):
    bot.add_cog(utilities(bot))