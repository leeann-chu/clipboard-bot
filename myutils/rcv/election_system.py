import abc
from typing import List, Optional, Tuple

class ElectionSystem(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __init__(self, candidates: List[str], ballots: List[List[str]]):
        self.candidates = candidates
        self.ballots = ballots

    @abc.abstractmethod
    def tabulate(self) -> Tuple[Optional[str], str]:
        pass
