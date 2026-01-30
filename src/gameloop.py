from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from src.bots.base import BaseBot
from src.client import TimeGuessrClient
from src.model import DailyRound
from src.player import Player
from src.teams import send_to_teams

logger = logging.getLogger(__name__)

@dataclass
class GameLoopConfig:
    rounds: int = 5
    keep_browser_open_ms: int = 0


class GameLoop:
    def __init__(self, bot: BaseBot, player: Player, config: Optional[GameLoopConfig] = None):
        self.bot = bot
        self.player = player
        self.config = config or GameLoopConfig()

    async def run(self) -> None:
        logger.info(f"[{self.bot.name}] Starting game loop")
        
        try:
            logger.info(f"[{self.bot.name}] Starting player and initializing page")
            page = await self.player.start()
            client = TimeGuessrClient(page)

            logger.info(f"[{self.bot.name}] Navigating to daily game")
            await client.go_to_daily()
            
            logger.info(f"[{self.bot.name}] Fetching answers for {self.config.rounds} rounds")
            answers: list[DailyRound] = await client.get_answers()
            logger.info(f"[{self.bot.name}] Retrieved {len(answers)} answer(s)")

            for i in range(1, self.config.rounds + 1):
                logger.info(f"[{self.bot.name}] Starting round {i}/{self.config.rounds}")
                round_data = answers[i - 1] if i - 1 < len(answers) else None

                location, year = await self.bot.guess_for_round(i, round_data)
                logger.info(f"[{self.bot.name}] Round {i} guess -> lat={location.lat}, lng={location.lng}, year={year}")

                logger.info(f"[{self.bot.name}] Submitting guess for round {i}")
                await client.make_guess(location, year)

                logger.info(f"[{self.bot.name}] Moving to next round")
                await client.go_to_next_round()

            logger.info(f"[{self.bot.name}] All rounds completed, retrieving results")
            results: str = f"{self.bot.name}\n{await client.get_results()}"
            
            logger.info(f"[{self.bot.name}] Sending results to Teams")
            await send_to_teams(results)
            logger.info(f"[{self.bot.name}] Results sent successfully")

            if self.config.keep_browser_open_ms > 0:
                logger.info(f"[{self.bot.name}] Keeping browser open for {self.config.keep_browser_open_ms}ms")
                await page.wait_for_timeout(self.config.keep_browser_open_ms)

            logger.info(f"[{self.bot.name}] Closing player")
            await self.player.close()
            logger.info(f"[{self.bot.name}] Game loop completed successfully")
            
        except Exception as e:
            logger.error(f"[{self.bot.name}] Error during game loop: {e}", exc_info=True)
            raise
