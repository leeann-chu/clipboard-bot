from sqlalchemy.sql.functions import next_value
from main import randomHexGen, db
from utils.models import Lists, Tasks, recreate
from utils.views import Cancel, Confirm
from discord.ext import commands
import discord
import re

def formatContent(data):
    items = (re.sub('\n- |\n-|\n• |\n•', '\n', data))
    itemList = items.split("\n")
    spaceless = [{s.strip()} for s in itemList]
    return spaceless

class ListView(discord.ui.View):
    def __init__(self, ctx, bot, titleList, numList):
        super().__init__()
        self.ctx = ctx
        self.bot = bot
        
        if titleList:
            for emoji, title in zip(numList, titleList):
                button = ListButton(emoji, title)
                self.add_item(button)
            
            backButton = PageButtons("⇽ Back", discord.ButtonStyle.gray)
            self.add_item(backButton)
            nextButton = PageButtons("⇾ Next", discord.ButtonStyle.blurple)
            self.add_item(nextButton)
        else:
            self.add_item(ScopeSelect(self))
            self.add_item(discord.ui.Button(emoji = "<:confirm:851278899832684564>", label="Close Buttons", style=discord.ButtonStyle.green, custom_id = "done", row=4))
            
    @discord.ui.button(emoji = "<:cancel:851278899270909993>", label="Exit", style=discord.ButtonStyle.red, custom_id = "cancel", row=4)
    async def cancel(self, button: discord.ui.button, interaction: discord.Interaction):
        await self.message.delete() 
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("No.", ephemeral= True)
        else:
            selected = list(interaction.data.values())[0]
            if selected == "done":
                await interaction.response.edit_message(view = None)
        return await super().interaction_check(interaction)        

class ListButton(discord.ui.Button['ListView']):
    def __init__(self, emoji, title):
        super().__init__(emoji = emoji, label = title)
        
    async def callback(self, interaction: discord.Interaction):   
        menu = ScopeSelect(self.view)
        done = discord.ui.Button(emoji = "<:confirm:851278899832684564>", label="Close Buttons", style=discord.ButtonStyle.green, custom_id = "done", row=4)
        childrenCID = []
 
        for child in self.view.children:
            try:
                childrenCID.append(child.custom_id) # had trouble with self.view.children
            except: pass

        if done.custom_id not in childrenCID:
            self.view.add_item(done)
        if menu.custom_id not in childrenCID:
            self.view.add_item(menu)
            
        selList = self.view.bot.db.query(Lists).filter_by(title = self.label).first()     
        await interaction.response.edit_message(embed = view(selList), view=self.view)
   
class PageButtons(discord.ui.Button['ListView']):
    def __init__(self, label, style):
        super().__init__(label = label, style = style, row = 4)
        
    async def callback(self, interaction:discord.Interaction):
        await self.view.message.delete()
        await self.view.bot._list.get_command('browse')(ctx=self.view.ctx, pagenum = 1) 
        
class ListSettings(discord.ui.View):
    def __init__(self, ogView):
        super().__init__()
        self.ogView = ogView
        self.add_item(ScopeSelect(ogView))
        
    @discord.ui.button(emoji="✏", label="Rename List", style=discord.ButtonStyle.gray)
    async def edit(self, button: discord.ui.button, interaction: discord.Interaction):
        print("rename list")
        
    @discord.ui.button(emoji="🙈", label="Hide List", style=discord.ButtonStyle.gray)
    async def hide(self, button: discord.ui.button, interaction: discord.Interaction):
        print("hide list")
        
    @discord.ui.button(emoji="<:trash:926991605615960064>", label="Delete List", style=discord.ButtonStyle.red)
    async def delete(self, button: discord.ui.button, interaction: discord.Interaction):
        await self.ogView.message.delete()
        await self.ogView.bot._list.get_command('delete')(ctx=self.ogView.ctx, title=interaction.message.embeds[0].title)
        
