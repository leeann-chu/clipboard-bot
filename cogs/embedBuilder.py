import discord
import random
from discord.ext import commands
from datetime import datetime
from utils.views import EmbedPageView
from bs4 import BeautifulSoup
import requests
import copy
import re

HEADERS = {"User-Agent": "fanfiction-abstractor-bot"}
FFN_GENRES = set()

ratingColors = {
    "Teen And Up Audiences": 0xE5D100,
    "Explicit": 0x9B0000,
    "General Audiences": 0x7de242,
    "Mature": 0xE1730D,
    "Not Rated":0xFFFFFF
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
        li.string = "- {}".format(li.text.strip())
        li.unwrap()
    field = field.blockquote.find_all("p")
    result = list(map(lambda x: x.text.strip(), field))
    result = "\n\n".join(result)
    if len(result) > 250:
        result = result[:250] + "…"
    return result
    
def generate_ao3_work_summary(link):
    """Generate the summary of an AO3 work.
    link should be a link to an AO3 fic
    Returns the message with the fic info, or else a blank string
    """
    ficPieces = {}
    r = requests.get(link, headers=HEADERS)
    if r.status_code != requests.codes.ok:
        return ficPieces, "Request not okay :c"
    if r.url == "https://archiveofourown.org/users/login?restricted=true":
        return ficPieces, ":lock: Restricted fic"
    soup = BeautifulSoup(r.text, "lxml")

    # if chapter link, replace with work link
    if "/chapters/" in link:
        share = soup.find(class_="share")
        work_id = share.a["href"].strip("/works/").strip("/share")
        link = f"https://archiveofourown.org/works/{work_id}"
    ficPieces["link"] = link

    preface = soup.find(class_="preface group")
    ficPieces["title"] = preface.h2.string.strip()
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
    checkmark = ""
    if updated or completed: # updated & published / completed & published
        ficPieces["status"] = completed.string
        ficPieces["updated"] = updated.string
        ficPieces["status_emoji"] = "<:not_finished:1057949352338927658>"
    else: # neither updated or completed
        ficPieces["status"] = "Published:"
        ficPieces["updated"] = tags.find("dd", class_="published").string
        ficPieces["status_emoji"] = ":white_large_square"

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
    """Generate the summary of an AO3 work.
    link should be a link to an AO3 series
    Returns the message with the series info, or else a blank string
    """
    embed_list = []
    r = requests.get(link, headers=HEADERS)
    if r.status_code != requests.codes.ok:
        return embed_list, "Request not okay :c"
    if r.url == "https://archiveofourown.org/users/login?restricted=true":
        return embed_list, ":lock: Restricted fic"
    soup = BeautifulSoup(r.text, "lxml")

    embed = discord.Embed(
        title = soup.find("h2", class_="heading").string.strip(),
        color = 0x2F3136
    )
    embed.url = link
 
    preface = soup.find(class_="series meta group")
    next_field = preface.dd
    multi_author = [f"""[{name.string}](https://archiveofourown.org{name["href"]})""" for name in next_field.find_all("a")]
    embed.description = "by " + ", ".join(multi_author)
    # author = ", ".join(map(lambda x: x.string, next_field.find_all("a")))
    next_field = next_field.find_next_sibling("dd")
    embed.add_field(name="Begun:", value=next_field.string) 
    next_field = next_field.find_next_sibling("dd")
    embed.add_field(name="Updated:", value=next_field.string) 
    next_field = next_field.find_next_sibling("dt")
    if next_field.string == "Description:":
        next_field = next_field.find_next_sibling("dd")
        embed.add_field(name="Description:", value=format_html(next_field), inline=False) 
        next_field = next_field.find_next_sibling("dt")

    # Get kind of long, removed in abtractor? 
    if next_field.string == "Notes:":
        next_field = next_field.find_next_sibling("dd")
        # embed.add_field(name="Notes:", value=format_html(next_field), inline=False) 
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

def makeEmbed(pieces):
    words_kudos_bookmarks = f"""`{pieces["words"]}` *words* | `{pieces["kudos"]}` *kudos* | `{pieces["bookmarks"]}` *bookmarks*
    """

    if "chapters" in pieces:
        chapters = pieces["chapters"]
    if "updated" in pieces:
        updated = pieces["updated"]

    if "rating" in pieces:
        rating = pieces["rating"]
    else: rating = "Not Rated"

    if "category" in pieces:
        category = pieces["category"]
    else: 
        category = "No category"
        pieces["category_emoji"] = "No category"

    embed = discord.Embed(
        title = pieces["title"],
        description = pieces["author"],
        color = ratingColors[rating]
    )

    if "fandoms" in pieces:
        embed.add_field(name="Fandoms:", value=pieces["fandoms"], inline=False)
    if "summary" in pieces:
        embed.add_field(name="Summary:", value=pieces["summary"], inline=False)
    if "series" in pieces:  
        embed.add_field(name="Series:", value=pieces["series"], inline=False)

    if rating != "Not Rated" and category != "No category":        
        embed.add_field(name="**Rating:**", value=f"""{rating}\n**Category**: {category}""")
    elif rating != "Not Rated":
        embed.add_field(name=f"Rating:", value=rating)
    elif category != "No category":
        embed.add_field(name=f"Category:", value=category) 

    if chapters and updated:
        embed.add_field(name="**Chapters:**", value=f"""{chapters}\n**{pieces["status"]}**\n{datetime.strftime(datetime.strptime(updated, "%Y-%m-%d"), "%B %d, %Y")}""")
    elif chapters:
        embed.add_field(name="Chapters:", value=chapters)
    elif updated:
        embed.add_field(name=pieces["status"], value=datetime.strftime(datetime.strptime(updated, "%Y-%m-%d"), "%B %d, %Y"))

    embed.add_field(name="**Symbols:**", value=f"""{ratingEmoji[rating]} {ratingEmoji[pieces["category_emoji"]]}\n{ratingEmoji[pieces["warnings_emoji"]]} {pieces["status_emoji"]}""")
    
    if pieces["warnings"] != "No Archive Warnings Apply":
        embed.add_field(name="Warnings:", value=pieces["warnings"])

    if "relationships" in pieces:
        embed.add_field(name="Relationships:", value=pieces["relationships"], inline=False)
    if "characters" in pieces:
        embed.add_field(name=pieces["character_heading"], value=pieces["characters"], inline=False)
    if "tags" in pieces:
        embed.add_field(name="Tags:", value=pieces["tags"], inline=False)

    embed.add_field(name="Stats:", value=words_kudos_bookmarks, inline=False)
    embed.url = pieces["link"]

    # embed.add_field(name="\u2800", value=field2, inline=False)

    embed.set_author(name="Archive of Our Own", icon_url="https://archiveofourown.org/images/ao3_logos/logo_42.png")

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
        print(datetime.now())
        pieces, error = generate_ao3_work_summary(link)
        if error:
            return await ctx.send(error)
        await ctx.channel.typing()
        print(datetime.now())
        embed = makeEmbed(pieces)
        embed.set_footer(text=f"Linked by {ctx.message.author}", icon_url=ctx.message.author.avatar.url)
        await ctx.send(embed=embed)
        print(f"{datetime.now()}\n")

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

async def setup(bot):
    await bot.add_cog(embedBuilder(bot))
