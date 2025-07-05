import requests
from bs4 import BeautifulSoup
from typing import List, Dict

try:
    from .base import BaseScraper
except Exception:
    from base import BaseScraper


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

            # Look for any anchor tag with href starting with "/rom/"
            anchors = soup.find_all("a", href=True)
            for a in anchors:
                href = a["href"]
                if not href.startswith("https://romhustler.org/rom/"):
                    continue

                title = a.get_text(strip=True)
                if not title:
                    continue

                # Construct full URL if missing the base URL
                full_url = f"https://romhustler.org{href}" if not href.startswith("https://romhustler.org") else href

                # Extract console code from URL (e.g., /rom/wii/... should give 'wii')
                parts = href.strip("/").split("/")
                console_code = parts[4] if len(parts) >= 6 and parts[3] == "rom" else None
                print(parts[5], parts[4], len(parts))
                results.append({
                    "title": title,
                    "url": full_url,
                    "source": self.name,
                    "size": None,  # Size isn't available in this version
                    "console": console_code,
                })

        except Exception as e:
            print(f"Error in RomHustlerScraper: {e}")

        # Deduplicate based on title + URL
        seen = set()
        unique: List[Dict] = []
        for item in results:
            key = (item["title"], item["url"])
            if key in seen:
                continue
            seen.add(key)
            unique.append(item)

        return unique


if __name__ == "__main__":
    scraper = RomHustlerScraper()
    results = scraper.search("New Super Mario Bros")
    for result in results:
        print(result)