class TaskSettings(discord.ui.View):
    def __init__(self, ogView):
        super().__init__()
        self.ogView = ogView
        self.add_item(ScopeSelect(ogView))
        
    @discord.ui.button(emoji="<:check:926281518266073088>", label="Change Task Status", style=discord.ButtonStyle.green)
    async def status(self, button: discord.ui.button, interaction: discord.Interaction):
        await self.ogView.message.delete()
        await self.ogView.bot._list.get_command('complete')(ctx=self.ogView.ctx, title=interaction.message.embeds[0].title)
        
    @discord.ui.button(emoji="✏", label="Rename Task", style=discord.ButtonStyle.gray)
    async def edit(self, button: discord.ui.button, interaction: discord.Interaction):
        print("rename task")
        
    @discord.ui.button(emoji="➕", label="Add Task", style=discord.ButtonStyle.primary)
    async def add(self, button: discord.ui.button, interaction: discord.Interaction):
        print("add tasks")
        
    @discord.ui.button(emoji="<:cross:926283850882088990>", label="Remove Task", style=discord.ButtonStyle.red)
    async def delete(self, button: discord.ui.button, interaction: discord.Interaction):
        print("remove task")

class CompleteView(discord.ui.View):
    def __init__(self, ctx, bot, title):
        super().__init__()
        self.ctx = ctx
        self.title = title
        self.bot = bot
        self.selList = self.bot.db.query(Lists).filter_by(title = title).first()
        taskList = sorted(self.selList.rel_tasks, key = lambda task: task.number)
        for task in taskList:
            if task.status == "<:check:926281518266073088>":
                style = discord.ButtonStyle.green
            elif task.status == "<:wip:926281721224265728>":
                style = discord.ButtonStyle.blurple
            else:
                style = discord.ButtonStyle.secondary
            self.add_item(CompleteButtons(task.status, task.number, style))
        
        self.add_item(ScopeSelect(self))
        
    @discord.ui.button(emoji = "<:cancel:851278899270909993>", label="Exit", style=discord.ButtonStyle.red, row=4)
    async def cancel(self, button: discord.ui.button, interaction: discord.Interaction):
        await self.message.delete()
        
    @discord.ui.button(emoji = "<:confirm:851278899832684564>", label="Close Buttons", style=discord.ButtonStyle.green, row=4)
    async def confirm(self, button: discord.ui.button, interaction: discord.Interaction):
        await interaction.response.edit_message(view = None)
        
class CompleteButtons(discord.ui.Button):
    def __init__(self, emoji, label, style):
        super().__init__(emoji = emoji, label = label, style = style)
        
    async def callback(self, interaction: discord.Interaction):  
        selTask = self.view.bot.db.query(Tasks).filter_by(listID = self.view.selList.id).filter_by(number = self.label).first()
        
        if selTask.status == "<:check:926281518266073088>":
            selTask.taskItem = selTask.taskItem.replace("~", "*")
            selTask.status = "<:wip:926281721224265728>"
        elif selTask.status == "<:wip:926281721224265728>":
            selTask.taskItem = selTask.taskItem.replace("*", "")
            selTask.status = "<:notdone:926280852856504370>"
        else:
            selTask.taskItem = f"~~{selTask.taskItem}~~"
            selTask.status = "<:check:926281518266073088>"
        self.view.bot.db.commit()
        
        checkoffView =  CompleteView(self.view.ctx, self.view.bot, self.view.title)
        checkoffView.message = self.view.message
        await interaction.response.edit_message(embed = view(self.view.selList, True), view = checkoffView)

class ScopeSelect(discord.ui.Select):
    def __init__(self, ogView):
        self.listOption = discord.SelectOption(label="List Settings", emoji="<:list:927096692069789696>")
        self.taskOption = discord.SelectOption(label="Task Settings", emoji="<:notdone:926280852856504370>")
        self.backOption = discord.SelectOption(label="Go Back", emoji="◀️")
        
        self.oldView = ogView
        
        super().__init__(placeholder = "Select between List and Task Settings",
                         options = [self.listOption, self.taskOption, self.backOption], custom_id="menu")

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "List Settings":
            view = ListSettings(self.oldView)
        elif self.values[0] == "Task Settings":
            view = TaskSettings(self.oldView)
        else:
            view = self.oldView
        return await interaction.response.edit_message(view = view)     

