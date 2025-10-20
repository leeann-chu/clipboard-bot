from myutils.rcv.election_system import ElectionSystem
from typing import Tuple, Optional, List

class Borda(ElectionSystem):
    def __init__(self, candidates: List[str], ballots: List[List[str]]):
        self.candidates = candidates
        self.ballots = ballots

        num_choices = 0
        for ballot in ballots:
            if len(ballot) > num_choices:
                num_choices = len(ballot)

        self.num_choices = num_choices

    def tabulate(self) -> Tuple[Optional[str], str]:
        tabulator_dict = {}
        for ballot in self.ballots:
            points_assigned = self.num_choices
            for ranking in ballot:
                if ranking not in tabulator_dict:
                    tabulator_dict[ranking] = 0
                tabulator_dict[ranking] += points_assigned
                points_assigned -= 1


        tabulated_list = list(tabulator_dict.items())
        # Switch order to sort numerically first.
        tabulated_list = sorted([(a, b) for b, a in tabulated_list], reverse=True)

        if len(tabulated_list) > 1 and tabulated_list[0][0] == tabulated_list[1][0]:
            # There was a tie
            winner = None
        else:
            winner = tabulated_list[0][1]
        
        result_string = "\n".join(
            [f"{option} got {n} points." for n, option in tabulated_list]
        )
        return winner, result_string
