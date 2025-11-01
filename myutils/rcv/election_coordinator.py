from typing import Any

import discord
from re import findall, MULTILINE
import copy
from datetime import datetime, timedelta
import json

from discord import Interaction
from discord._types import ClientT

from collections import Counter
from typing import List, Union, Set, Optional

from myutils.rcv.election_system import ElectionSystem
from myutils.rcv.borda import Borda
from myutils.rcv.instant_runoff import InstantRunoff
from myutils.rcv.kemeny import Kemeny

from myutils.poll_class import writetoFile

import asyncio


# Coordinator of distributing ballots and counting votes.
class RCVElectionCoordinator:
    def __init__(self, ctx, title, opts, emojis, election_time, num_choices, method):
        if num_choices < 1 or num_choices > 4:
            raise Exception("Number of choices must be 1, 2, 3, or 4")

        if method not in ["kemeny", "irv", "borda"]:
            raise Exception("Election method must be one of: {kemeny, irv, borda}")

        if method == "kemeny" and len(opts) > 12:
            raise Exception("Too many candidates for Kemeny to handle.")

        self.ctx = ctx
        self.title = title
        self.opts = opts
        self.emojis = emojis
        self.candidates = list(
            [
                f"{copy.copy(emoji)} {copy.copy(opt)}"
                for emoji, opt in zip(self.emojis, self.opts)
            ]
        )
        self.ballots = {}
        self.request_view = RCVBallotRequestView(self, ctx.author.id)
        self.election_start_time = discord.utils.utcnow()
        self.election_time = election_time
        self.election_end_time = self.election_start_time + timedelta(
            seconds=self.election_time
        )
        self.num_choices = num_choices
        self.poll_message = None
        self.method = method
        self.lock = asyncio.Lock()  # just one lock because I don't wanna think
        self.election_begun = False
        self.stop_condition = asyncio.Condition()
        self.timer_task = None

    def election_in_progress_embed(self):
        candidates_string = "\n".join(
            [f"{emoji} {opt}" for emoji, opt in zip(self.emojis, self.opts)]
        )
        embed = discord.Embed(
            title=self.title,
            description=f"""
            Here are the candidates:\n{candidates_string}\n
            Click "Request Ballot" below to cast your vote. 
            Submitting a new ballot will overwrite your previous vote.
        """,
            color=0x419E85,
        )
        embed.add_field(name="Votes Recorded:", value=len(self.ballots))
        embed.add_field(
            name="Poll Open Time:",
            value=f"<t:{int(self.election_start_time.timestamp())}:f>",
        )
        embed.add_field(
            name="Poll Close Time:",
            value=f"<t:{int(self.election_end_time.timestamp())}:f>",
        )

        return embed

    def election_end_embed(self, winner, result_string):
        voting_string = ""
        for user_tuple, rankings in self.ballots.items():
            _user_id = user_tuple[0]
            user_name = user_tuple[1]

            # just use the emojis to try and avoid exceeding the embed limit
            ranking_string = " ".join([ranking.split(" ")[0] for ranking in rankings])
            voting_string += f"{user_name} ranked "
            voting_string += f"{ranking_string}\n"

        embed_title = f"The winner is {winner} !!!"
        embed_description = ""
        if len(embed_description) + len(result_string) > 4096:
            embed_description += "Too long to put in this embed."
        elif (
            len(embed_description) + len(result_string) + len(voting_string) + 2 > 4096
        ):
            embed_description += result_string
        else:
            embed_description += f"{result_string}\n\n{voting_string}"

        embed = discord.Embed(
            title=embed_title,
            description=embed_description,
        )
        embed.add_field(name="Votes Recorded:", value=len(self.ballots))
        embed.add_field(
            name="Poll Open Time:",
            value=f"<t:{int(self.election_start_time.timestamp())}:f>",
        )
        embed.add_field(
            name="Poll Close Time:",
            value=f"<t:{int(self.election_end_time.timestamp())}:f>",
        )
        return embed

    def get_election_system(self) -> ElectionSystem:
        candidates = copy.deepcopy(self.candidates)
        ballots = list(copy.deepcopy(self.ballots).values())
        if self.method == "kemeny":
            return Kemeny(candidates, ballots)
        elif self.method == "irv":
            return InstantRunoff(candidates, ballots)
        elif self.method == "borda":
            return Borda(candidates, ballots)
        else:
            raise Exception(f"Invalid election counting system {self.method}")

    async def close_poll_button_press(self):
        async with self.stop_condition:
            self.stop_condition.notify_all()

            async with self.lock:
                self.timer_task.cancel()

    async def hold_election(self):
        async with self.lock:
            if self.election_begun:
                return
            self.election_begun = True

        await self.begin_election()

        async with self.lock:
            self.timer_task = asyncio.create_task(
                self.election_timer(self.election_time)
            )

        await self.close_polls()
        await asyncio.sleep(5)
        await self.tabulate()

        # asyncio will complain if a task is not awaited, even if it's already finished
        await self.timer_task

    async def begin_election(self):
        async with self.lock:
            embed = self.election_in_progress_embed()
            self.poll_message = await self.ctx.send(embed=embed, view=self.request_view)

    async def election_timer(self, timeout):
        try:
            await asyncio.sleep(timeout)
            async with self.stop_condition:
                self.stop_condition.notify_all()
        except asyncio.CancelledError:
            # Cancel task gracefully.
            print("Election finished before timer. Cancelling wait.")

    async def distribute_ballot(self, interaction):
        async with self.lock:
            user = interaction.user
            ballot_fill_view = RCVBallotFillView(
                self,
                self.ctx,
                self.title,
                self.opts,
                self.emojis,
                num_choices=self.num_choices,
            )

            embed = discord.Embed(
                title="Ballot",
                description="Please rank the options in order of preference",
            )
            await interaction.response.send_message(
                ephemeral=True, embed=embed, view=ballot_fill_view
            )

    async def collect_ballot(self, interaction: discord.Interaction, ballot: list):
        async with self.lock:
            # Collect both id and name to ensure uniqueness
            user_id = interaction.user.id
            user_name = interaction.user.name
            self.ballots[(user_id, user_name)] = copy.deepcopy(ballot)

            rank_string = "\n".join(
                [f"{n+1}. {ranking}" for n, ranking in enumerate(ballot)]
            )

            embed = self.election_in_progress_embed()
            await self.poll_message.edit(embed=embed)

            embed = discord.Embed(
                title="Ballot Collected",
                description=f"Your vote has been counted! You voted for:\n{rank_string}",
            )
            await interaction.response.edit_message(embed=embed, view=None)

    async def close_polls(self):
        # Only want to close the poll after receiving the stop event.
        # This can be set after a timeout or
        async with self.stop_condition:
            await self.stop_condition.wait()

        async with self.lock:
            embed = discord.Embed(
                title="Polls Have Closed",
                description="The polls have closed. Ballot counting will begin shortly.",
            )
            await self.poll_message.edit(embed=embed, view=None)

    async def tabulate(self):
        async with self.lock:
            if len(self.ballots) == 0:
                embed = discord.Embed(title="Strange. No votes were counted.")
                await self.ctx.send(embed=embed, view=None)
                return

            election_system = self.get_election_system()
            winner, result_string = election_system.tabulate()
            if winner is None:
                result_string += "Switching to Borda count.\n"
                b = Borda(self.candidates, self.ballots)
                winner, borda_result = b.tabulate()
                if len(result_string) + len(borda_result) < 4000:
                    result_string += borda_result
                else:
                    result_string = f"Couldn't find a winner with {self.method}. Using Borda count instead.\n"
                    result_string += borda_result

            embed = self.election_end_embed(winner, result_string)
            await self.poll_message.edit(embed=embed, view=None)
            await self.ctx.send(
                content="The election has concluded. Please see the results above.",
                reference=self.poll_message.to_reference(),
            )

            to_dump = {key[0]: value for key, value in self.ballots.items()}
            writetoFile(to_dump, "storedPolls")


