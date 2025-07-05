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
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                )
            }
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            table = soup.find("table", {"class": "table-roms"})
            if table:
                rows = table.find_all("tr")
            else:
                # Fallback: look for anchors pointing to individual ROM pages within #results box
                rows = []
                for a in soup.select("div#results a[href^='/rom']"):
                    fake_row = soup.new_tag("tr")
                    td_link = soup.new_tag("td")
                    td_link.append(a)
                    fake_row.append(td_link)
                    rows.append(fake_row)

            for row in rows:
                a = row.find("a", href=True)
                if not a:
                    continue
                title = a.get_text(strip=True)
                if not title:
                    continue
                href = a["href"]
                size_td = None
                tds = row.find_all("td")
                if len(tds) > 1:
                    size_td = tds[1].get_text(strip=True)

                # Extract console code from path '/rom/<console>/...' pattern
                console_code = None
                parts = href.strip("/").split("/")
                if len(parts) >= 3 and parts[0] == "rom":
                    console_code = parts[1]

                results.append(
                    {
                        "title": title,
                        "url": f"https://romhustler.org{href}",
                        "source": self.name,
                        "size": size_td,
                        "console": console_code,
                    }
                )
        except Exception:
            # Fail silently to avoid crashing the whole search
            pass

        # Deduplicate identical titles (same link may appear multiple times)
        seen = set()
        unique: List[Dict] = []
        for item in results:
            key = (item["title"], item["url"])
            if key in seen:
                continue
            seen.add(key)
            unique.append(item)

        return unique 