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
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                )
            }
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            tbody = soup.find("tbody")
            if tbody:
                rows = tbody.find_all("tr")
            else:
                # Fallback: anchors inside table rows with vault list
                rows = soup.select("table tr")

            for row in rows:
                link = row.find("a", href=True)
                if not link:
                    continue
                title = link.get_text(strip=True)
                href = link["href"]
                cols = row.find_all("td")
                size = cols[-1].get_text(strip=True) if len(cols) > 1 else None
                console_code = None
                if len(cols) >= 2:
                    console_code = cols[1].get_text(strip=True).lower()
                results.append(
                    {
                        "title": title,
                        "url": f"https://vimm.net{href}",
                        "source": self.name,
                        "size": size,
                        "console": console_code,
                    }
                )
        except Exception:
            pass

        # Deduplicate
        seen = set()
        unique: List[Dict] = []
        for item in results:
            key = (item["title"], item["url"])
            if key in seen:
                continue
            seen.add(key)
            unique.append(item)

        return unique 