### Ballot Request Objects BEGIN ###
class RCVBallotRequestView(discord.ui.View):
    def __init__(self, coordinator, pollmaster):
        super().__init__(timeout=None)
        self.add_item(RCVRequestBallotButton(coordinator))
        self.add_item(RCVClosePollButton(coordinator, pollmaster))


class RCVRequestBallotButton(discord.ui.Button):
    def __init__(self, coordinator):
        super().__init__(label="Request Ballot", style=discord.ButtonStyle.primary)
        self.coordinator = coordinator

    async def callback(self, interaction: discord.Interaction):
        await self.coordinator.distribute_ballot(interaction)


class RCVClosePollButton(discord.ui.Button):
    def __init__(self, coordinator, pollmaster):
        super().__init__(label="Close Poll", style=discord.ButtonStyle.secondary)
        self.coordinator = coordinator
        self.pollmaster = pollmaster

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id == self.pollmaster:
            await self.coordinator.close_poll_button_press()
        else:
            await interaction.response.send_message(
                "You don't have permission to close the poll.", ephemeral=True
            )


### Ballot Request Objects END ###


### Ballot Fill Objects BEGIN ###
class RCVBallotFillSelection(discord.ui.Select):
    def __init__(
        self, placeholder="Choice", opts=None, emojis=None, disabled=True, row=None
    ):
        select_options = [
            discord.SelectOption(label=option, emoji=emoji)
            for option, emoji in zip(opts, emojis)
        ]
        select_options.append(  # If you don't want to rank anything else
            discord.SelectOption(label="None", emoji=None)
        )
        super().__init__(
            placeholder=placeholder, options=select_options, disabled=disabled, row=row
        )
        self.plain_opts = opts
        self.emojis = emojis

        self.current_opt = None
        self.current_emoji = None

    async def callback(self, interaction: discord.Interaction):
        self.current_opt = self.values[0]

        if self.current_opt == "None":
            self.current_emoji = None
        else:
            ind = self.plain_opts.index(self.current_opt)
            print(ind)
            print(self.current_opt)
            print(self.current_emoji)
            self.current_emoji = self.emojis[ind]

        await self.view.update_options(self, interaction)


class RCVBallotSubmitButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Submit", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        await self.view.submit_ballot(interaction)


class RCVBallotFillView(discord.ui.View):
    def __init__(self, coordinator, ctx, title, options, emojis, num_choices=3):
        super().__init__(timeout=180)

        self.coordinator = coordinator
        self.ctx = ctx
        self.title = title
        self.num_choices = num_choices

        if num_choices < 1 or num_choices > 4 or num_choices > len(options):
            raise Exception("Invalid number of choices provided.")

        labels = [
            "First Choice",
            "Second Choice",
            "Third Choice",
            "Fourth Choice",
            "Fifth Choice",
        ]
        self.choices = []
        for i in range(num_choices):
            self.choices.append(
                RCVBallotFillSelection(
                    placeholder=labels[i],
                    opts=options,
                    emojis=emojis,
                    disabled=True,
                    row=i,
                )
            )
        self.choices[0].disabled = False
        for choice in self.choices:
            self.add_item(choice)

        self.submit_button = RCVBallotSubmitButton()
        self.add_item(self.submit_button)

    async def update_options(
        self, selection: RCVBallotFillSelection, interaction: discord.Interaction
    ):
        row_num = selection.row
        selected = selection.values[0]

        # We need to set this selection as the default so it doesn't get cleared after
        # we send the response.
        selection.options = copy.deepcopy(
            selection.options
        )  # hopefully no memory issues python GC.
        # It's probably fine, should at least all get collected after election's over.

        for i in range(len(selection.options)):
            if selection.options[i].label == selected:
                selection.options[i].default = True
            else:
                selection.options[i].default = False

        # For the following options, we want to remove the one selected above.
        culled_choices = copy.deepcopy(selection.options)
        for i in range(len(culled_choices)):
            if culled_choices[i].label == selected:
                culled_choices.pop(i)
                break

        for child in self.children:
            if child.row is None or child.row <= row_num:
                continue
            elif child.row == row_num + 1 and selected != "None":
                child.disabled = False
            else:
                child.disabled = True
            child.options = culled_choices

        if row_num + 1 == self.num_choices or selected == "None":
            self.submit_button.disabled = False
        else:
            self.submit_button.disabled = True

        await interaction.response.edit_message(view=self)

    async def submit_ballot(self, interaction: discord.Interaction):
        ballot = []
        for choice in self.children:
            # Skip the submit button
            if type(choice) is not RCVBallotFillSelection:
                continue

            # "None" option is selected and shouldn't be counted.
            if choice.current_emoji == None:
                continue

            ballot.append(
                f"{copy.copy(choice.current_emoji)} {copy.copy(choice.current_opt)}"
            )

        if self.ballot_is_valid(ballot):
            await self.coordinator.collect_ballot(interaction, ballot)
        else:
            embed = discord.Embed(
                title="Vote Not Counted",
                description="Your ballot was not valid and your vote was not "
                "counted. Please be sure that you ranked at least one option"
                " and that there were no duplicates. Request another ballot "
                "to try again. No funny business this time.",
            )
            await interaction.response.edit_message(view=None, embed=embed)

    def ballot_is_valid(self, ballot):
        if not isinstance(ballot, list):
            return False

        # Check for empty ballot
        if len(ballot) == 0:
            return False

        # Check for duplicates
        ballot_set = set(ballot)
        if len(ballot_set) != len(ballot):
            return False

        return True


### Ballot Fill Objects END ###
