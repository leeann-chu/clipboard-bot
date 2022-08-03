from main import randomHexGen
from main import db as db
from main import override as override
from utils.models import Lists, Tasks, recreate
from utils.views import Cancel, Confirm
from discord.ext import commands
import discord
import re

listsPerPage = 5
tasksPerPage = 15

class ListView(discord.ui.View):
    def __init__(self, ctx, bot, allLists, pagenum, totpage):
        super().__init__()
        self.ctx = ctx
        self.bot = bot
        self.allLists = allLists
        self.pagenum = pagenum
        self.totpage = totpage
        
        if isinstance(allLists, list):
            for _list in allLists[pagenum]:
                button = ListButton(_list.id, _list.title)
                if _list.private and (str(ctx.author.id) != _list.author):
                    button.disabled = True
                self.add_item(button)
            
            if totpage > 1:                            
                backButton = PageButton("⇽ Back", discord.ButtonStyle.gray)
                nextButton = PageButton("⇾ Next", discord.ButtonStyle.blurple)
                if pagenum == 0:
                    backButton.disabled = True
                if pagenum == totpage - 1:
                    nextButton.disabled = True
                self.add_item(backButton)
                self.add_item(nextButton)
                
        else:
            if allLists.private:
                self.add_item(discord.ui.Button(emoji="<:white_check:930021702560280596>", label="Open List", style=discord.ButtonStyle.primary, custom_id = "private"))
            if str(ctx.author.id) == allLists.author:
                self.add_item(ScopeSelect(self))
            self.add_item(discord.ui.Button(emoji = "<:confirm:851278899832684564>", label="Close Buttons", style=discord.ButtonStyle.green, custom_id = "done", row=4))
        self.add_item(discord.ui.Button(emoji = "<:cancel:851278899270909993>", label="Exit", style=discord.ButtonStyle.red, custom_id = "cancel", row=4))
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This is not your menu to navigate.", ephemeral= True)
        else:
            selected = list(interaction.data.values())[0]
            if selected == "done":
                await interaction.response.edit_message(view = None)
            elif selected == "cancel":
                self.stop()
                await self.message.delete()
            elif selected == "private":
                await interaction.response.send_message(embed = view(self.allLists), ephemeral=True)
        return await super().interaction_check(interaction)           
    
class ListButton(discord.ui.Button['ListView']):
    def __init__(self, id, title):
        super().__init__(label = title)
        self.listID = id
        
    async def callback(self, interaction: discord.Interaction): 
    #* Appending Extra Buttons  
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
    ## 
        selList = db.query(Lists).filter_by(id = self.listID).first() 
        if selList.private:
            return await interaction.response.send_message(content = "> Here's your private list!", embed = view(selList), view = EphemeralView(self.view, True), ephemeral = True)
        await interaction.response.edit_message(content = "> Here's your list!", embed = view(selList), view = self.view)

class EphemeralView(discord.ui.View):
    def __init__(self, ogView, *arg):
        super().__init__()
        self.ogView = ogView
        self.add_item(ScopeSelect(ogView, *arg))
        self.add_item(discord.ui.Button(emoji = "<:confirm:851278899832684564>", label="Close Buttons", style=discord.ButtonStyle.green, custom_id = "done", row=4))
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        selected = list(interaction.data.values())[0]
        if selected == "done":
            await interaction.response.edit_message(view = None)

        return await super().interaction_check(interaction)  
    
class PageButton(discord.ui.Button['ListView']):
    def __init__(self, label, style):
        super().__init__(label = label, style = style, row = 4)
        
    async def callback(self, interaction:discord.Interaction):
        pagenum = self.view.pagenum
        if self.label == "⇽ Back":
            pagenum -= 1
        else:
            pagenum += 1
        if isinstance(self.view, ListView):
            newView = ListView(self.view.ctx, self.view.bot, self.view.allLists, pagenum, self.view.totpage)
        elif isinstance(self.view, CompleteView):
            newView = CompleteView(self.view.ctx, self.view.bot, self.view.selList, self.view.allTasks, pagenum, self.view.totpage)
        elif isinstance(self.view, RemoveView):
            newView = RemoveView(self.view.ctx, self.view.bot, self.view.selList, self.view.dupList, self.view.allTasks, pagenum, self.view.totpage)
        newView.message = self.view.message
        await interaction.response.edit_message(view=newView)
        
