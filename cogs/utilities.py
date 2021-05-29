import discord
import json
from discord.ext import commands
from main import randomHexGen, get_prefix
import asyncio

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
        
        prefix = get_prefix(self, ctx)
        embed = discord.Embed(
            title = "Changing Server Prefix",
            description = f"The **current** standard prefix is `{prefix}`\n\nPlease enter the new prefix:",
            color = randomHexGen()
        )
        embed.set_footer(text="Enter \"cancel\" to close menu!")
        
        delEmbed = await ctx.send(embed = embed)
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        
        try: 
            newPrefix = await self.bot.wait_for('message', check = check, timeout = 20)
            
            if (newPrefix.content) == 'cancel':
                await delEmbed.delete()
            else:
                with open("prefixes.json", 'r') as f:
                    prefixes = json.load(f) 
                prefixes[str(ctx.guild.id)] = newPrefix.content
                with open("prefixes.json", 'w') as f:
                    json.dump(prefixes, f, indent = 4)
                await ctx.send(f"Successfully changed **standard prefix** to: `{newPrefix.content}`")
        except asyncio.TimeoutError:
            await ctx.send(f"{ctx.author.display_name} did not respond in time!", delete_after = 5)
        
    @prefix.error
    async def prefix_error(self, ctx, error):
        member = ctx.message.author
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f"sorry {member.display_name}, you do not have permission edit server prefix!", delete_after = 3)
    ##
        
    #➥ Clear Command and Error
    @commands.command(name="clear", aliases=["purge", "delete"])
    @commands.has_permissions(manage_guild=True)
    async def clear(self, ctx, amount=10):
        await ctx.channel.purge(limit=amount)
        await ctx.send(f"Cleared {amount} messages!", delete_after = 5)

    @clear.error
    async def clear_error(self, ctx, error):
        member = ctx.message.author
        message = ctx.message
        
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f"Sorry {member.display_name}, you do not have permission to clear messages!", delete_after = 3)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"{member.display_name}, you forgot to include the number of messages you wanted to ")
    ##

def setup(bot):
    bot.add_cog(utilities(bot))