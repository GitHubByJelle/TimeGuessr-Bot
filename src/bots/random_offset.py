from __future__ import annotations

import random
from typing import Optional

from src.bots.base import BaseBot
from src.model import DailyRound, Location
from src.custom_types import Guess, Year


class RandomOffsetBot(BaseBot):
    """
    Uses the true answer but adds a random offset to the coordinates.
    Useful for testing the game flow while not being perfectly accurate.
    """

    name = "RandomOffsetBot 🎲"

    def __init__(
        self,
        max_lat_offset: float = 0.02,
        max_lng_offset: float = 0.02,
        year_jitter: int = 0,
        seed: Optional[int] = None,
    ):
        self.max_lat_offset = max_lat_offset
        self.max_lng_offset = max_lng_offset
        self.year_jitter = year_jitter

        if seed is not None:
            random.seed(seed)

    async def guess_for_round(self, round_index: int, round_data: Optional[DailyRound]) -> Guess:
        if round_data is None:
            raise ValueError("RandomOffsetBot requires round_data (answers)")

        true_loc = round_data.Location

        lat_offset = random.uniform(-self.max_lat_offset, self.max_lat_offset)
        lng_offset = random.uniform(-self.max_lng_offset, self.max_lng_offset)

        guess_location = Location(
            lat=true_loc.lat + lat_offset,
            lng=true_loc.lng + lng_offset,
        )

        true_year = int(round_data.Year)
        year_offset = random.randint(-self.year_jitter, self.year_jitter) if self.year_jitter > 0 else 0
        guess_year: Year = true_year + year_offset

        return (guess_location, guess_year)