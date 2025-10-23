from itertools import combinations
from typing import Set, FrozenSet, List, Tuple, Optional
import copy
from myutils.rcv.election_system import ElectionSystem

class Kemeny:

    def __init__(self, candidates: List[str], ballots: List[List[str]]):
        self.candidates = candidates
        self.ballots = ballots

        # Subset of candidates : (Kemeny Score, Kemeny Consensus)
        self.memo = {frozenset(): (0, [])}

    def score_pair(self, pair: Tuple[str, str], ballot: List[str], ordering: List[str]):
        # Find ballot preference
        first_choice = None
        for candidate in ballot:
            if candidate in pair:
                first_choice = candidate
                break

        # Assume if neither is ranked they are equally undesirable
        if first_choice is None:
            return 1

        for candidate in ordering:
            if candidate not in pair:
                continue
            if candidate == first_choice:
                return 0
            else:
                return 2

        # Shoudn't reach here
        print("This should never be reached")
        return 0

    def kemeny_distance(self, ballot: List[str], ordering: List[str]) -> int:
        d = 0
        for pair in combinations(ordering, 2):
            d += self.score_pair(pair, ballot, ordering)
        return d

    def sum_distance(self, ordering: List) -> int:
        """Calculate the sum of KT distances between each ballot and ordering"""
        total = 0
        for ballot in self.ballots:
            total += self.kemeny_distance(ballot, ordering)

        return total

    def recurrence(self, C_prime: FrozenSet):
        min_cost = None
        min_ordering = None
        for c in C_prime:
            C_double_prime = C_prime - frozenset([c])
            assert len(C_double_prime) == len(C_prime) - 1
            assert C_double_prime in self.memo

            _, ordering = self.memo[C_double_prime]
            new_ordering = copy.copy(ordering)
            new_ordering.insert(0, c)

            # determine the cost of ranking c in first position
            cost = self.sum_distance(new_ordering)
            if min_cost is None or cost < min_cost:
                min_cost = cost
                min_ordering = new_ordering

        self.memo[C_prime] = (min_cost, min_ordering)

    def tabulate(self) -> Tuple[Optional[str], str]:
        # See section 5. of https://fpt.akt.tu-berlin.de/publications/kemeny.pdf
        # for the algorithm.
        # Time Complexity (2^m * m^2 * n) where m = len(self.candidates) and 
        # n = len(self.ballots).

        for cardinality in range(1, len(self.candidates) + 1):
            for subset in combinations(self.candidates, cardinality):
                self.recurrence(frozenset(subset))

        _, consensus = self.memo[frozenset(self.candidates)]
        print(consensus)
        winner = consensus[0]
        result_string = "The Kemeny consensus is:\n"
        result_string += "\n".join([f"{n+1}. {ranking}" for n, ranking in enumerate(consensus)])

        return winner, result_string


if __name__ == "__main__":
    # candidates = [
    #     "a",
    #     "b",
    #     "c",
    #     "d",
    #     "e",
    # ]

    # ballots = [
    #     ["a", "c", "b", "d", "e"],
    #     ["d", "c", "a", "b", "e"],
    #     ["e", "b", "d", "a", "c"],
    #     ["e", "a", "b", "c", "d"],
    # ]

    # candidates = [
    #     "Grand Sensei Dareth's Mojo Dojo",
    #     "The Anglish Kingdom",
    #     "Alcoholics Androgynous",
    #     "Department of Gaming Efficiency",
    #     "Cuomintang",
    #     "Nuclear Brewery",
    #     "HilAldi",
    #     "Inversive Feral Hog Horde",
    #     "Papal Conclave",
    # ]
    # ballots = [
    #     [
    #         "Grand Sensei Dareth's Mojo Dojo",
    #         "Department of Gaming Efficiency",
    #         "HilAldi",
    #         "Alcoholics Androgynous",
    #     ],
    #     ["Cuomintang", "Grand Sensei Dareth's Mojo Dojo", "Nuclear Brewery", "HilAldi"],
    #     ["Alcoholics Androgynous", "Inversive Feral Hog Horde", "Nuclear Brewery", "Cuomintang"],
    #     [
    #         "The Anglish Kingdom",
    #         "Grand Sensei Dareth's Mojo Dojo",
    #         "Department of Gaming Efficiency",
    #         "Papal Conclave",
    #     ],
    #     ["The Anglish Kingdom"],
    # ]

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
    for i in range(20):
        ballot = random.sample(candidates, 4)
        ballots.append(ballot)

    print(ballots)

    election = Kemeny(candidates, ballots)
    winner, result_string = election.tabulate()

    if winner is not None:
        print(f"The winner is {winner} !!!")

    if result_string is not None:
        print(result_string)
