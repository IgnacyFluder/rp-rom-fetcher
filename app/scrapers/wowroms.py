import requests
from bs4 import BeautifulSoup
from typing import List, Dict
try:
    from .base import BaseScraper
except Exception:
    from base import BaseScraper

class WowRomsScraper(BaseScraper):
    name = "WowRoms"
    SEARCH_URL = "https://wowroms.com/en/roms/list?search={query}"
    BASE_URL = "https://wowroms.com"


    def search(self, query: str) -> List[Dict]:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
        }

        try:
            resp = requests.get(self.SEARCH_URL.format(query=requests.utils.quote(query)), headers=headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            wrapper = soup.find("div", id="sandBox-wrapper")
            if not wrapper:
                print("No search results wrapper found.")
                return []

            results = []
            for li in wrapper.select("li.element"):
                info = li.select_one(".group_info")
                if not info:
                    continue

                title_tag = info.select_one("a.title-5")
                if not title_tag:
                    continue
                title = title_tag.get_text(strip=True)
                url = self.BASE_URL + title_tag["href"]

                console_tag = info.select_one("a.col-title.colorRed")
                console = console_tag.get_text(strip=True) if console_tag else "Unknown"

                def extract(label: str):
                    tag = info.find("a", string=lambda t: t and label in t)
                    return tag.find("b").get_text(strip=True) if tag and tag.find("b") else None

                region = extract("Region")
                genre = extract("Genre")
                size = extract("File Size")
                downloads = extract("Downlaod")
                rating = extract("Rating")

                results.append({
                    "title": title,
                    "url": url,
                    "console": console,
                    "size": size,
                    "downloads": downloads,
                    "source": self.name,
                })

            return results
        except Exception as e:
            print(f"Error searching WowRoms: {e}")
            return []
        
    def get_download_url(self, url: str) -> str:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        return self.BASE_URL + soup.find("a", string='Download rom', href=True)["href"]


wr = WowRomsScraper()
search = wr.search("mario")
print(wr.get_download_url(search[0]["url"]))