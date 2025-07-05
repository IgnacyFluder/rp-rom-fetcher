from abc import ABC, abstractmethod
from typing import List, Dict


class BaseScraper(ABC):
    """Abstract base class for ROM site scrapers."""

    name: str  # Human readable site name

    @abstractmethod
    def search(self, query: str) -> List[Dict]:
        """Return a list of dicts with keys: title, url, source, cover(optional), size(optional)"""
        raise NotImplementedError 