from __future__ import annotations

import logging
from playwright.async_api import Browser, BrowserContext, Page, Playwright

logger = logging.getLogger(__name__)


class Player:
    def __init__(
        self,
        playwright: Playwright,
        browser: Browser,
        width: int = 1920,
        height: int = 1080,
    ):
        self.playwright = playwright
        self.browser = browser
        self.width = width
        self.height = height

        self.context: BrowserContext | None = None
        self.page: Page | None = None

    async def start(self) -> Page:
        logger.info(f"Creating browser context with viewport {self.width}x{self.height}")
        self.context = await self.browser.new_context(
            viewport={"width": self.width, "height": self.height}
        )
        logger.info("Creating new page")
        self.page = await self.context.new_page()
        logger.info("Player started successfully")
        return self.page

    async def close(self) -> None:
        if self.context is not None:
            logger.info("Closing browser context")
            await self.context.close()
            logger.info("Browser context closed")
