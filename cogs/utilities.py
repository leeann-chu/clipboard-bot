import discord
import asyncio
from utils.poll_class import Confirm, Cancel, readfromFile, writetoFile
from discord.ext import commands
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
        view = Cancel()
        prefixEmbed = await ctx.send(embed = embed, view = view)
        stuff = await self.multi_wait(ctx, view, 50)
        if isinstance(stuff, str):
            newPrefix = stuff
            prefixes = readfromFile("prefixes")
            prefixes[str(ctx.guild.id)] = newPrefix
            writetoFile(prefixes, "prefixes")
            embed.description = f"Successfully changed **standard prefix** to: `{newPrefix}`"
            await prefixEmbed.edit(embed = embed, view = None, delete_after = 5)
            await ctx.channel.purge(limit = 1)
        else:
            embed.description = f"Prefix menu canceled. \n**Standard prefix**: `{ctx.prefix}`"
            await prefixEmbed.edit(embed = embed, view = None, delete_after = 5)
        
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

    #➥ multi_wait command
    @commands.command()
    @commands.is_owner()
    async def multi_wait(self, ctx, view, timeout):    
      
        # asyncio magic?
        done, pending = await asyncio.wait([
                            self.waitCheck(ctx, 50),
                            view.wait()], 
                            timeout = timeout,
                            return_when = asyncio.FIRST_COMPLETED)
        try:
            stuff = done.pop().result()
            return stuff
        except KeyError:
                await ctx.send("Something went wrong, keyError")
        except Exception as e: 
            print(e) 
            
        for future in done:
            print("more errors?")
            future.exception()
        for future in pending:
            future.cancel()
    ##

def setup(bot):
    bot.add_cog(utilities(bot))