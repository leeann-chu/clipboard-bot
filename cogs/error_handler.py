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
        if hasattr(ctx.command, 'on_error'):
            return
        
        if ctx.author == self.bot.user:
            return
        if hasattr(ctx.command, 'on_error'):
            return

        ignored = (commands.CommandNotFound, )
        error = getattr(error, 'original', error)
        message = ctx.message
        member = ctx.message.author

        if isinstance(error, ignored):
            if message.content.startswith('~help'):
                return
            elif message.content.startswith('~~'):
                return
            await ctx.send(f"Unknown command: `{message.content}`. Use `{ctx.prefix}help` for list of commands")
            return

        elif isinstance(error, commands.errors.NotOwner):
            await ctx.send("Nice Try.")
            return

        elif isinstance(error, commands.BadArgument):
            if ctx.command.qualified_name == 'tag list':
                await ctx.send('I could not find that member. Please try again.')

        elif isinstance(error, commands.MissingRequiredArgument):
            # print('This is a different error message {}:'.format(ctx.command), file=sys.stderr)
            # traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
            await ctx.send(f"{member.display_name} you forgot to include a parameter! Use `{ctx.prefix}help` for list of commands")
    
        else:
            print(f'This is a different error message {ctx.command}:', file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

async def setup(bot):
    await bot.add_cog(CommandErrorHandler(bot))