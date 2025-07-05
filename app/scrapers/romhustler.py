import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from .base import BaseScraper


class RomHustlerScraper(BaseScraper):
    name = "RomHustler"

    SEARCH_URL = "https://romhustler.org/roms/search?query={query}"

    def search(self, query: str) -> List[Dict]:
        results: List[Dict] = []
        try:
            url = self.SEARCH_URL.format(query=requests.utils.quote(query))
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            table = soup.find("table", {"class": "table-roms"})
            if not table:
                return results
            for row in table.find_all("tr"):
                cols = row.find_all("td")
                if len(cols) < 2:
                    continue
                title = cols[0].get_text(strip=True)
                link = cols[0].find("a")
                if not link:
                    continue
                href = link["href"]
                size = cols[1].get_text(strip=True) if len(cols) > 1 else None
                results.append(
                    {
                        "title": title,
                        "url": f"https://romhustler.org{href}",
                        "source": self.name,
                        "size": size,
                    }
                )
        except Exception:
            # Fail silently to avoid crashing the whole search
            pass
        return results 