class ListSettings(discord.ui.View):
    def __init__(self, ogView):
        super().__init__()
        self.ogView = ogView
        self.add_item(ScopeSelect(ogView))
        
    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.ogView.ctx.author.id:
            await interaction.response.send_message("This is not your menu to navigate.", ephemeral= True)  
            return False
        else:
            return await super().interaction_check(interaction)
        
    @discord.ui.button(emoji="✏", label="Rename List", style=discord.ButtonStyle.gray)
    async def edit(self, interaction: discord.Interaction, button: discord.ui.button):
        await interaction.response.defer()
        await self.ogView.message.delete()
        newctx = self.ogView.ctx
        newctx.invoked_with = 'rename'
        listID = str(interaction.message.embeds[0].footer.text).split(" ")[-1]
        await self.ogView.bot._list.get_command('rename')(self.ogView.ctx, title=":" + listID)
        
    # @discord.ui.button(emoji="🙈", label="Toggle Visibility", style=discord.ButtonStyle.gray)
    # async def hide(self, button: discord.ui.button, interaction: discord.Interaction):
    #     title = interaction.message.embeds[0].title
    #     selList = db.query(Lists).filter_by(title = title).first()
    #     if not selList.private:
    #         newctx = self.ogView.ctx
    #         newctx.invoked_with = 'hide'
    #         await self.ogView.bot._list.get_command('hide')(ctx=self.ogView.ctx, title=title)
    #     else:
    #         newctx = self.ogView.ctx
    #         newctx.invoked_with = 'show'
    #         await self.ogView.bot._list.get_command('show')(ctx=self.ogView.ctx, title=title)
    #     await self.ogView.message.delete()
        
    @discord.ui.button(emoji="<:trash:926991605615960064>", label="Delete List", style=discord.ButtonStyle.red)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.button):
        await self.ogView.message.delete()
        newctx = self.ogView.ctx
        newctx.invoked_with = 'delete_list'
        listID = str(interaction.message.embeds[0].footer.text).split(" ")[-1]
        await self.ogView.bot._list.get_command('delete_list')(self.ogView.ctx, title=":" + listID) #using a weird pound to avoid people who may use it in their title
        
class TaskSettings(discord.ui.View):
    def __init__(self, ogView):
        super().__init__()
        self.ogView = ogView
        self.add_item(ScopeSelect(ogView))
        
    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.ogView.ctx.author.id:
            await interaction.response.send_message("This is not your menu to navigate.", ephemeral= True)  
            return False
        else:
            return await super().interaction_check(interaction)
            
    @discord.ui.button(emoji="<:check:926281518266073088>", label="Change Task Status", style=discord.ButtonStyle.green)
    async def status(self, interaction: discord.Interaction, button: discord.ui.button):
        await self.ogView.message.delete()
        newctx = self.ogView.ctx
        newctx.invoked_with = 'complete'
        await self.ogView.bot.tasks.get_command('complete')(self.ogView.ctx, title=interaction.message.embeds[0].title)
        
    @discord.ui.button(emoji="➕", label="Add Task", style=discord.ButtonStyle.primary)
    async def add(self, interaction: discord.Interaction, button: discord.ui.button):
        await interaction.response.defer()
        await self.ogView.message.delete()
        newctx = self.ogView.ctx
        newctx.invoked_with = 'add'
        await self.ogView.bot.tasks.get_command('add')(self.ogView.ctx, inp=interaction.message.embeds[0].title)
        
    @discord.ui.button(emoji="<:cross:926283850882088990>", label="Remove Task", style=discord.ButtonStyle.red)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.button):
        await self.ogView.message.delete()
        newctx = self.ogView.ctx
        newctx.invoked_with = 'delete_task'
        await self.ogView.bot.tasks.get_command('delete_task')(self.ogView.ctx, title=interaction.message.embeds[0].title)

