from datetime import datetime
import json
import re
import copy
import requests
import ao3
from bs4 import BeautifulSoup
import discord
from discord.ext import commands
from myutils.views import EmbedPageView
from myutils.API_KEYS import AO3_PASSWORD, AO3_USERNAME
from myutils.poll_class import readfromFile, writetoFile

HEADERS = {"User-Agent": "fanfiction-abstractor-bot"}

ratingColors = {
    "Teen And Up Audiences": 0xE5D100,
    "Explicit": 0x9B0000,
    "General Audiences": 0x45DE1B,
    "Mature": 0xED5300,
    "Not Rated":0xFFFFFF,
    
    "K": 0x7de242,
    "K+": 0x70D6FF,
    "T": 0xE5D100,
    "M": 0xDB3700
}

ratingEmoji = {
    "Teen And Up Audiences": "<:TeenAndUpAudiences:1057882444654706728>",
    "Explicit": "<:Explicit:1057882406176165950>",
    "General Audiences": "<:GeneralAudiences:1057906281580597258>",
    "Mature": "<:Mature:1057926297646534697>",
    "Not Rated":":white_large_square:",

    "Gen": "<:Gen:1057907181044891719>",
    "F/M": "<:FM:1057882423234404463>",
    "M/M": "<:MM:1057885176455237763>",
    "F/F": "<:FF:1057882410097852466>",
    "Other": "<:Other:1057882436568100935>",
    "Multi": "<:Multi:1057882432239583282>",
    "No category": ":white_large_square:",

    "No Archive Warnings Apply": ":white_large_square:",
    "Creator Chose Not To Use Archive Warnings": "<:exclaimquestion:1057929664133349416>",
    "Exclaim": "<:exclaim:1057929667253915648>"
}

alertDB = {} 

#* ExtraInfo View for AO3
class ExtraInfo(discord.ui.View):
    def __init__(self, summary, tags):
        super().__init__()
        self.summary = summary
        self.tags = tags        
    #Add our buttons
    @discord.ui.button(label = "Summary")
    async def back(self, i:  discord.Interaction, button: discord.ui.Button):
        await i.response.send_message(f"__Summary__\n{self.summary}", ephemeral = True)
        return

    @discord.ui.button(label = "Tags")
    async def member(self, i:  discord.Interaction, button: discord.ui.Button):
        await i.response.send_message(f"__Tags__\n{self.tags}", ephemeral = True)
        return

    async def on_timeout(self) -> None:
        await self.message.edit(view = None)

def format_date(given_date):
    return datetime.strftime(datetime.strptime(given_date, "%Y-%m-%d"), "%B %d, %Y")

def format_html(field):
    """Format an HTML segment for discord markdown.
    field should be a note or summary from AO3.
    """
    brs = field.find_all("br")
    for br in brs:
        br.replace_with("\n")
    ols = field.find_all("ol")
    for ol in ols:
        ol.name = "p"
    uls = field.find_all("ul")
    for ul in uls:
        ul.name = "p"
    for li in field.find_all("li"):
        li.string = f"- {li.text.strip()}"
        li.unwrap()
    field = field.blockquote.find_all("p")
    result = list(map(lambda x: x.text.strip(), field))
    result = "\n\n".join(result)
    if len(result) > 250:
        result = result[:250] + "…"
    return result

def fic_update_alert_embed(pieces):
    # rating for ao3, rated for ffn
    rating = "Not Rated"
    if "rating" in pieces:
        rating = pieces["rating"]
    elif "rated" in pieces:
        rating = pieces["rated"]

    if "category" in pieces:
        category = pieces["category"]
    else: 
        category = "No category" 
        pieces["category_emoji"] = "No category" # I can't do what I did for rating because of Multi complicating things

    embed = discord.Embed(
        title = f"""{pieces["lock"]}{pieces["title"]}""",
        description = pieces["author"] + "\n",
        color = ratingColors[rating])

    if "updated" in pieces:
        embed.add_field(name=pieces["status"].capitalize() + ":", value=format_date(pieces["updated"]))

    embed.add_field(name="**Chapters:**", value=pieces["chapters"])
    embed.add_field(name="**Symbols:**", value=f"""{ratingEmoji[rating]} {ratingEmoji[pieces["category_emoji"]]}\n{ratingEmoji[pieces["warnings_emoji"]]} {pieces["status_emoji"]}""") 
    return embed

