from typing import Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from src.model import Location

Year = int
Guess = Tuple["Location", Year]