class PrivateView(discord.ui.View):
    def __init__(self, ctx, selList):
        super().__init__()
        self.ctx = ctx
        self.selList = selList
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This is not your menu to navigate.", ephemeral= True)
            return False
        else:
            return await super().interaction_check(interaction) 
        
    @discord.ui.button(emoji="<:white_check:930021702560280596>", label="Open List", style=discord.ButtonStyle.primary)
    async def open(self, interaction: discord.Interaction, button: discord.ui.button):
        await interaction.response.send_message(embed = view(self.selList), ephemeral = True)
    
    @discord.ui.button(emoji = "<:cancel:851278899270909993>", label="Exit", style=discord.ButtonStyle.red, custom_id = "cancel", row=4)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.button):
        await self.message.delete()
        
class CompleteView(discord.ui.View):
    def __init__(self, ctx, bot, selList, allTasks, pagenum, totpage):
        super().__init__()
        self.ctx = ctx
        self.bot = bot
        self.selList = selList
        self.allTasks = allTasks
        self.pagenum = pagenum
        self.totpage = totpage
        
        for task in allTasks[pagenum]:
            if task.status == "<:check:926281518266073088>":
                style = discord.ButtonStyle.green
            elif task.status == "<:wip:926281721224265728>":
                style = discord.ButtonStyle.blurple
            else:
                style = discord.ButtonStyle.secondary
            self.add_item(CompleteButtons(task.status, task.number, style))
            
        if totpage > 1:                            
            backButton = PageButton("⇽ Back", discord.ButtonStyle.gray)
            nextButton = PageButton("⇾ Next", discord.ButtonStyle.blurple)
            if pagenum == 0:
                backButton.disabled = True
            if pagenum == totpage - 1:
                nextButton.disabled = True
            self.add_item(backButton)
            self.add_item(nextButton)
        
        self.add_item(ScopeSelect(self))
        self.add_item(discord.ui.Button(emoji = "<:cancel:851278899270909993>", label="Exit", style=discord.ButtonStyle.red, custom_id = "cancel", row=4))
        self.add_item(discord.ui.Button(emoji = "<:confirm:851278899832684564>", label="Close Buttons", style=discord.ButtonStyle.green, custom_id = "done", row=4))
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This is not your menu to navigate.", ephemeral= True)
        else:
            selected = list(interaction.data.values())[0]
            if selected == "done":
                await interaction.response.edit_message(view = None)
            elif selected == "cancel":
                self.stop()
                await self.message.delete()
        return await super().interaction_check(interaction)      
     
class CompleteButtons(discord.ui.Button):
    def __init__(self, emoji, label, style):
        super().__init__(emoji = emoji, label = label, style = style)
        
    async def callback(self, interaction: discord.Interaction):  
        selTask = self.view.allTasks[self.view.pagenum][(int(self.label) - (self.view.pagenum*tasksPerPage)) - 1]
        
        if selTask.status == "<:check:926281518266073088>":
            selTask.taskItem = selTask.taskItem.replace("~", "*")
            selTask.status = "<:wip:926281721224265728>"
        elif selTask.status == "<:wip:926281721224265728>":
            selTask.taskItem = selTask.taskItem.replace("*", "")
            selTask.status = "<:notdone:926280852856504370>"
        else:
            selTask.taskItem = f"~~{selTask.taskItem}~~"
            selTask.status = "<:check:926281518266073088>"
        db.commit()
        
        checkoffView =  CompleteView(self.view.ctx, self.view.bot, self.view.selList, self.view.allTasks, self.view.pagenum, self.view.totpage)
        checkoffView.message = self.view.message
        await interaction.response.edit_message(embed = view(self.view.selList, True), view = checkoffView)
        