def generate_ao3_work_summary(link):
    """Generate the summary of an AO3 work.
    link should be a link to an AO3 fic
    Returns an embed with parsed pieces of the fic, and a possible error message
    """
    ficPieces = {}
    r = requests.get(link, headers=HEADERS)
    soup = BeautifulSoup(r.text, "lxml")
    ficPieces["lock"] = ""
    if r.status_code != requests.codes.ok:
        return ficPieces, "Request not okay :c"
    if r.url == "https://archiveofourown.org/users/login?restricted=true":
        ao3_session = AO3.Session(AO3_USERNAME, AO3_PASSWORD)
        soup = ao3_session.request(link)
        ficPieces["lock"] = ":lock: "

    # if chapter link, replace with work link
    if "/chapters/" in link:
        share = soup.find(class_="share")
        work_id = share.a["href"].strip("/works/").strip("/share")
        link = f"https://archiveofourown.org/works/{work_id}"
    ficPieces["link"] = link # in case it was changed if it was a chapter link

    preface = soup.find(class_="preface group")
    ficPieces["title"] = preface.h2.text.strip()

    author = preface.h3.string
    multi_author = []
    if author is None:
        multi_author = [f"""[{name.string}](https://archiveofourown.org{name["href"]})""" for name in preface.h3.find_all("a")]
        ficPieces["author"] = "by " + ", ".join(multi_author)
    else:
        ficPieces["author"] = author.strip()

    summary = preface.find(class_="summary module")
    if summary:
        ficPieces["summary"] = format_html(summary)

    tags = soup.find(class_="work meta group")
    rating = tags.find("dd", class_="rating tags")
    category = tags.find("dd", class_="category tags")
    fandoms = tags.find("dd", class_="fandom tags")
    warnings = tags.find("dd", class_="warning tags")
    relationships = tags.find("dd", class_="relationship tags")
    characters = tags.find("dd", class_="character tags")
    freeform = tags.find("dd", class_="freeform tags")
    series = tags.find("dd", class_="series")
    bookmarks = tags.find("dd", class_="bookmarks")
    words = tags.find("dd", class_="words")
    chapters = tags.find("dd", class_="chapters")
    kudos = tags.find("dd", class_="kudos")

    ficPieces["kudos"] = kudos.string if kudos else 0
    ficPieces["bookmarks"] = bookmarks.string if bookmarks else 0
    ficPieces["words"] = words.string if words else 0
    
    completed = tags.find("dt", class_="status") # can be none
    updated = tags.find("dd", class_="status") 
    if updated or completed: # updated & published / completed & published
        ficPieces["status"] = completed.string[:-1]
        ficPieces["updated"] = updated.string
        ficPieces["status_emoji"] = "<:not_finished:1057949352338927658>"
    else: # neither updated or completed
        ficPieces["status"] = "Published"
        ficPieces["updated"] = tags.find("dd", class_="published").string
        ficPieces["status_emoji"] = ":white_large_square:"

    if chapters:
        part, whole = chapters.string.split("/")
        ficPieces["chapters"] = chapters.string
    if part == whole:
        ficPieces["status_emoji"] = "<:Completed:1057962897017421884>"

    multi_series = ""
    if series:
        for s in series.find_all(class_="position")[:5]:
            s_name = s.text.split()
            s = f"""**Part {s_name[1]}** of **[{" ".join(s_name[3:])}](https://archiveofourown.org{s.a["href"]})**\n"""
            multi_series += s
        ficPieces["series"] = multi_series

    if fandoms:
        fandoms = list(map(lambda x: x.string, fandoms.find_all("a")))
        if len(fandoms) > 5:
            ficPieces["fandoms"] = ", ".join(fandoms[:5]) + "…"
        else:
            ficPieces["fandoms"] = ", ".join(fandoms)

    if rating:
        ficPieces["rating"] = ", ".join(map(lambda x: x.string, rating.find_all("a")))
    if category: 
        category = list(map(lambda x: x.string, category.find_all("a")))
        ficPieces["category"] = ", ".join(category)
        if len(category) > 1:
            ficPieces["category_emoji"] = "Multi"
        else:
            ficPieces["category_emoji"] = category[0]

    warnings = list(map(lambda x: x.string, warnings.find_all("a")))
    ficPieces["warnings"] = ", ".join(warnings)
    if warnings[0] in ratingEmoji:
        ficPieces["warnings_emoji"] = warnings[0]
    else:
        ficPieces["warnings_emoji"] = "Exclaim"

    if relationships:
        ficPieces["character_heading"] = "Additional Characters:"
        relationships = list(map(lambda x: x.string, relationships.find_all("a")))
        if len(relationships) > 4:
            ficPieces["relationships"] = ", ".join(relationships[:4]) + "…"
        else:
            ficPieces["relationships"] = ", ".join(relationships)
    else:
        ficPieces["character_heading"] = "Characters:"

    if characters:
        characters = list(map(lambda x: x.string, characters.find_all("a")))
        # hides characters already listed in relationships
        if relationships:
            already_listed = set() 
            for r in relationships[:4]:
                r = r.replace(" & ", "/").split("/")
                for c in r:
                    if " (" in c:
                        c = c.split(" (")[0] 
                    already_listed.add(c)
            chars_static = characters.copy()
            for c in chars_static:
                before = c
                if " (" in c:
                    c = c.split(" (")[0] 
                if " - " in c:
                    c = c.split(" - ")[0]
                if c in already_listed:
                    characters.remove(before)

        if len(characters) > 4:
            ficPieces["characters"] = ", ".join(characters[:4]) + "…"
        else:
            ficPieces["characters"] = ", ".join(characters)

    if freeform: # same as tags
        freeform = list(map(lambda x: x.string, freeform.find_all("a")))
        if len(freeform) > 5:
            ficPieces["tags"] = ", ".join(freeform[:5]) + "…"
        else:
            ficPieces["tags"] = ", ".join(freeform)

    return ficPieces, ""

