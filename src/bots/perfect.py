from __future__ import annotations

from typing import Optional

from src.bots.base import BaseBot
from src.model import DailyRound
from src.custom_types import Guess


class PerfectBot(BaseBot):
    name = "PerfectBot 💯"

    async def guess_for_round(self, round_index: int, round_data: Optional[DailyRound]) -> Guess:
        if round_data is None:
            raise ValueError("PerfectBot requires round_data (answers)")

        return (round_data.Location, int(round_data.Year))
