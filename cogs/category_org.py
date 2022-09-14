import discord
from discord.ext import commands
from discord.ext.commands import TextChannelConverter, CategoryChannelConverter, RoleConverter

class category_org(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        print("category_org is Ready")

    # Send list of channels to another category
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def massmove(self, ctx, *, category_channel):
        category, channels = category_channel.split("\n")
        category_obj = await CategoryChannelConverter().convert(ctx, category)
    
        for channel in channels.split(" "):
            channel_obj = await TextChannelConverter().convert(ctx, channel)
            await channel_obj.edit(category=category_obj)

    @massmove.error
    async def massmove_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(error)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Make sure you're following the correct syntax: \n```{ctx.prefix}massmove <category_id> \n #text-channel #text-channel ...```")
        else:
            await ctx.send(error)

    # Mass change channel permissions <- should not delete perms already there
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def masspermit(self, ctx, *, category_role_channel):
        category, role, boolean = category_role_channel.split("\n")
        category_obj = await CategoryChannelConverter().convert(ctx, category)
        
        for channel in category_obj.channels:
            if role == "": #If role left empty match channel name
                role_obj = await RoleConverter().convert(ctx, channel.name)
            else: #If role given edit perms for given role
                role_obj = await RoleConverter().convert(ctx, role.strip())

            over = channel.overwrites_for(role_obj)
            over.read_messages = True if boolean.lower() == "true" else False
            await channel.set_permissions(role_obj, overwrite=over)

        await ctx.send(f"Permissions for channels in {category_obj} changed")

    @masspermit.error
    async def masspermit_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Make sure you're following the correct syntax: \n```{ctx.prefix}masspermit <category_id> \n@role_name \n<boolean>```")
        else:
            await ctx.send(error)

    # Mass change channel permissions to match role name and makes channel private
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def massmatch(self, ctx, *, category):
        category_obj = await CategoryChannelConverter().convert(ctx, category)
        for channel in category_obj.channels:
            role_obj = await RoleConverter().convert(ctx, channel.name)            
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite (
                    read_messages = False
                ),
                role_obj: discord.PermissionOverwrite (
                    read_messages = True, )}
            await channel.edit(overwrites=overwrites)

        await ctx.send(f"Permissions for channels in {category_obj} changed")

    @massmatch.error
    async def massmatch_error(self, ctx, error):
        await ctx.send(error)

async def setup(bot):
    await bot.add_cog(category_org(bot))