def generate_ao3_series_summary(link):
    """Generate the summary of an AO3 series.
    link should be a link to an AO3 series
    Returns an embed with the series and a list of works
    """
    embed_list = []
    lockIcon = ""
    r = requests.get(link, headers=HEADERS)
    soup = BeautifulSoup(r.text, "lxml")

    if r.status_code != requests.codes.ok:
        return embed_list, "Request not okay :c"
    if r.url == "https://archiveofourown.org/users/login?restricted=true":
        ao3_session = AO3.Session(AO3_USERNAME, AO3_PASSWORD)
        soup = ao3_session.request(link)
        lockIcon = ":lock: "   

    embed = discord.Embed(
        title = f"""{lockIcon}{soup.find("h2", class_="heading").text.strip()}""",
        color = 0x2F3136
    )
    embed.url = link
    embed.set_author(name="Archive of Our Own", icon_url="https://archiveofourown.org/images/ao3_logos/logo_42.png")
 
    preface = soup.find(class_="series meta group")
    next_field = preface.dd
    multi_author = [f"""[{name.string}](https://archiveofourown.org{name["href"]})""" for name in next_field.find_all("a")]
    
    # author = ", ".join(map(lambda x: x.string, next_field.find_all("a")))
    next_field = next_field.find_next_sibling("dd")
    begun = next_field.string # Begun
    next_field = next_field.find_next_sibling("dd")
    updated = next_field.string # Updated
    next_field = next_field.find_next_sibling("dt")

    embed.description = f"""by {", ".join(multi_author)}\n\n**Begun:** {format_date(begun)}\n**Updated:** {format_date(updated)}"""

    if next_field.string == "Description:":
        next_field = next_field.find_next_sibling("dd")
        embed.add_field(name="Description:", value=format_html(next_field), inline=False) 
        next_field = next_field.find_next_sibling("dt")
    if next_field.string == "Notes:": # Even thought not being used, still need to go through all fields
        next_field = next_field.find_next_sibling("dd")
        next_field = next_field.find_next_sibling("dt")

    next_field = next_field.find_next_sibling("dd").dl.dd
    words = next_field.string
    next_field = next_field.find_next_sibling("dd")
    works = next_field.string
    complete = next_field.find_next_sibling("dd").string
    complete = "<:Completed:1057962897017421884>" if complete == "Yes" else "<:not_finished:1057949352338927658>"
    embed.add_field(name="Stats:", value=f"`{words}` *words* | `{works}` *works* | {complete} *complete*", inline=False)
    
    # Find titles and links to first few works
    works = soup.find_all(class_=re.compile("work blurb group work-.*"))
    multi_works = [f"""{i+1}. [{work.h4.a.string}](https://archiveofourown.org{work.h4.a["href"]})""" for i, work in enumerate(works)]
    chunked_works = [multi_works[i:i + 4] for i in range(0, len(multi_works), 4)]
    embed_list = []
    for index, chunk in enumerate(chunked_works):
        dummy_embed = copy.deepcopy(embed)
        dummy_embed.add_field(name="\u2800", value="\n".join(chunk))
        dummy_embed.set_footer(text=f"Page {index+1}/{len(chunked_works)}")
        embed_list.append(dummy_embed)

    return embed_list, ""

