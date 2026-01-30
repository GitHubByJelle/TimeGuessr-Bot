from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from src.model import DailyRound
from src.custom_types import Guess


class BaseBot(ABC):
    name: str = "BaseBot"

    @abstractmethod
    async def guess_for_round(self, round_index: int, round_data: Optional[DailyRound]) -> Guess:
        """
        Returns: (Location, Year)
        """
        raise NotImplementedError
