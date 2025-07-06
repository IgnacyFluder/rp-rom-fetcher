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


            size = None

            rows = soup.find_all("tr")
            for tr in rows:
               tds = tr.find_all("td")
               if len(tds) < 3:
                   continue
               
               link = tds[1].find("a")
               if not link or not link.has_attr("href"):
                   continue
               
               href = link["href"]
               if not href.startswith("/rom/") and not href.startswith("https://romhustler.org/rom/"):
                   continue
               
               title = link.get_text(strip=True)
               size = tds[2].get_text(strip=True)

               full_url = f"https://romhustler.org{href}" if href.startswith("/rom/") else href

               parts = full_url.strip("/").split("/")
               console_code = parts[4] if len(parts) >= 6 and parts[3] == "rom" else None

               results.append({
                   "title": title,
                   "url": full_url,
                   "source": self.name,
                   "size": size,
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

        # Look for the correct <a> that contains the download button
        value = None
        for tr in soup.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) != 2:
                continue

            strong = tds[0].find("strong")
            if strong and strong.get_text(strip=True).lower() == "can download":
                value = tds[1].get_text(strip=True).lower()
                value = value == "yes"
        print(value)    
        if value is None:
            raise ValueError("Download link not found on page.")
        elif value == False:
            raise ValueError("This game is restricted.")


        download_link = None
        for a in soup.find_all("a", href=True):
            if a.text.strip().lower() == "download":
                download_link = a["href"]
                break

        if not download_link:
            raise ValueError("Download link not found on page.")

        # RomHustler uses relative links
        if download_link.startswith("/"):
            return f"https://romhustler.org{download_link}"
        return download_link


if __name__ == "__main__":
    scraper = RomHustlerScraper()
    results = scraper.search("New Super Mario Bros")
    for result in results:
        print(result)
    
    print(scraper.get_download_url(results[0]["url"]))