#* ------- Setting up Cog -------
class clipboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = db
        
    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        print("clipboard is Ready")
        
    @commands.group(aliases = ["checklist", "clipboard", "l", "list", "lists", "task"])
    async def _list(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(f"Please specify what you'd like to do. \nEx: `{ctx.prefix}list create` \nSee `{ctx.prefix}list help` for a list of examples!")

    @commands.group(aliases = ["n", "notes"])
    async def note(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(f"Note subcommands are wip, use `{ctx.prefix}list create` to create lists instead")

#* -------    Help Command   -------
    @_list.command()
    async def help(self, ctx):
        embed = discord.Embed(
            title = "Help Menu",
            description =
            f"""`{ctx.prefix}list make`
            `{ctx.prefix}list view`
            `{ctx.prefix}list view <title>`
            `{ctx.prefix}list complete`
            `{ctx.prefix}list delete`
            `{ctx.prefix}view <title>`
            """,
            color = randomHexGen()
        ) 
        await ctx.send(embed = embed)
    
#* -------    List Creation   -------
    @_list.command(aliases = ["create", "new", "c", "m"])
    async def make(self, ctx, *, title=None):
        member = ctx.guild.get_member(ctx.author.id)
        try: pfp = member.avatar.url
        except: pfp = None

        await ctx.trigger_typing()
        embed = discord.Embed (
            title = "Checklist Creation",
            description = "",
            color = randomHexGen()
        )
        view = Cancel()
    #* Checklist Creation Embed
        if title is None:
            embed.description = "What would you like the **Title**/**Category** of your checklist to be?"
            embed.set_footer(text=f"{member}'s list | Title cannot exceed 200 characters") 
            titlePrompt = await ctx.send(f"> This question will time out in `3 minutes` • [{member}]", embed = embed, view = view)
            title = await self.bot.get_command('multi_wait')(ctx, view, 180)
            if not title:
                embed.description = f"List Creation canceled."
                embed.remove_footer()
                return await titlePrompt.edit(embed = embed, view = None, delete_after = 5)
            if len(title) > 200:
                title = False
                return await ctx.send("Title cannot exceed 200 characters, try again.")
            
            await titlePrompt.delete()

        if "\n" not in title:
            embed.description = "Enter the tasks you wish to complete separated by *new lines*"
            embed.set_footer(text=f"{member}'s list")
            tasksPrompt = await ctx.send(f"> This question will time out in `6 minutes` • [{member}]", embed = embed, view = view)
            taskString = await self.bot.get_command('multi_wait')(ctx, view, 400)
            taskList = (re.sub('\n- |\n-|\n• |\n•', '\n', taskString)).split("\n")
            if not taskString:
                embed.description = f"List Creation canceled."
                embed.remove_footer()
                return await tasksPrompt.edit(embed = embed, view = None, delete_after = 5)
            await tasksPrompt.delete()

        else:
            entireList = title
            title = re.match(r"\A.*", entireList).group()
            taskList = (re.sub('\n- |\n-|\n• |\n•', '\n', entireList)).split("\n")[1:] #turn into a list
    ##
        taskString = "\n<:notdone:926280852856504370> ".join(['', *taskList]) #Turn into a string
    #* Confirmation Embed
        embed = discord.Embed (
            title = f"{title}",
            description = taskString, 
            color = 0x2F3136
        )
        embed.set_footer(text=f"Created by {member}", icon_url=pfp if pfp else '')
        view = Confirm()
        confirmationEmbed = await ctx.send(f"> Does this look correct? • [{member}]", embed = embed, view=view)
    ##
        await view.wait()
        if view.value is None:
            embed.description = "Confirmation menu timed out!"
            return await confirmationEmbed.edit(embed = embed, view = None, delete_after = 3)
        elif view.value:
            _list = Lists(title = title, author = str(ctx.author.id), author_name = member.name)
            self.db.add(_list)
            for task in enumerate(taskList, start=1):
                newTask = Tasks(listID = _list.id, taskItem = task[1], number = task[0])
                self.db.add(newTask)
                _list.rel_tasks.append(newTask)

            self.db.commit()
            return await confirmationEmbed.edit("Saved to Database!", embed = embed, view = None)
        else:
            embed.description = "List canceled!"
            return await confirmationEmbed.edit(embed = embed, view = None, delete_after = 5)

#* Select your lists (allows for looser searches)
    @_list.command(aliases = ["b", "view"])
    async def browse(self, ctx, *, filterOption=None, pagenum = 0):
        member = ctx.guild.get_member(ctx.author.id)
    
        if filterOption is None:
            allLists = self.db.query(Lists).filter_by(author = str(ctx.author.id)).all()
        else: # given argument search for
            allLists = self.db.query(Lists).filter(Lists.title.like(f'{filterOption}%')).all()
            if not allLists:
                allLists = self.db.query(Lists).filter(Lists.author_name.like(f'{filterOption}%')).all()
       
        allLists = chunkList(allLists, 20)

        if len(allLists[pagenum]) > 1:
            numList = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
            titleList = [_list.title for _list in allLists[pagenum]]
            numList = numList[:len(titleList)]
        elif len(allLists[pagenum]) == 1:
            viewListObject = ListView(ctx, self, titleList = None, numList = None)
            viewListObject.message = await ctx.send(embed = view(allLists[pagenum][0]), view=viewListObject)
            return
        else:
            return await ctx.send(f"List(s) not found! Create a list using `{ctx.prefix}list create`")
        viewListObject = ListView(ctx, self, titleList, numList)
        viewListObject.message = await ctx.send(f"> Choose a list to view! • [{member}]", view = viewListObject)
    @browse.error
    async def _browse_handler(self, ctx, error):
        print(error)

#* Mark Tasks as complete
    @_list.command(aliases = ["checkoff"])
    async def complete(self, ctx, *, title: str):
        selList = await self._list.get_command('_checkExistence')(ctx, title)
        checkView = CompleteView(ctx, self, title)
        checkView.message = await ctx.send(embed = view(selList, True), view = checkView)
    
    @complete.error
    async def _list_handler(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'title':
                await ctx.send("You must specify which List's tasks you would like to mark complete.")  
        else:
            print(error)

#* Delete a List
    @_list.command()
    async def delete(self, ctx, *, title):
        member = ctx.guild.get_member(ctx.author.id)
        selList = await self._list.get_command('_checkExistence')(ctx, title)
        confirmView = Confirm()
        confirmationEmbed = await ctx.send(f"> Are you sure you want to delete this list? • [{member}]", embed = view(selList), view = confirmView)
        await confirmView.wait()
        if confirmView.value is None:
            await ctx.send("Confirmation menu timed out!", delete_after = 5)
        elif confirmView.value:
            self.db.delete(selList)
            self.db.commit()
            await ctx.send("Database Updated!", delete_after = 5)
        else:
            await ctx.send("Confirmation menu canceled!", delete_after = 5)
        await confirmationEmbed.delete()
        
    @delete.error
    async def delete_handler(self, ctx, error):
        print(error)
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'title':
                await ctx.send("You must specify what list you would like to delete.") 

#* View one list
    @commands.command(aliases = ["view", "v"]) # command that is not nested in the Note Group
    async def open(self, ctx, *, title=None):
        if title is None:
            await self._list.get_command('browse')(ctx, pagenum = 0)

        else:
            selList = self.db.query(Lists).filter_by(title = title).first()
            await ctx.send(embed = view(selList))

#* Other Commands
    @_list.command()
    async def recreate(self, ctx):
        recreate()
        await ctx.send("Database recreated")
        
    @_list.command()
    async def _checkExistence(self, ctx, title):
        selList = self.db.query(Lists).filter_by(title = title).first()
        if selList is None:
            return await ctx.send(f"No lists were found with name: `{title}`!")
        else:
            return selList 

    @_list.command()
    async def emoji(self,ctx):
        embed = discord.Embed (
            title = type(ctx.author.id),
            description = 
            """<:wip:926281721224265728> Harass Nathaniel
            <:notdone:926280852856504370> Work on Copper pot
            <:check:926281518266073088> Buy Dildos
            """,
            # description = "",
            color = 0x2F3136
        )

        await ctx.send(embed = embed)

#* Given query object, returns embed
def view(selList, numbered=None):
    sortedTasks = sorted(selList.rel_tasks, key = lambda task: task.number) #sorts by number instead of most recently updated
    if numbered:
        taskList = [f"{task.status} {task.number}. {task.taskItem}" for task in sortedTasks]
    else:
        taskList = [f"{task.status} {task.taskItem}" for task in sortedTasks]
    embed = discord.Embed(
        title = selList.title,
        description = f"\n".join(taskList),
        color = 0x2F3136,
        timestamp = selList.created
    )
    embed.set_footer(text = f"Created by {selList.author_name}")
    return embed

def chunkList(queryList, n): #chunk a list into lists of n size
    queryList = [queryList[i:i + n] for i in range(0, len(queryList), n)]
    return queryList

def setup(bot):
    bot.add_cog(clipboard(bot))