def generate_ffn_work_summary(link):
    """Generate summary of FFN work.
    link should be a link to an FFN fic
    Returns an embed with parsed pieces of the fic, and a possible error message
    """
    MY_HEADER = {"User-Agent": "username#1234"}
    fichub_link = "https://fichub.net/api/v0/epub?q=" + link
    r = requests.get(fichub_link, headers=MY_HEADER)
    if r.status_code != requests.codes.ok:
        return {}, "Request not okay :c"
    metadata = json.loads(r.text)["meta"]
    extra_metadata = metadata.get("rawExtendedMeta")
    if extra_metadata is None: extra_metadata = {}
    combined = {**metadata, **extra_metadata}
    ficPieces = { k: combined[k] for k in combined.keys() & 
    {"title", "status", "chapters", "characters", "genres", "rated", "favorites", "reviews", "words"} } # filters out relevant keys
    ficPieces["summary"] = metadata["description"].strip("<p>").strip("</p>")
    ficPieces["updated"] = metadata["updated"].split("T")[0]

    if extra_metadata:
        ficPieces["fandoms"] = extra_metadata["raw_fandom"]
    else:
        ficPieces["ffnstuff"] = metadata.get("extraMeta", None)
    ficPieces["author"] = f"""by [{metadata["author"]}]({metadata["authorUrl"]})"""
    ficPieces["link"] = link # avoid key error 
    return ficPieces, ""

def makeEmbed(pieces):
    if "lock" in pieces: ## ao3 link
        stats_line = f"""`{pieces["words"]}` *words* | `{pieces["kudos"]}` *kudos* | `{pieces["bookmarks"]}` *bookmarks* | `{pieces["chapters"]}` *chapter(s)* """
    else: # ffn link
        pieces["lock"] = ""
        favorites = pieces.get("favorites", 0)
        reviews = pieces.get("reviews", 0)
        stats_line = f"""`{pieces["words"]}` *words* | `{favorites}` *favorites* | `{reviews}` *reviews* | `{pieces["chapters"]}` *chapter(s)*"""
    
    # rating for ao3, rated for ffn
    rating = "Not Rated"
    if "rating" in pieces:
        rating = pieces["rating"]
    elif "rated" in pieces:
        rating = pieces["rated"]

    if "category" in pieces:
        category = pieces["category"]
    else: 
        category = "No category" 
        pieces["category_emoji"] = "No category" # I can't do what I did for rating because of Multi complicating things

    embed = discord.Embed(
        title = f"""{pieces["lock"]}{pieces["title"]}""",
        description = pieces["author"] + "\n",
        color = ratingColors[rating])

    if "fandoms" in pieces:
        # embed.add_field(name="Fandoms:", value=pieces["fandoms"], inline=False)
        embed.description += f"""**Fandoms:** {pieces["fandoms"]}\n"""
    if "ffnstuff" in pieces:
        embed.add_field(name="Misc Info:", value=pieces["ffnstuff"], inline=False)
    if "summary" in pieces:
        # embed.add_field(name="Summary:", value=pieces["summary"], inline=False)
        embed.description += f"""**Summary:** {pieces["summary"]}\n"""
    if "series" in pieces:  
        embed.add_field(name="Series:", value=pieces["series"], inline=False)

    if rating != "Not Rated" and category != "No category":        
        embed.add_field(name="**Rating:**", value=f"""{rating}\n**Category**: {category}""")
    elif rating != "Not Rated":
        embed.add_field(name="Rating:", value=rating)
    elif category != "No category":
        embed.add_field(name="Category:", value=category) 

    if "updated" in pieces:
        embed.add_field(name=pieces["status"].capitalize() + ":", value=format_date(pieces["updated"]))

    if "warnings" in pieces: # don't add symbols if ffn link
        embed.add_field(name="**Symbols:**", value=f"""{ratingEmoji[rating]} {ratingEmoji[pieces["category_emoji"]]}\n{ratingEmoji[pieces["warnings_emoji"]]} {pieces["status_emoji"]}""")
        if pieces["warnings"] != "No Archive Warnings Apply":
            embed.add_field(name="Warnings:", value=pieces["warnings"])
    if "genres" in pieces:
        embed.add_field(name="**Genre:**", value=pieces["genres"])

    if "relationships" in pieces:
        embed.add_field(name="Relationships:", value=pieces["relationships"], inline=False)
    if "characters" in pieces:
        character_heading = pieces["character_heading"] if "character_heading" in pieces else "Characters:"
        if pieces["characters"]: # catch if characters are an empty set
            embed.add_field(name=character_heading, value=pieces["characters"], inline=False)
    if "tags" in pieces:
        # embed.add_field(name="Tags:", value=pieces["tags"], inline=False)
        embed.description += f"""**Tags:** {pieces["tags"]}\n"""

    embed.add_field(name="Stats:", value=stats_line, inline=False)
    embed.url = pieces["link"]
    # embed.add_field(name="\u2800", value=field2, inline=False)
    return embed

