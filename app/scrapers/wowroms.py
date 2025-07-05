import requests
from bs4 import BeautifulSoup
from typing import List, Dict

from .base import BaseScraper


class WowRomsScraper(BaseScraper):
    name = "WowRoms"

    SEARCH_URL = "https://wowroms.com/en/search?q={query}"

    def search(self, query: str) -> List[Dict]:
        results: List[Dict] = []
        try:
            url = self.SEARCH_URL.format(query=requests.utils.quote(query))
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.select("a.link-game[href]"):
                title = a.get("title") or a.get_text(strip=True)
                href = a.get("href")
                if not title or not href:
                    continue
                # href pattern /en/roms/<console>/<slug>
                parts = href.strip("/").split("/")
                console = parts[2] if len(parts) > 3 else None
                results.append({
                    "title": title,
                    "url": f"https://wowroms.com{href}",
                    "source": self.name,
                    "console": console,
                })
                if len(results) >= 10:
                    break
        except Exception:
            pass
        return results 