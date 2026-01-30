from __future__ import annotations

import json
from typing import List

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from src.model import DailyRound, Location, DailyRoundResult, GameResults
from src.custom_types import Year
import logging


class TimeGuessrClient:
    def __init__(self, page: Page):
        self.page = page
        
    async def go_to_daily(self) -> None:
        logger = logging.getLogger(__name__)
        page = self.page
        
        logger.info("Navigating to timeguessr.com")
        await page.goto("https://timeguessr.com/", wait_until="domcontentloaded")

        logger.info("Clicking 'Daily' button")
        await page.get_by_text("Daily", exact=True).click()
        await page.wait_for_url("**/roundonedaily*", timeout=30000)

        logger.info("Clicking 'Continue to game' button")
        await page.get_by_text("Continue to game", exact=True).click()
        await page.wait_for_timeout(1000)

        logger.info("Checking for cookie consent dialog")
        dialog = page.locator(".fc-dialog.fc-choice-dialog")
        try:
            await dialog.wait_for(state="visible", timeout=15000)
            logger.info("Cookie dialog found, clicking 'do not consent'")
            await page.locator("button.fc-cta-do-not-consent").click()
            await dialog.wait_for(state="hidden", timeout=15000)
            logger.info("Cookie dialog dismissed")
        except PlaywrightTimeoutError:
            logger.info("No cookie dialog appeared")

    async def _click_map_coordinate_exact(self, location: Location) -> None:
        page = self.page
        map_locator = page.locator("#googleMap")
        await map_locator.scroll_into_view_if_needed()

        await page.wait_for_selector("#googleMap .mk-map-view", state="visible", timeout=30000)

        # hover first so the map expands
        await map_locator.hover()
        await page.wait_for_timeout(400)

        await page.wait_for_function(
            "() => window.mapkit && Array.isArray(mapkit.maps) && mapkit.maps.length > 0",
            timeout=30000,
        )

        pt = await page.evaluate(
            """([lat, lng]) => {
                const map = mapkit.maps[0];
                const coord = new mapkit.Coordinate(lat, lng);
                const p = map.convertCoordinateToPointOnPage(coord);
                return { x: p.x, y: p.y };
            }""",
            [location.lat, location.lng],
        )

        await page.mouse.click(pt["x"], pt["y"])
        await page.wait_for_timeout(200)

    async def _click_via_zoom(self, location: Location) -> None:
        page = self.page
        map_locator = page.locator("#googleMap")

        # hover first so the map expands
        await map_locator.hover()
        await page.wait_for_timeout(400)
        
        # Zoom in on the target location (higher zoom level)
        await page.evaluate(
            """([lat, lng]) => {
                const map = mapkit.maps[0];
                const coord = new mapkit.Coordinate(lat, lng);
                map.setCenterAnimated(coord, false);
                // Zoom in more
                const currentZoom = map.cameraDistance;
                map.cameraDistance = currentZoom * 0.3;
            }""",
            [location.lat, location.lng],
        )
        await page.wait_for_timeout(600)

        # Click the center of the map
        box = await map_locator.bounding_box()
        if box:
            center_x = box["x"] + box["width"] / 2
            center_y = box["y"] + box["height"] / 2
            await page.mouse.click(center_x, center_y)
        
        await page.wait_for_timeout(200)

    async def _place_pin(self, page: Page, location: Location) -> None:
        try:
            await self._click_map_coordinate_exact(location)

            await page.wait_for_function(
                "() => typeof localStorage.getItem('coords') === 'string' && localStorage.getItem('coords').length > 0",
                timeout=3000,
            )
        except PlaywrightTimeoutError:
            await self._click_via_zoom(location)

    async def click_year_slider(self, year: Year) -> None:
        page = self.page
        slider = page.locator("#myRange")
        await slider.wait_for(state="visible", timeout=30000)

        min_year = int((await slider.get_attribute("min")) or "1900")
        max_year = int((await slider.get_attribute("max")) or "2026")
        year = max(min_year, min(max_year, int(year)))

        await page.evaluate(
            """([year]) => {
                const slider = document.getElementById("myRange");
                slider.value = String(year);
                slider.dispatchEvent(new Event("input", { bubbles: true }));
                slider.dispatchEvent(new Event("change", { bubbles: true }));
            }""",
            [year],
        )

    async def make_guess(self, location: Location, year: Year) -> None:
        logger = logging.getLogger(__name__)
        page = self.page

        logger.info(f"Making guess: location=({location.lat}, {location.lng}), year={year}")
        
        # Reset coords
        await page.evaluate("() => localStorage.removeItem('coords')")
        logger.debug("Cleared previous coordinates")

        # 1) place pin
        logger.info("Placing pin on map")
        await self._place_pin(page, location)
        
        # wait until coords saved
        await page.wait_for_function(
                "() => typeof localStorage.getItem('coords') === 'string' && localStorage.getItem('coords').length > 0",
                timeout=10000,
        )
        logger.info("Pin placed successfully")

        # 2) set year
        logger.info(f"Setting year to {year}")
        await self.click_year_slider(year)

        # if coords got lost, re-place
        coords = await page.evaluate("() => localStorage.getItem('coords')")
        if not coords:
            logger.warning("Coordinates lost, re-placing pin")
            await self.click_map_coordinate_exact(location)  # ty:ignore[unresolved-attribute]
            await page.wait_for_function(
                "() => typeof localStorage.getItem('coords') === 'string' && localStorage.getItem('coords').length > 0",
                timeout=10000,
            )
            logger.info("Pin re-placed successfully")

        # 3) submit guess
        logger.info("Submitting guess")
        await page.locator("#makeGuess").click()
        logger.info("Guess submitted")

    async def go_to_next_round(self) -> None:
        next_round = self.page.locator("#nextRound")
        await next_round.wait_for(state="visible", timeout=30000)
        await next_round.click()

    async def get_answers(self) -> List[DailyRound]:
        logger = logging.getLogger(__name__)
        logger.info("Retrieving answers from localStorage")
        
        raw = await self.page.evaluate("() => localStorage.getItem('dailyArray')")
        if raw is None:
            logger.error("localStorage key 'dailyArray' not found")
            raise RuntimeError("localStorage key 'dailyArray' not found")

        data = json.loads(raw)[:5]
        logger.info(f"Retrieved {len(data)} daily rounds")
        logger.debug(f"Daily array data: {json.dumps(data, indent=2)}")
        return [DailyRound.model_validate(item) for item in data]

    async def get_results(self) -> str:
        """Formats the game results from localStorage into a shareable string."""
        logger = logging.getLogger(__name__)
        logger.info("Fetching game results from localStorage")
        
        # Get daily number
        daily_number = await self.page.evaluate("() => localStorage.getItem('dailyNumber')")
        logger.info(f"Daily number: {daily_number}")
        
        # Round names in order
        round_names = ["one", "two", "three", "four", "five"]
        
        # Collect all round data
        game_results: GameResults = GameResults(
            daily_number=int(daily_number) if daily_number and daily_number.isdigit() else 0,
            total_score=0,
            rounds=[]
        )
        
        for i, round_name in enumerate(round_names):
            # Get score, year, distance
            score: str = await self.page.evaluate(f"() => localStorage.getItem('{round_name}Total')")
            year: str = await self.page.evaluate(f"() => localStorage.getItem('{round_name}Year')")
            distance: str = await self.page.evaluate(f"() => localStorage.getItem('{round_name}Distance')")

            logger.info(f"Round {i+1}: score={score}, year={year}, distance={distance}")
            
            game_results.total_score += int(score) if score.isdigit() else 0
            game_results.rounds.append(DailyRoundResult(
                score=int(score) if score.isdigit() else 0,
                year=int(year) if year.isdigit() else 0,
                distance=distance,
            ))
        
        logger.info(f"Total score: {game_results.total_score}")
        return game_results.format_results()