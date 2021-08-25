import discord
from discord.ext import commands, menus
from main import randomHexGen

class menusUtil(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        print("menusUtil is Ready")

#➥ Setting up a Confirmation Menu
class Confirm(discord.ui.View):    
    def __init__(self):
        super().__init__()
        self.value = None     
        
    @discord.ui.button(emoji="<:confirm:851278899832684564>", style=discord.ButtonStyle.green)
    async def yes(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = True
        self.stop()
        
    @discord.ui.button(emoji="<:cancel:851278899270909993>", style=discord.ButtonStyle.red)
    async def no(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = False
        self.stop()
##
        
#➥ Setting up Viewing Notes Menu
class ViewNotes(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=9)
    
    async def format_page(self, menu, entries): 
        embed = discord.Embed(
            title = "Your Saved Notes",
            description = "Enter a number to view your selected note",
            color = randomHexGen()
        )
        embed.set_footer(text = f'\nPage {menu.current_page + 1}/{self.get_max_pages()}' + " | React with ❌ to cancel option selection")
        for entry in entries:
            embed.add_field(name = entry.option + " " + entry.title, value = entry.tag)        
        
        return embed
##
        
#➥ Setting up Deleting Notes Menu
class DeleteNotes(menus.MenuPages):
    def __init__(self, source):
        super().__init__(source = source, timeout = 60, delete_message_after=True)
        
    async def finalize(self, timed_out):
        try:
            if timed_out:
                await self.message.clear_reactions()
            else:
                await self.message.delete()
        except discord.HTTPException:
            pass
        
    @menus.button('<:cancel:851278899270909993>', position=menus.Last(0)) 
    async def on_cancel(self, payload):
        self.stop()
##

#➥ Setting up Menu Page Source
class EmbedFormatSource(menus.ListPageSource):
    def __init__(self, entries, per_page):
        super().__init__(entries, per_page=per_page)
            
    async def format_page(self, menu, entries): 
            embed = discord.Embed(
                title = "Selected Note(s) to be Deleted: \n" + entries[0].title,
                description = "Enter a number to delete selected note",
                color = randomHexGen()
            )
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/519350010706395157/850574601623961640/full_cross.png")
            embed.set_footer(text = f'\nPage {menu.current_page + 1}/{self.get_max_pages()}' + " | React with ❌ to cancel option selection")
            for entry in entries:
                embed.add_field(name = entry.option + "\n__" + entry.tag + "__", value = entry.content)        
            return embed
##

def setup(bot):
    bot.add_cog(menusUtil(bot))