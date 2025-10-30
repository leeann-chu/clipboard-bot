import traceback
from re import MULTILINE, findall
from typing import List
import discord
from myutils.poll_class import readfromFile, writetoFile

#➥ Setting up a Confirmation Menu — Want to get rid of
class Confirm(discord.ui.View):
    def __init__(self, ctx):
        super().__init__()
        self.value = None
        self.ctx = ctx

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This is not your menu to navigate.", ephemeral= True)
            return False
        else:
            return await super().interaction_check(interaction)

    @discord.ui.button(emoji="<:confirm:851278899832684564>", label = "Yes", style=discord.ButtonStyle.green)
    async def yes(self, button: discord.ui.button, interaction: discord.Interaction):
        self.value = True
        self.stop()

    @discord.ui.button(emoji="<:cancel:851278899270909993>", label = "No", style=discord.ButtonStyle.red)
    async def no(self, button: discord.ui.button, interaction: discord.Interaction):
        self.value = False
        self.stop()
##

class Cancel(discord.ui.View):
    def __init__(self, ctx, timeout=400):
        super().__init__(timeout=timeout)
        self.value = None
        self.ctx = ctx

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This is not your menu to navigate.", ephemeral= True)
            return False
        else:
            return await super().interaction_check(interaction)

    @discord.ui.button(emoji="<:cancel:851278899270909993>", label = "Exit", style=discord.ButtonStyle.red)
    async def no(self, button: discord.ui.button, interaction: discord.Interaction):
        self.value = False
        self.stop()

## 

class EmbedPageView(discord.ui.View):
    def __init__(self, eList, pagenum):
        super().__init__(timeout=20)
        self.eList = eList
        self.pagenum = pagenum
        self.totpage = len(self.eList)

        self.children[0].disabled = True # back button should be disabled on init
    
    async def update_children(self, i: discord.Interaction):
        self.back.disabled = self.pagenum <= 0
        self.next.disabled = self.pagenum + 1 >= self.totpage

        await i.response.edit_message(embed=self.eList[self.pagenum], view=self)

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        await self.message.edit(view=self)
    
    @discord.ui.button(label = "⇽ Back", style = discord.ButtonStyle.gray)
    async def back(self, i:  discord.Interaction, button: discord.ui.Button):
        self.pagenum -= 1
        await self.update_children(i)

    @discord.ui.button(label = "⇾ Next", style = discord.ButtonStyle.blurple)
    async def next(self, i:  discord.Interaction, button: discord.ui.Button):
        self.pagenum += 1
        await self.update_children(i)

# Modals
class PollModal(discord.ui.Modal, title='Poll Maker'):
    title_input = discord.ui.TextInput(label='Poll Title', placeholder="Your title goes here", required=True)
    options = discord.ui.TextInput(label='Options', 
                                   placeholder="""Ex) \t🪁 Blue\n\t🍏 Green\n\t🚗 Red\n\t🪙 Yellow""", 
                                   required = True,
                                   style=discord.TextStyle.paragraph)

    def __init__(self, msg=None, emojis=None, _title=None):
        super().__init__()
        self.msg = msg
        self.emojis = emojis
        self._title = _title
    
    async def on_submit(self, interaction: discord.Interaction):
        emojis_opts_pairs = findall(r"^(\S+)\s+(.*)", self.options.value, MULTILINE)
        self.emojis, self.msg  = map(list, zip(*emojis_opts_pairs))
        self._title = self.title_input.value
        
        await interaction.response.defer(thinking=False) # this satisfies the modal so it thinks it sent a response even though it didn't
        return await interaction.message.delete()

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)
        traceback.print_exception(type(error), error, error.__traceback__)

class PrefixModal(discord.ui.Modal, title='Prefix Manager'):
    def __init__(self, embed):
        super().__init__()
        self.prefix = discord.ui.TextInput(label='New Prefix', placeholder="Your new prefix here...")
        self.embed = embed
        self.add_item(self.prefix)

    async def on_submit(self, interaction: discord.Interaction):
        prefixes = readfromFile("prefixes")
        prefixes[str(interaction.guild_id)] = self.prefix.value
        writetoFile(prefixes, "prefixes")
        self.embed.description = f"Successfully changed **standard prefix** to: `{self.prefix.value}`"
        return await interaction.response.edit_message(embed=self.embed, view = None)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)
        traceback.print_exception(type(error), error, error.__traceback__)

# Modal Universal Button — Look I tried to use a decorator I really did do you think I subclass for fun?
class ResponseButton(discord.ui.Button['ResponseView']):
    def __init__(self, buttonLabel, modal):
        super().__init__(label = buttonLabel, style=discord.ButtonStyle.primary)
        self.modal = modal        
    async def callback(self, interaction: discord.Interaction): 
        await interaction.response.send_modal(self.modal)

# Modal Prefix View 
class ResponseView(discord.ui.View):
    children: List[ResponseButton]
    def __init__(self, ctx, label, modal):
        super().__init__(timeout=150)
        self.ctx = ctx
        self.add_item(ResponseButton(label, modal))

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This is not for you to poke around with <:humber:940834492376039494>", ephemeral= True)
            return False
        else:
            return await super().interaction_check(interaction)

    async def on_timeout(self) -> None:
        self.children[0].disabled = True 
        try:
            await self.message.edit(view=self)
        except Exception: # message deleted
            print("message was deleted after success")