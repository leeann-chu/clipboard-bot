from discord.ext import tasks
import json
import os
import sys
import asyncio
import psutil
# from myutils.poll_class import readfromFile, writetoFile
from discord.ext import commands
import discord, traceback
from main import randomHexGen, get_prefix
from myutils.views import Confirm, ResponseView, PrefixModal

def restart_program():
    python = sys.executable
    os.execl(python, python, * sys.argv)

class utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        print("utilities is Ready")

    # never full implemented, not fully sure how to pass ctx without triggering the command
    # manually. would like to auto start this when bot starts but not sure how to achieve that
    @tasks.loop(hours=3)
    async def watch_battery_task(self):
        battery = psutil.sensors_battery()
        await self.bot.get_channel(809686249999826955).send(battery.percent)

    #➥ Server prefix set command
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def prefix(self, ctx):
        prefixList = get_prefix(self.bot, ctx.message) # necessary for the whole list instead of the one in current use
        embed = discord.Embed(
            title = "Changing Server Prefix",
            description = f"The **current** standard prefix is `{prefixList[0]}`",
            color = randomHexGen()
        )
        # could add the ability to edit personal prefix. personally that's too much work but i could
        response_view = ResponseView(ctx, "Change Prefix", PrefixModal(embed)) # view that holds modal
        response_view.message = await ctx.send(embed = embed, view = response_view)

    @prefix.error
    async def prefix_error(self, ctx, error):
        member = ctx.message.author
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f"sorry {member.display_name}, you are not powerful enough to edit the server prefix!", delete_after = 3)
        else:
            print(traceback.format_exc())
    ##

    @commands.command()
    @commands.is_owner()
    async def emoji_msg_error_check(self, ctx, emojiList, msgList):
        success = True
        if len(emojiList) > 25:
            print("emojilist is > 25")
            await ctx.send("Polls may only have up to 24 options. Try making the Poll again.")
            success = False
        elif len(emojiList) != len(msgList):
            print(emojiList)
            print(msgList)
            print("emoji list is not == optionlist")
            await ctx.send("You have an unmatched number of options and emojis. Try making the Poll again.")
            success = False
            
        return emojiList, msgList, success

    #➥ Clear Command and Error
    @commands.command(aliases=["purge", "c"])
    @commands.has_permissions(manage_guild=True)
    async def clear(self, ctx, amount: int = 10, override = None):
        if override is None:
            view = Confirm(ctx)
            msg = await ctx.send(f"Clear {amount} messages?", view = view)
            await view.wait()
            if view.value is None:
                return await ctx.send("Confirmation menu timed out!", delete_after = 3)
            elif view.value:
                if amount>501 or amount<0:
                    await msg.delete()
                    return await ctx.send("Invalid amount. Maximum is 500", delete_after = 3)
                await msg.delete()
                await ctx.channel.purge(limit = amount + 1)
                await ctx.send(f"Cleared {amount} messages!", delete_after = 3)
            else:
                await msg.delete()
                return await ctx.send("Confirmation menu canceled", delete_after = 3)
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
        else:
            await ctx.send("It's highly probable the bot does not have the permissions to fulfil your wishes, sorry")
    ##

    # clear any json Dictionary (used for emoji_count and member)
    @commands.command()
    @commands.is_owner()
    async def clear_dictionary(self, ctx, dictionary: str):
        try:
            os.remove(f'data/{dictionary}.json')
        except OSError:
            await ctx.send("Dictionary not found, options: emoji_count and member_emoji")
            return
        
        with open(f'data/{dictionary}.json', 'x') as f:
            json.dump({}, f,  indent=4)
            await ctx.send("Successfully cleared dictionary!")            

    #➥ waitfor command — Depreciated
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
            return await ctx.send("You took too long, try again! ", delete_after = 5)
    ##

    #➥ multi_wait command — Depreciated 
    @commands.command()
    @commands.is_owner()
    async def multi_wait(self, ctx, view, timeout):
        # asyncio magic?
        done, pending = await asyncio.wait([
                            self.waitCheck(ctx, timeout), 
                            view.wait()], # broken
                            timeout = timeout,
                            return_when = asyncio.FIRST_COMPLETED)
        try:
            stuff = done.pop().result()
            if isinstance(stuff, str):
                return stuff
            else:
                pending.pop().cancel()
                return None
        except KeyError:
            await ctx.send("You took too long, try again!", delete_after = 5)
        except Exception as e:
            print(e)

        for future in done:
            print("more errors?")
            future.exception()
        for future in pending:
            future.cancel()
    ##

    @commands.command()
    @commands.is_owner()
    async def restart(self, ctx):
        await ctx.message.delete()
        message = await ctx.send("Restarting... Allow up to 20 seconds")
        restart_program()

    @commands.command()
    @commands.is_owner()
    async def battery_watch(self, ctx, enabled):
        if enabled == "start":
            if not self.watch_battery_task.is_running():
                await ctx.send("Begining watch")
                self.watch_battery_task.start()
            else:
                await ctx.send("No need silly! Already have my eye on it ;)")
        elif enabled == "stop":
            if self.watch_battery_task.is_running():
                print("Ending watch")
                self.watch_battery_task.cancel()
                await ctx.send("No longer watching battery")

async def setup(bot):
    await bot.add_cog(utilities(bot))