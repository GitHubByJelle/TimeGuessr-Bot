from typing import Optional, Literal
from pydantic import BaseModel, HttpUrl


class Location(BaseModel):
    lat: float
    lng: float


class DailyRound(BaseModel):
    No: str
    URL: HttpUrl
    Year: str
    Location: Location
    Description: Optional[str] = None
    License: Optional[str] = None
    Country: Optional[str] = None
    StreetView: Optional[HttpUrl | Literal[""]] = None

class DailyRoundResult(BaseModel):
    score: int
    year: int
    distance: str

class GameResults(BaseModel):
    daily_number: int
    total_score: int
    rounds: list[DailyRoundResult]

    def format_results(self) -> str:
        result_lines = [f"TimeGuessr #{self.daily_number} - {self.total_score / 1000:.3f}/50.000\n"]
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
        for i, rd in enumerate(self.rounds):
            line = f"{emojis[i]} 🏆{rd.score} - 📅{rd.year}y - 🌍{rd.distance}"
            result_lines.append(line)
        
        result_lines.append("\nhttps://timeguessr.com")
        return "\n".join(result_lines)


class LLMLocation(BaseModel):
    country: str
    city: str
    street: Optional[str] = None
    building: Optional[str] = None

    def _build_query_strings(self) -> list[str]:
        """
        Fallback order:
        1) all info (country, city, street, building if present)
        2) country, city, street (if street present)
        3) country, city
        4) country
        """
        country = (self.country or "").strip()
        city = (self.city or "").strip()
        street = (self.street or "").strip() if self.street else ""
        building = (self.building or "").strip() if self.building else ""

        parts_all = [p for p in (building, street, city, country) if p]
        parts_ccs = [p for p in (street, city, country) if p]
        parts_cc = [p for p in (city, country) if p]
        parts_c = [p for p in (country,) if p]

        queries: list[str] = []
        if parts_all:
            queries.append(", ".join(parts_all))
        if parts_ccs:
            q = ", ".join(parts_ccs)
            if q not in queries:
                queries.append(q)
        if parts_cc:
            q = ", ".join(parts_cc)
            if q not in queries:
                queries.append(q)
        if parts_c:
            q = ", ".join(parts_c)
            if q not in queries:
                queries.append(q)

        return queries


class LLMGuessResponse(BaseModel):
    location: LLMLocation
    year: int


class AzureMapsPosition(BaseModel):
    lat: float
    lon: float


class AzureMapsResult(BaseModel):
    position: AzureMapsPosition


class AzureMapsResponse(BaseModel):
    results: list[AzureMapsResult]