class embedBuilder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        print("embedBuilder is Ready")

    # Commands
    @commands.command()
    async def sendFic(self, ctx, link):
        await ctx.channel.typing()
        pieces, error = generate_ao3_work_summary(link)
        if error:
            return await ctx.send(error)
        embed = makeEmbed(pieces)
        embed.set_author(name="Archive of Our Own", icon_url="https://archiveofourown.org/images/ao3_logos/logo_42.png")
        embed.set_footer(text=f"Linked by {ctx.message.author}", icon_url=ctx.message.author.avatar.url)
        await ctx.send(embed=embed)
        # extraInfo = ExtraInfo(pieces["summary"], pieces["tags"])
        # extraInfo.message = await ctx.send(embed=embed, view=extraInfo)

    @commands.command()
    async def sendFFN(self, ctx, link):
        await ctx.channel.typing()
        pieces, error = generate_ffn_work_summary(link)
        if error:
            return await ctx.send(error)
        embed = makeEmbed(pieces)
        embed.set_author(name="FanFiction.net", icon_url="https://media.cdnandroid.com/item_images/687604/imagen-fanfiction-net-0big.jpg")
        embed.set_footer(text=f"Linked by {ctx.message.author}", icon_url=ctx.message.author.avatar.url)
        await ctx.send(embed=embed)

    @commands.command()
    async def sendSeries(self, ctx, link):
        embed_list, error = generate_ao3_series_summary(link)
        if error:
            return await ctx.send(error)
        await ctx.channel.typing()
        if len(embed_list) < 2:
            return await ctx.send(embed=embed_list[0])
        pageView = EmbedPageView(eList = embed_list, pagenum = 0)
        pageView.message = await ctx.send(embed=embed_list[0], view = pageView)

    @commands.command(aliases=["alertme", "am"])
    async def alertMe(self, ctx, link):
        await ctx.channel.typing()
        pieces, error = generate_ao3_work_summary(link)
        if error:
            return await ctx.send(error)
        
        embed = fic_update_alert_embed(pieces)
        embed.set_author(name="Archive of Our Own", icon_url="https://archiveofourown.org/images/ao3_logos/logo_42.png")
        embed.set_footer(text=f"Requested by {ctx.message.author}", icon_url=ctx.message.author.avatar.url)
        # Fic is already completed, return early
        if pieces["status"] == "Completed" or pieces["status"] == "Published":
            return await ctx.send("This fic is Completed! <:Completed:1057962897017421884>", embed=embed)
        
        # ------------- ALERT ME SCRIPT -------------- #
        alertDB = readfromFile("alertMe")
        work_link = pieces["link"] # cleaned in case it's a chapter link
        alertInfoDict = alertDB.setdefault(work_link, {})
        sendEmbed = True
        alert_message = None

        if not alertInfoDict: # creating a new link in db 
            alertInfoDict["chapters"] = [pieces["chapters"].split("/")[0]] # create a new one 
            alert_message = ":mega: You've been added to the alerts for this fic!"
        else:
            curr_chapter = alertInfoDict["chapters"]
            updated_chap = int(pieces["chapters"].split("/")[0]) 
            if int(curr_chapter) < updated_chap: #setup to ping
                embed.add_field(name=":tada: Fic Updated! :tada:", value=f"""{curr_chapter} → {updated_chap}""", inline=False)
                alertInfoDict["chapters"] = updated_chap
            else:
                if not alert_message: # Fic already linked
                    await ctx.send("No new updates on this fic :pensive:") # Nothing updated
                    sendEmbed = False # send nothing      

        if ctx.message.author.id not in alertInfoDict["usersNotified"]:
            alertInfoDict["usersNotified"].append(ctx.message.author.id)

        if sendEmbed:
            await ctx.send(alert_message, embed=embed)

        alertDB[work_link] = alertInfoDict # save updates
        writetoFile(alertDB, "alertMe")

    async def removeAlert(self, ctx, link):
        await ctx.channel.typing()
        pieces, error = generate_ao3_work_summary(link)
        if error:
            return await ctx.send(error)
        
        alertDB = readfromFile("alertMe")
        work_link = pieces["link"] # cleaned in case it's a chapter link



        del alertDB[work_link]
        writetoFile(alertDB, "alertMe")
        await ctx.send("Alert removed from database!")


async def setup(bot):
    await bot.add_cog(embedBuilder(bot))
