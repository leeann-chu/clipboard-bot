import discord
import csv
import random
from discord.ext import commands
from discord.ext.commands import TextChannelConverter, VoiceChannelConverter, CategoryChannelConverter, RoleConverter

#remember to save your csv without the UTF encoding
channel_id = {
    "icon_idea"          : "370200859675721732",
    "general_category"   : "370200859675721730",
    "voice_category"     : "370200859675721734",
    "gaming_category"    : "966833708189487165",
    "interests_category" : "811036378501873695",
    "nsfw_category"      : "966833499166343198",
    "general"            : "370200859675721732",
    "memes"              : "370260333425721347",
    "art"                : "370260576192036865",
    "counting"           : "388542578779226112",
    "bot"                : "388133097851453440",
    "general_vc"         : "878073222178959370",
    "virgin_vc"          : "485329660062728212",
    "chad_vc"            : "485329708033114113",
    "afk_vc"             : "388493850563575818",
    "vidya"              : "464281055466225664",
    "pets"               : "829568327915405323",
    "minecraft"          : "716338107594702919",
    "tech"               : "869235656365318185",
    "politics"           : "813943234110685234",
    "guns"               : "456508133913788436",
    "fit"                : "962927526550851614",
    "documents"          : "811036333962559500",
    "cooking"            : "1030154745022787665",
    "anime"   : "377274787740909579",
    "role1"   : "871957977370878052",
    "role2"   : "871958094899462154",
    "role3"   : "871958129666060298",
    "role4"   : "871958159168782357",
    "botrole" : "388833071908257793"
}

category_list = ["general_category", "voice_category", "gaming_category", "interests_category", "nsfw_category"]
channel_list = ["general", "memes", "art", "counting", "bot", "vidya", "pets", "minecraft", "tech", "politics", "guns", "fit", "documents", "cooking", "anime"]
voice_list = ["general_vc", "virgin_vc", "chad_vc", "afk_vc"]
role_list = ["role1", "role2", "role3", "role4", "botrole"]

def partition (members_list, n):
    random.shuffle(members_list)
    return [members_list[i::n] for i in range(n)]

class category_org(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        print("category_org is Ready")

    # Enforcing Theme Change
    @commands.command() 
    @commands.has_permissions(manage_guild=True)
    async def changeTheme(self, ctx):
        # contents = await ctx.message.attachments[0].read()
        try: await ctx.message.attachments[0].save("data/serverTheme.csv")
        except IndexError:
            return await ctx.send("You forgot to include an attachment!")
        # with open(contents, 'r') as csv_file:
        with open('data/serverTheme.csv', 'r') as csv_file:
            for (default, new) in csv.reader(csv_file):
                default = default.strip(' "\'\t\r\n')
                new = new.strip(' "\'\t\r\n')
                channel_from_dict = channel_id[default]
                if new == "":
                    continue
                if default in channel_list:
                    channel_obj = await TextChannelConverter().convert(ctx, channel_from_dict)
                    await channel_obj.edit(name=new)
                    continue
                if default in role_list:
                    role_obj = await RoleConverter().convert(ctx, channel_from_dict)
                    await role_obj.edit(name=new)
                    continue 
                if default in category_list:
                    category_obj = await CategoryChannelConverter().convert(ctx, channel_from_dict)
                    await category_obj.edit(name=new)
                    continue
                if default in voice_list:
                    vc_obj = await VoiceChannelConverter().convert(ctx, channel_from_dict)
                    await vc_obj.edit(name=new)
                    continue
                if default == "icon_idea":
                    channel_obj = await TextChannelConverter().convert(ctx, channel_from_dict)
                    await channel_obj.send(f"Submitted Icon Prompt: {new}")
                    continue

                await ctx.send(f"Error: `{default}` is unrecognized")

                    # print(f"id: {channel_id[default.strip()]} new: {new.strip()}")
    @changeTheme.error
    async def changeTheme_error(self, ctx, error):
        if isinstance(error, discord.errors.Forbidden):
            await ctx.send(error)
        else:
            await ctx.send(error)
    
    # Shuffle Members
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def shuffleMembers(self, ctx):
        members = [member for member in ctx.guild.members if not member.bot]

        red, yellow, green, blue = partition(members, 4)
        #await ctx.send(f"{red}\n{yellow}\n{green}\n{blue}")

        red_role = await RoleConverter().convert(ctx, "871957977370878052")
        yellow_role = await RoleConverter().convert(ctx, "871958094899462154")
        green_role = await RoleConverter().convert(ctx, "871958129666060298")
        blue_role = await RoleConverter().convert(ctx, "871958159168782357")
        for member in members: # for visual effect, remove all roles at once — could look cooler
            await member.remove_roles(red_role, yellow_role, green_role, blue_role)  

        for member in members: # then add them back 
            if member in red:
                await member.add_roles(red_role) # add_roles takes a long time because rate limited
                print(member.name, "was given red_role")
            elif member in yellow:
                await member.add_roles(yellow_role)
                print(member.name, "was given yellow_role")    
            elif member in green:
                await member.add_roles(green_role)
                print(member.name, "was given green_role") 
            elif member in blue:
                await member.add_roles(blue_role)
                print(member.name, "was given blue_role")   

        await ctx.send("Done with shuffling roles!")    

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