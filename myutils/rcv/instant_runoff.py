import copy

from collections import Counter
from typing import List, Union, Set, Optional, Tuple

from myutils.rcv.election_system import ElectionSystem

class InstantRunoff(ElectionSystem):
    # "Borrowed" this code from https://medium.com/@goldengrisha/building-an-instant-runoff-voting-algorithm-in-python-b9a9ad2ca97d
    def __init__(self, candidates, ballots):
        self.candidates = candidates
        self.ballots = ballots

    def get_all_ballots(self, voters: List[List[Union[str, None]]]) -> Set[str]:
        all_ballots: Set[str] = set()
        for row in voters:
            for vote in row:
                if vote is not None:
                    all_ballots.add(vote)
        return all_ballots

    def clear_matrix(
        self,
        voters: List[List[Union[str, None]]],
        frequency: Counter[str],
        all_ballots: Set[str],
        result_string: str,
        round_num: int,
    ) -> List[List[Union[str, None]]]:
        # Track candidates present in the current front line (top preferences of each voter)
        front_line: Set[str] = set()
        for i in range(len(voters)):
            for j in range(len(voters[i])):
                current = voters[i][j]
                if current is not None:
                    front_line.add(current)
                    break

        # Candidates not in the front line have zero votes
        candidates_to_remove = all_ballots - front_line

        # Add candidates with the minimum votes
        min_votes = min(frequency.values(), default=0)
        candidates_to_remove |= {
            candidate for candidate, count in frequency.items() if count == min_votes
        }

        removed_candidates = set()
        # Remove candidates from the matrix
        for i in range(len(voters)):
            for j in range(len(voters[i])):
                if voters[i][j] in candidates_to_remove:
                    removed_candidates.add(voters[i][j])
                    voters[i][j] = None

        result_string += f"In round {round_num}, "
        result_string += ", ".join([candidate for candidate in removed_candidates])
        result_string += " got eliminated.\n"

        return voters, result_string

    def tabulate(self) -> Tuple[Optional[str], str]:
        voters = copy.copy(self.ballots)
        all_ballots = set(copy.copy(self.candidates))

        half = len(voters) // 2
        result_string = ""
        round_num = 1
        while True:
            # Count first-choice votes
            frequency: Counter[str] = Counter()
            for vote in voters:
                for candidate in vote:
                    if candidate is not None:
                        frequency[candidate] += 1
                        break

            if not frequency:
                result_string += (
                    f"In round {round_num}, no candidate could achieve a majority.\n"
                )
                return None, result_string  # Complete tie (no candidates left)

            # Check if all remaining candidates are tied
            if len(set(frequency.values())) == 1 and len(frequency) > 1:
                result_string += (
                    f"In round {round_num}, no candidate could achieve a majority.\n"
                )
                return (
                    None,
                    result_string,
                )  # Complete tie with multiple candidates remaining

            # Check if any candidate has more than half the votes
            most_common = frequency.most_common(1)
            if most_common and most_common[0][1] > half:
                result_string += (
                    f"In round {round_num}, {most_common[0][0]} achieved a majority.\n"
                )
                return most_common[0][0], result_string

            # Clear the least frequent candidates
            voters, result_string = self.clear_matrix(
                voters, frequency, all_ballots, result_string, round_num
            )
            round_num += 1

if __name__ == "__main__":
    candidates = [
        "a",
        "b",
        "c",
        "d",
        "e",
        "f",
        "g",
        "h",
        "i",
        "j",
    ]

    import random

    ballots = []
    for i in range(23):
        ballot = random.sample(candidates, 4)
        ballots.append(ballot)

    print(ballots)

    irv = InstantRunoff(candidates, ballots)

    winner, result_string = irv.runoff()

    print(f"The winner is {winner} !!!")
    print(result_string)
