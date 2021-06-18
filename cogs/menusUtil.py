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
class Confirm(menus.Menu):
    def __init__(self, msg):
        super().__init__(timeout = 40, delete_message_after=True, message = msg)
        self.result = None

    async def send_initial_message(self, ctx):
        return await ctx.send(embed = self.msg)

    @menus.button('<:cancel:851278899270909993>')
    async def do_deny(self, payload):
        self.result = False
        self.stop()

    @menus.button('<:confirm:851278899832684564>')
    async def do_confirm(self, payload):
        self.result = True
        self.stop()

    async def prompt(self, ctx):
        await self.start(ctx, wait=True)
        return self.result
    
#➥ Setting up an Viewing Notes Menu
class ViewNotes(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=9)
    
    async def format_page(self, menu, titleList, optionList, tagList):
        embed = discord.Embed(
            title = "Your Notes: ",
            description = "Enter a number to view selected note",
            color = randomHexGen()
        )
        #embed.add_field(name = entry + "Title: " + entry, value = entry)
        embed.set_footer(text = f'\nPage {menu.current_page + 1}/{self.get_max_pages()}')
        return '\n'.join(f'{i}. {v.title}' for i, v in enumerate(titleList, start = 1))
##
    
def setup(bot):
    bot.add_cog(menusUtil(bot))