class RemoveView(discord.ui.View):
    def __init__(self, ctx, bot, selList, dupList, allTasks, pagenum, totpage):
        super().__init__()
        self.ctx = ctx
        self.bot = bot
        self.selList = selList
        self.dupList = dupList
        self.allTasks = allTasks
        self.pagenum = pagenum
        self.totpage = totpage
    
        for task in allTasks[pagenum]:
            if task.status == "<:check:926281518266073088>":
                style = discord.ButtonStyle.green
            elif task.status == "<:wip:926281721224265728>":
                style = discord.ButtonStyle.blurple
            elif task.status == "<:cross:926283850882088990>":
                style = discord.ButtonStyle.red
            else:
                style = discord.ButtonStyle.secondary
            self.add_item(RemoveButtons(task.status, task.number, style))
        #* Page turning
        if totpage > 1:                            
            backButton = PageButton("⇽ Back", discord.ButtonStyle.gray)
            nextButton = PageButton("⇾ Next", discord.ButtonStyle.blurple)
            if pagenum == 0:
                backButton.disabled = True
            if pagenum == totpage - 1:
                nextButton.disabled = True
            self.add_item(backButton)
            self.add_item(nextButton)
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This is not your menu to navigate.", ephemeral= True)
            return False
        else:
            return await super().interaction_check(interaction)   
    
    @discord.ui.button(emoji = "<:cancel:851278899270909993>", label="Exit", style=discord.ButtonStyle.red, custom_id = "cancel", row=4)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.button):
        await self.message.delete()
        db.delete(self.dupList)
        db.commit()
        
    @discord.ui.button(emoji = "<:white_check:930021702560280596>", label="Save Changes", style=discord.ButtonStyle.primary, custom_id = "save", row=4)
    async def save(self, interaction: discord.Interaction, button: discord.ui.button):
        sel_taskList = sorted(self.selList.rel_tasks, key = lambda task: task.number)
        dup_taskList = sorted(self.dupList.rel_tasks, key = lambda task: task.number)
        i = 1 #needs to be outside the for loop
        for dup_task, sel_task in zip(dup_taskList, sel_taskList):
            if dup_task.status == "<:cross:926283850882088990>":
                self.selList.rel_tasks.remove(sel_task)
                continue
            sel_task.number = i 
            i += 1
        
        db.delete(self.dupList)
        db.commit()
        await interaction.response.edit_message(content = "Changes Saved!", embed = view(self.selList), view = None)
        
class RemoveButtons(discord.ui.Button):
    def __init__(self, emoji, label, style):
        super().__init__(emoji = emoji, label = label, style = style)
        
    async def callback(self, interaction: discord.Interaction):  
        dupTask = self.view.allTasks[self.view.pagenum][(int(self.label) - (self.view.pagenum*tasksPerPage)) - 1]
        selTask = db.query(Tasks).filter_by(listID = self.view.selList.id).filter_by(number = self.label).first()

        if dupTask.status == "<:cross:926283850882088990>":
            dupTask.status = selTask.status
        else:
            dupTask.status = "<:cross:926283850882088990>"
        db.commit()
       
        delete_taskView =  RemoveView(self.view.ctx, self.view.bot, self.view.selList, self.view.dupList, self.view.allTasks, self.view.pagenum, self.view.totpage)
        delete_taskView.message = self.view.message
        await interaction.response.edit_message(embed = view(self.view.dupList, True), view = delete_taskView)

