import discord
import traceback
import sys
from discord.ext import commands

class CommandErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        print("error_handler is Ready")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        # prefix = get_prefix(self.bot, ctx)
        if ctx.author == self.bot.user:
            return
        if hasattr(ctx.command, 'on_error'):
            return
        cog = ctx.cog
        if cog:
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                return

        ignored = (commands.CommandNotFound, )
        error = getattr(error, 'original', error)
        message = ctx.message

        if isinstance(error, ignored):
            if message.content.startswith('~help'):
                return
            await ctx.send(f"Unknown command `{message.content}`." + " Type `{0.prefix}chelp` for list of commands".format(ctx))
            return

        elif isinstance(error, commands.BadArgument):
            if ctx.command.qualified_name == 'tag list':
                await ctx.send('I could not find that member. Please try again.')

        else:
            print('This is a different error message {}:'.format(ctx.command), file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
#➥ Repeat Command
    @commands.command(name='repeat', aliases=['mimic', 'copy'])
    async def do_repeat(self, ctx, *, inp: str):
        await ctx.send(inp)

    @do_repeat.error
    async def do_repeat_handler(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'inp':
                await ctx.send("You forgot to give me input to repeat!")
##

def setup(bot):
    bot.add_cog(CommandErrorHandler(bot))