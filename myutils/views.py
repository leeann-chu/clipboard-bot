import discord, traceback
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
class ResponseModal(discord.ui.Modal, title='Prefix Manager'):
    prefix = discord.ui.TextInput(label='New Prefix', placeholder="Your new prefix here...")

    async def on_submit(self, interaction: discord.Interaction):
        prefixes = readfromFile("prefixes")
        prefixes[str(interaction.guild_id)] = self.prefix.value
        writetoFile(prefixes, "prefixes")
        await interaction.response.send_message(f"Successfully changed **standard prefix** to: `{self.prefix.value}`")

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)
        traceback.print_exception(type(error), error, error.__traceback__)


# Model View 
class ResponseView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=150)
        self.ctx = ctx

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This is not for you to poke around with.", ephemeral= True)
            return False
        else:
            return await super().interaction_check(interaction)

    async def on_timeout(self) -> None:
        self.children[0].disabled = True 
        await self.message.edit(view=self)

    @discord.ui.button(label="Open Modal", style=discord.ButtonStyle.blurple)
    async def modal_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ResponseModal())