class ScopeSelect(discord.ui.Select):
    def __init__(self, ogView, *arg):
        self.listOption = discord.SelectOption(label="List Settings", emoji="<:list:927096692069789696>")
        self.taskOption = discord.SelectOption(label="Task Settings", emoji="<:notdone:926280852856504370>")
        self.backOption = discord.SelectOption(label="Go Back", emoji="⬅️")
        self.oldView = ogView
        options = [self.listOption, self.taskOption, self.backOption]
        if arg:
            options = [self.listOption, self.taskOption]            
        
        super().__init__(placeholder = "Select between List and Task Settings",
                         options = options, custom_id="menu")

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
        
    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        print("clipboard is Ready")
        
    @commands.group(aliases = ["checklist", "clipboard", "l", "list", "lists"])
    async def _list(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(f"Please specify what you'd like to do. \nEx: `{ctx.prefix}list create` \nSee `{ctx.prefix}list help` for a list of examples!")

    @commands.group(aliases = ["n", "notes"])
    async def note(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(f"Note subcommands are wip, use `{ctx.prefix}list create` to create lists instead")
            
    @commands.group(aliases = ["t", "task"])
    async def tasks(self, ctx):
        if ctx.invoked_subcommand is None:
            allLists = db.query(Lists).filter_by(author = str(ctx.author.id)).all()
            if allLists:
                titlesOnly = [lists.title for lists in allLists]
                await ctx.send(f"Available lists: {', '.join(titlesOnly)} \nUse `{ctx.prefix}task <command> <list>` to continue \nFor more help refer to `{ctx.prefix}list help`")
            else:
                "You have no lists! Create a list before completing tasks: `{ctx.prefix}list create`"
           
        
           
            

#* -------    Help Command   -------
    @_list.command(aliases = ["h"])
    async def help(self, ctx):
        embed = discord.Embed(
            title = "Help Menu",
            description =
            f"""
            Any <> should be ignored when using the command. 
            \nEx) `{ctx.prefix}list view <title>` 
            ⤷ `{ctx.prefix}list view YourCoolListHere`\n
            [`{ctx.prefix}list`](https://imgur.com/DI7IQcn \"Aliases: checklist, clipboard, l\") ➙ The start of any list related command
            [`{ctx.prefix}list make`](https://imgur.com/DI7IQcn \"Aliases: create, new, c, m\") ➙ Guides you through making a list
            [`{ctx.prefix}list view <title>`](https://imgur.com/DI7IQcn \"Aliases: open, browse, b, v \") ➙ Brings up editing menu for that list
            ⤷ `{ctx.prefix}list view {override}<author's username>` 
            ⤷ `{ctx.prefix}list view {override}GracefulLion`
            [`{ctx.prefix}list rename <title> {override} <newtitle>`](http://www.howardhallis.com/tpoe/noflash.html \"Aliases: r\")
            [`{ctx.prefix}list delete <title>`](https://imgur.com/DI7IQcn \"Aliases: d\") 
            ⤷ `{ctx.prefix}list delete {override}<title>` ➙ to override the confirmation menu 
            ⤷ `{ctx.prefix}list delete :<ListID>`
            `{ctx.prefix}list show/hide <title>` ➙ WIP, allows you to mark a list as private so that only you can see it. I don't recommend marking lists as private yet.
            
            `{ctx.prefix}list override` ➙ Return current override for server
            `{ctx.prefix}list override <new override>` ➙ The current override symbol is set to `{override}`
            """,
            color = randomHexGen()
        ) 
        embed.add_field(name="Task Commands", 
        value=f"""
        [`{ctx.prefix}task`](https://imgur.com/DI7IQcn \"Aliases: t\") ➙ Lists available list titles as a shortcut to task completion
        [`{ctx.prefix}task add <title>`](https://imgur.com/DI7IQcn \"Aliases: a\") 
        [`{ctx.prefix}task remove <title>`](https://imgur.com/DI7IQcn \"Aliases: r\")
        [`{ctx.prefix}task complete <title>`](https://imgur.com/DI7IQcn \"Aliases: checkoff, c\")
        """)
        embed.set_footer(text=f"Tip: Don't use your override symbol in your List titles")
        await ctx.send(embed = embed)

#*  --------------------- LIST COMMANDS --------------------------- 
#* -------    List Creation   -------
    @_list.command(aliases = ["create", "new", "c", "m"])
    async def make(self, ctx, *, title=None):
        member = ctx.guild.get_member(ctx.author.id)
        try: pfp = member.avatar.url
        except: pfp = None

        embed = discord.Embed (
            title = "Checklist Creation",
            description = "",
            color = randomHexGen()
        )
        view = Cancel(ctx)
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
        embed.set_author(name="List is Public")
        view = Confirm(ctx)
        confirmationEmbed = await ctx.send(f"> Does this look correct? • [{member}]", embed = embed, view=view)
    ##
        await view.wait()
        if view.value is None:
            embed.description = "Confirmation menu timed out!"
            return await confirmationEmbed.edit(embed = embed, view = None, delete_after = 3)
        elif view.value:
            _list = Lists(title = title, author = str(ctx.author.id), author_name = member.name)
            db.add(_list)
            for task in enumerate(taskList, start=1):
                newTask = Tasks(listID = _list.id, taskItem = task[1], number = task[0])
                db.add(newTask)
                _list.rel_tasks.append(newTask)

            db.commit()
            return await confirmationEmbed.edit(content="Saved to Database!", embed = embed, view = None)
        else:
            embed.description = "List canceled!"
            return await confirmationEmbed.edit(embed = embed, view = None, delete_after = 5)

#* Select your lists (allows for looser searches)
    @_list.command(aliases = ["b", "view", "v"])
    async def browse(self, ctx, *, filterOption=None, pagenum = 0): #pagenum starts at 0
        member = ctx.guild.get_member(ctx.author.id)
    
        if filterOption is None:
            allLists = db.query(Lists).filter_by(author = str(ctx.author.id)).all()
        else: # given argument search for
            if "^" in filterOption:
                allLists = db.query(Lists).filter(Lists.author_name.like(f'{filterOption.replace("^", "")}%')).all()
            else: 
                allLists = db.query(Lists).filter(Lists.title.like(f'{filterOption}%')).all()            
        
        if allLists:
            if len(allLists) == 1:
                viewListObject = ListView(ctx, self, allLists = allLists[0], pagenum = 0, totpage = 1)
                if allLists[0].private:
                    if allLists[0].author != str(ctx.author.id):
                        invoke = str(ctx.invoked_with).replace("_list", "").strip()
                        return await ctx.send(f"You may not `{invoke}` this list because it is private!") 
                    viewListObject.message = await ctx.send(content = f"> {allLists[0].title} • [{member}]", view = viewListObject)
                    return
                viewListObject.message = await ctx.send(embed = view(allLists[0]), view = viewListObject)
                return
            allListsChunked = chunkList(allLists, listsPerPage)
        else:
            return await ctx.send(f"List(s) not found! Create a list using `{ctx.prefix}list create`")
  
        # Allow to select between lists
        viewListObject = ListView(ctx, self, allListsChunked, pagenum, len(allListsChunked))
        viewListObject.message = await ctx.send(f"> Choose a list to view! • [{member}]", view = viewListObject)

#* List view admin 
    @commands.is_owner()
    @_list.command(aliases = ["@view"])
    async def _view_admin(self, ctx, pagenum=0):
        allLists = db.query(Lists).all()
        if allLists:
            allListsChunked = chunkList(allLists, listsPerPage)
        else:
            return await ctx.send(f"List(s) not found! Create a list using `{ctx.prefix}list create`")
        viewListObject = ListView(ctx, self, allListsChunked, pagenum, len(allListsChunked))
        viewListObject.message = await ctx.send(f"Viewing all possible lists", view = viewListObject)

#* Delete a List
    @_list.command(aliases = ["remove", "delete", "d"])
    async def delete_list(self, ctx, *, title):
        member = ctx.guild.get_member(ctx.author.id)

        #Delete from Menu (you must own the list to click the delete button)
        if ":" == title[0]:
            selList = _overrideOwner_ByID(self, ctx, title.replace(":", "").strip())
        else: #Deleting from command
            selList = _checkOwner_Exists(self, ctx, title.replace(override, "")) #does this list exist? and are you the owner?
        if isinstance(selList, str):
            return await ctx.send(selList)

        if override not in title:
            confirmView = Confirm(ctx)
            confirmationEmbed = await ctx.send(f"> Are you sure you want to delete this list? • [{member}]", embed = view(selList), view = confirmView)
            await confirmView.wait()
            if confirmView.value is None:
                await ctx.send("Confirmation menu timed out!", delete_after = 5)
            elif confirmView.value:
                db.delete(selList)
                db.commit()
                await ctx.send("Database Updated!", delete_after = 5)
            else:
                await ctx.send("Confirmation menu canceled!", delete_after = 5)
            await confirmationEmbed.delete()
        else:
            db.delete(selList)
            db.commit()
            await ctx.send("Database Updated!", delete_after = 5)
        
#* Renaming Lists
    @_list.command(aliases = ["r"])
    async def rename(self, ctx, *, title):
        member = ctx.guild.get_member(ctx.author.id)

        #Renaming from Menu
        if ":" == title[0]:
            selList = _overrideOwner_ByID(self, ctx, title.replace(":", "").strip())
        else: #renaming from command
            selList = _checkOwner_Exists(self, ctx, title.partition(override)[0].strip()) #does this list exist? and are you the owner?
        if isinstance(selList, str):
            return await ctx.send(selList)
        
        if override not in title:
            cancelView = Cancel(ctx)
            confirmationEmbed = await ctx.send(f"> Please enter your new title for this list • [{member}]", embed = view(selList), view = cancelView)
            newListName = await self.bot.get_command('multi_wait')(ctx, cancelView, 60)
            if not newListName:
                await confirmationEmbed.delete()
                return await ctx.send("Menu canceled", delete_after = 5)
            await confirmationEmbed.delete()
        else:
            newListName = title.split(override)[1].strip()
        
        selList.title = newListName   
        db.commit()
        await ctx.send(f"> List successfully renamed! • [{member}]", embed = view(selList))

#* Hiding Lists
    @_list.command()
    async def hide(self, ctx, *, title):    
        member = ctx.guild.get_member(ctx.author.id)   
        selList = _checkOwner_Exists(self, ctx, title) #does this list exist? and are you the owner?
        if isinstance(selList, str):
            return await ctx.send(selList)

        selList.private = True
        db.commit()
        await ctx.send(f"List successfully marked private! • [{member}]", delete_after = 5)
        
    @_list.command()
    async def show(self, ctx, *, title):    
        member = ctx.guild.get_member(ctx.author.id)   
        selList = _checkOwner_Exists(self, ctx, title) #does this list exist? and are you the owner?
        if isinstance(selList, str):
            return await ctx.send(selList)

        selList.private = False
        db.commit()
        await ctx.send(f"List successfully marked public! • [{member}]", delete_after = 5)
         
#*  --------------------- TASK COMMANDS ---------------------------         
#* Mark Tasks as complete
    @tasks.command(aliases = ["checkoff", "c"])
    async def complete(self, ctx, *, title: str, pagenum = 0):
        member = ctx.guild.get_member(ctx.author.id)
        selList = _checkOwner_Exists(self, ctx, title) #does this list exist? and are you the owner?
        if isinstance(selList, str):
            return await ctx.send(selList)
        
        taskList = sorted(selList.rel_tasks, key = lambda task: task.number)
        taskListChunked = chunkList(taskList, tasksPerPage)
        
        checkView = CompleteView(ctx, self.bot, selList, taskListChunked, pagenum, len(taskListChunked))
        if selList.private:
            checkView.message = await ctx.send(content = f"> {selList.title} • [{member}]", view = checkView)
        else:
            checkView.message = await ctx.send(embed = view(selList, True), view = checkView)
        
#* Add a Task to a List
    @tasks.command(aliases = ["a", "add"])
    async def task_add(self, ctx, *, inp):    
        member = ctx.guild.get_member(ctx.author.id)   
        title = re.match(r"\A.*", inp).group()
        selList = _checkOwner_Exists(self, ctx, title) #does this list exist? and are you the owner?
        if isinstance(selList, str):
            return await ctx.send(selList)
        
        if "\n" not in inp: 
            cancelView = Cancel(ctx) 
            tasksPrompt = await ctx.send(f"Enter the tasks you wish to add separated by *new lines* \nThis question will time out in `6 minutes`", view = cancelView)
            taskString = await self.bot.get_command('multi_wait')(ctx, cancelView, 400)
            if not taskString:
                await tasksPrompt.delete()
                return await ctx.send("Adding tasks canceled.", delete_after = 5)
            await tasksPrompt.delete()
            taskList = (re.sub('\n- |\n-|\n• |\n•', '\n', taskString)).split("\n")
        else:
            taskList = (re.sub('\n- |\n-|\n• |\n•', '\n', inp)).split("\n")[1:] #turn into a list
            
        for task in enumerate(taskList, start = len(selList.rel_tasks)+1):
            newTask = Tasks(listID = selList.id, taskItem = task[1], number = task[0])
            db.add(newTask)
            selList.rel_tasks.append(newTask)
            
        db.commit()
        await ctx.send(f"Tasks Successfully Added! • [{member}]", embed = view(selList))
  
#* Remove a Task from a list 
    @tasks.command(aliases = ["remove", "delete", "d"])
    async def delete_task(self, ctx, *, title, pagenum = 0):    
        selList = _checkOwner_Exists(self, ctx, title) #does this list exist? and are you the owner?
        if isinstance(selList, str):
            return await ctx.send(selList)
        dupList = Lists(title = "&" + selList.title, author = "0", author_name = "0")
        db.add(dupList)
        for task in selList.rel_tasks:
            newTask = Tasks(listID = dupList.id, taskItem = task.taskItem, number = task.number, status = task.status)
            db.add(newTask)
            dupList.rel_tasks.append(newTask)
        db.commit() 
        
        taskList = sorted(dupList.rel_tasks, key = lambda task: task.number)
        taskListChunked = chunkList(taskList, tasksPerPage)
        deleteTasksView = RemoveView(ctx, self, selList, dupList, taskListChunked, pagenum, len(taskListChunked))
        deleteTasksView.message = await ctx.send(embed = view(dupList, True), view = deleteTasksView)
   
#* Error Handling for missing Title
    @rename.error
    @delete_task.error
    @delete_list.error
    @complete.error
    @hide.error
    @show.error
    async def _error_handler(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'title':
                invoke = str(ctx.invoked_with).replace("_list", "").strip()
                await ctx.send(f"You must specify what list you would like to `{invoke}`. \nTry `{ctx.prefix}{ctx.invoked_parents[0]} {invoke} <title>`.")  
        else:
            print(error)
            
#* View one list (does not allow for editing list)
    @commands.command(aliases = ["view", "o"]) # command that is not nested in the Note Group
    async def open(self, ctx, *, title=None):
        member = ctx.guild.get_member(ctx.author.id)   
        if title is None:
            await self._list.get_command('browse')(ctx, pagenum = 0)

        else:
            selList = _checkOwner_Exists(self, ctx, title) #does this list exist? and are you the owner?
            if isinstance(selList, str):
                return await ctx.send(selList)
            
            if selList.private:
                privView = PrivateView(ctx, selList)
                privView.message = await ctx.send(f"> {selList.title} • [{member}]", view = privView)
                return                
            await ctx.send(embed = view(selList))  

#* Other Commands
    @_list.command()
    async def recreate(self, ctx):
        recreate()
        await ctx.send("Database recreated")
        
    @_list.command()
    async def override(self, ctx, *, symbol = None):
        global override
        if symbol:
            override = symbol
            await ctx.send("Your new override symbol is " + override)
        else:
            await ctx.send("Your current override symbol is " + override)       
            
    @_list.command()
    async def example(self, ctx):
        await ctx.guild.get_member(ctx.author.id).send("https://imgur.com/DI7IQcn")

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
        title = selList.title.replace("^", ""),
        description = f"\n".join(taskList),
        color = 0x2F3136,
        timestamp = selList.created
    )
    embed.set_author(name="Private List" if selList.private else "Public List")
    embed.set_footer(text = f"Created by {selList.author_name} | List ID: {selList.id}")
    return embed

def chunkList(queryList, n): #chunk a list into lists of n size
    queryList = [queryList[i:i + n] for i in range(0, len(queryList), n)]
    return queryList
    
def _checkOwner_Exists(self, ctx, input_title):
    selList = db.query(Lists).filter(Lists.title.ilike(input_title)).all()
    output = "Error!"
    if not selList:
        return f"No lists were found with name: `{input_title}`!"
    for _list in selList:
        if _list.author != str(ctx.author.id):
            invoke = str(ctx.invoked_with).replace("_list", "").strip()
            output = f"You may not `{invoke}` this list because you do not own it!"
        else:
            return _list
    return output

def _overrideOwner_ByID(self, ctx, listID):
    selList = db.query(Lists).filter_by(id = listID).first()
    output = "Error!"
    if not selList:
        return f"No lists were found with ID: `{listID}`!"
    if selList.author == str(ctx.author.id) or ctx.author.id == self.bot.owner_id:
        return selList
    invoke = str(ctx.invoked_with).replace("_list", "").strip()
    output = f"You may not `{invoke}` this list because you do not own it!"
    return output

async def setup(bot):
    await bot.add_cog(clipboard(bot))
