import logging
import asyncio
from playwright.async_api import async_playwright

from src.bots.perfect import PerfectBot
from src.bots.llm import LLMBot
from src.gameloop import GameLoop
from src.player import Player

# Configure logging at module level
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True  # Override any existing configuration
)

logger = logging.getLogger(__name__)

async def run_bots_parallel(bots, headless: bool = False):
    logger.info(f"Starting parallel execution for {len(bots)} bot(s)")
    async with async_playwright() as p:
        logger.info(f"Launching browser (headless={headless})")
        browser = await p.chromium.launch(headless=headless,
        args=["--no-sandbox", "--disable-setuid-sandbox"] if headless else None)

        try:
            tasks = []
            for bot in bots:
                logger.info(f"Setting up player for bot: {bot.name}")
                player = Player(p, browser, width=1920, height=1080)
                loop = GameLoop(bot=bot, player=player)
                tasks.append(asyncio.create_task(loop.run()))

            logger.info("Running all bot tasks in parallel")
            await asyncio.gather(*tasks)
            logger.info("All bots completed successfully")

        except Exception as e:
            logger.error(f"Error during bot execution: {e}", exc_info=True)
            raise
        finally:
            logger.info("Closing browser")
            await browser.close()

def main() -> None:
    try:
        asyncio.run(run_bots_parallel(
            bots=[
                # PerfectBot(),
                LLMBot(),
                # RandomOffsetBot(max_lat_offset=0.01, max_lng_offset=0.01, year_jitter=3, seed=42),
                # add more bots here later
            ],
            headless=True
        ))
    except Exception as e:
        logger.info(f"Error running bots: {e}")

if __name__ == "__main__":
    main()
