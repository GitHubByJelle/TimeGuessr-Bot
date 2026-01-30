from __future__ import annotations

import base64
from typing import Optional

import aiohttp
from openai import OpenAI

from src.bots.base import BaseBot
from src.custom_types import Guess
from src.model import (
    AzureMapsResponse,
    AzureMapsResult,
    DailyRound,
    LLMGuessResponse,
    LLMLocation,
    Location,
)
from src.settings import settings


class LLMBot(BaseBot):
    """
    Uses Azure OpenAI vision model to analyze TimeGuessr images
    and guess both location and year.
    """

    name = "GPT 5.2 🤖"

    def __init__(self):
        self.client = OpenAI(
            base_url=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
        )

    async def guess_for_round(self, round_index: int, round_data: Optional[DailyRound]) -> Guess:
        if round_data is None:
            raise ValueError("LLMBot requires round_data to get the image URL")

        image_url = str(round_data.URL)
        img_uri = await self._download_image_base64(image_url)

        llm_response: LLMGuessResponse = self._get_llm_guess(img_uri)
        location: Location = await self._location_to_coordinates(llm_response.location)

        return (location, llm_response.year)

    def _get_llm_guess(self, image_uri: str) -> LLMGuessResponse:
        """Get structured guess from the LLM using the image."""
        response = self.client.responses.parse(
            model="gpt-5.2-chat",
            input=[
                {
                    "role": "developer",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "You are an AI assisstant that helps me to play TimeGuessr. TimeGuessr is a game where you have to guess a location and year, based on a given image. Your goal is to estimate both of them, by considering the details in the image together with the world events. In your final answer, do not explain your answer, since I am using the location in an url.",
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_image",
                            "image_url": image_uri,
                        }
                    ],
                },
            ],  # ty:ignore[invalid-argument-type]
            text_format=LLMGuessResponse,
            reasoning={"effort": "medium"},
            tools=[],
            store=True,
            include=["reasoning.encrypted_content", "web_search_call.action.sources"],  # ty:ignore[invalid-argument-type]
        )

        answer: Optional[LLMGuessResponse] = response.output_parsed
        if answer is None:
            raise ValueError("No answer received from the model.")

        return answer

    async def _download_image_base64(self, url: str) -> str:
        """Download an image from a URL and return it as a data URI for OpenAI."""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status < 200 or resp.status >= 300:
                    text = await resp.text()
                    raise aiohttp.ClientResponseError(
                        request_info=resp.request_info,
                        history=resp.history,
                        status=resp.status,
                        message=text,
                        headers=resp.headers,
                    )
                content = await resp.read()
                content_type = resp.headers.get("Content-Type", "image/jpeg")
                base64_data = base64.b64encode(content).decode("utf-8")
                return f"data:{content_type};base64,{base64_data}"

    async def _azure_maps_search(
        self,
        session: aiohttp.ClientSession,
        query: str,
        *,
        base_url: str = "https://atlas.microsoft.com/search/address/json",
    ) -> list[AzureMapsResult]:
        """
        Async GET request to Azure Maps Search API.
        """
        params = {
            "subscription-key": settings.AZURE_MAPS_KEY,
            "api-version": "1.0",
            "language": "en-US",
            "query": query,
        }

        async with session.get(base_url, params=params) as resp:
            if resp.status < 200 or resp.status >= 300:
                text = await resp.text()
                raise aiohttp.ClientResponseError(
                    request_info=resp.request_info,
                    history=resp.history,
                    status=resp.status,
                    message=text,
                    headers=resp.headers,
                )

            data = await resp.json()
            response_obj = AzureMapsResponse.model_validate(data)
            return response_obj.results

    async def _location_to_coordinates(self, location: LLMLocation) -> Location:
        """
        Tries progressively less specific queries until Azure Maps returns a result.
        Raises ValueError if nothing can be found even with the country-only fallback.
        """
        queries = location._build_query_strings()

        timeout = aiohttp.ClientTimeout(total=15)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            for q in queries:
                results = await self._azure_maps_search(session, q)
                if results:
                    r: AzureMapsResult = results[0]
                    return Location(lat=r.position.lat, lng=r.position.lon)

        raise ValueError(f"No coordinates found for location using fallbacks: {queries}")