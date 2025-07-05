import json
import logging
import requests
from typing import List, Dict, Optional
from .base import BaseScraper

LOGGER = logging.getLogger(__name__)


class ArchiveOrgScraper(BaseScraper):
    """Search Internet Archive for individual ROM files."""

    name = "Archive.org"

    ADV_SEARCH = (
        "https://archive.org/advancedsearch.php"
        "?q={query}"
        "&fl[]=identifier&fl[]=title&fl[]=mediatype"
        "&output=json&rows=50&page=1"
    )

    METADATA_URL = "https://archive.org/metadata/{identifier}"

    # allowed extensions we consider actual ROMs / archives
    ALLOWED_EXT = (
        ".zip",
        ".7z",
        ".rar",
        ".nes",
        ".sfc",
        ".smc",
        ".gba",
        ".gbc",
        ".gb",
        ".n64",
        ".z64",
        ".v64",
        ".iso",
        ".bin",
    )

    def _choose_file(self, identifier: str) -> Optional[Dict]:
        try:
            meta_resp = requests.get(self.METADATA_URL.format(identifier=identifier), timeout=15)
            meta_resp.raise_for_status()
            data = meta_resp.json()
            files = data.get("files", [])
            for f in files:
                name = f.get("name", "")
                if name.lower().endswith(self.ALLOWED_EXT):
                    size = f.get("size")
                    size_str = f"{int(size) / (1024 * 1024):.1f} MB" if size and size.isdigit() else None
                    url = f"https://archive.org/download/{identifier}/{name}"
                    console_code = None
                    # crude: check directory path or name for known consoles
                    lower_name = name.lower()
                    for key in (
                        "nes",
                        "snes",
                        "gba",
                        "gbc",
                        "gb",
                        "n64",
                        "psx",
                        "ps2",
                        "genesis",
                        "megadrive",
                    ):
                        if key in lower_name:
                            console_code = key
                            break
                    return {"url": url, "size": size_str, "console": console_code}
        except Exception as e:
            LOGGER.debug("Archive.org metadata failed: %s", e)
        return None

    def search(self, query: str) -> List[Dict]:
        results: List[Dict] = []
        try:
            api_url = self.ADV_SEARCH.format(query=requests.utils.quote(query))
            resp = requests.get(api_url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            for doc in data.get("response", {}).get("docs", []):
                identifier = doc["identifier"]
                title = doc.get("title", identifier)
                chosen = self._choose_file(identifier)
                if not chosen:
                    continue
                results.append(
                    {
                        "title": title,
                        "url": chosen["url"],
                        "source": self.name,
                        "size": chosen["size"],
                        "console": chosen["console"],
                    }
                )
        except Exception as e:
            LOGGER.debug("Archive.org search failed: %s", e)
        return results 