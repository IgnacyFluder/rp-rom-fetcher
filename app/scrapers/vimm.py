import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from .base import BaseScraper


class VimmScraper(BaseScraper):
    name = "Vimm's Lair"

    SEARCH_URL = "https://vimm.net/vault/?p=list&search={query}"

    def search(self, query: str) -> List[Dict]:
        results: List[Dict] = []
        try:
            url = self.SEARCH_URL.format(query=requests.utils.quote(query))
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            tbody = soup.find("tbody")
            if not tbody:
                return results
            for row in tbody.find_all("tr"):
                cols = row.find_all("td")
                if not cols:
                    continue
                link = cols[0].find("a")
                if not link:
                    continue
                title = link.get_text(strip=True)
                href = link["href"]
                size = cols[-1].get_text(strip=True) if len(cols) > 1 else None
                results.append(
                    {
                        "title": title,
                        "url": f"https://vimm.net{href}",
                        "source": self.name,
                        "size": size,
                    }
                )
        except Exception:
            pass
        return results 