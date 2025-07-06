import os
from typing import List, Dict
from slugify import slugify
import requests
from bs4 import BeautifulSoup

# Base RetroPie roms directory (can be overridden via env)
ROMS_BASE_DIR = os.environ.get("ROMS_BASE_DIR", os.path.expanduser("~/RetroPie/roms"))
# Ensure base dir exists so tests/development don't explode. (On non-Pi hosts this will just create a folder)
os.makedirs(ROMS_BASE_DIR, exist_ok=True)

# Simple mapping of console codes (as reported by scrapers) → directory names in RetroPie.
# You can extend this mapping if you add more systems.
CONSOLE_DIR_MAP = {
    "nes": "nes",
    "snes": "snes",
    "gba": "gba",
    "gbc": "gbc",
    "gb": "gb",
    "genesis": "genesis",
    "megadrive": "megadrive",
    "n64": "n64",
    "psx": "psx",
    "ps2": "ps2",
    "mame": "mame-libretro",
    "arcade": "arcade",
}


def slugify_title(title: str) -> str:
    """Generate a URL-safe slug from a game title."""
    return slugify(title, lowercase=True)


def is_downloaded(slug: str) -> bool:
    """Return True if any file starting with slug exists anywhere under `ROMS_BASE_DIR`."""
    for root, _dirs, files in os.walk(ROMS_BASE_DIR):
        for fname in files:
            if fname.startswith(slug):
                return True
    return False


def get_downloaded_games() -> List[str]:
    """Return slugs for all games found under `ROMS_BASE_DIR`."""
    slugs: List[str] = []
    for root, _dirs, files in os.walk(ROMS_BASE_DIR):
        for fname in files:
            if fname.lower().endswith((
                ".zip",
                ".7z",
                ".rar",
                ".nes",
                ".sfc",
                ".smc",
                ".gba",
                ".gb",
                ".gbc",
                ".n64",
                ".z64",
                ".v64",
                ".bin",
                ".iso",
            )):
                slugs.append(fname.split(".")[0])
    return slugs


def unify_results(results: List[Dict]) -> List[Dict]:
    """Merge multiple scraper results, combining identical titles.

    Each item in results should have at minimum: title, url, source, and optionally cover.
    """
    merged: Dict[str, Dict] = {}
    for item in results:
        slug = slugify_title(item["title"])
        if slug not in merged:
            merged[slug] = {
                "title": item["title"],
                "slug": slug,
                "cover": item.get("cover"),
                "sources": [],
                "console": item.get("console"),
            }
        merged[slug]["sources"].append({
            "source": item["source"],
            "url": item["url"],
            "size": item.get("size"),
            "console": item.get("console"),
        })
    # Convert to list sorted by title
    return sorted(merged.values(), key=lambda x: x["title"].lower())


def safe_filename(filename: str) -> str:
    """Sanitize filenames to avoid filesystem issues."""
    keep = "_.-() "
    return "".join(c for c in filename if c.isalnum() or c in keep)


def console_to_dir(console: str) -> str:
    """Return the RetroPie directory for a given console code."""
    return CONSOLE_DIR_MAP.get(console.lower(), "unsorted") 


def is_downloadable(url: str) -> bool:
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Find all table rows
        for tr in soup.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) != 2:
                continue

            strong = tds[0].find("strong")
            if strong and strong.get_text(strip=True).lower() == "can download":
                value = tds[1].get_text(strip=True).lower()
                return value == "yes"

        return False  # "Can Download" not found

    except Exception as e:
        print(f"Error checking downloadability: {e}")
        return False


def normalize_console_name(console_name: str) -> str:
    name_map = {
        "Nintendo Entertainment System": "NES",
        "Super Nintendo Entertainment System": "SNES",
        "Nintendo 64": "N64",
        "Nintendo Game Boy": "Game Boy",
        "Nintendo Game Boy Color": "GBC",
        "Nintendo Game Boy Advance": "GBA",
        "Nintendo DS": "DS",
        "Nintendo 3DS": "3DS",
        "Nintendo Switch": "Switch",
        "Sony PlayStation": "PS1",
        "Sony PlayStation 2": "PS2",
        "Sony PlayStation 3": "PS3",
        "Sony PlayStation Portable": "PSP",
        "Microsoft Xbox": "Xbox",
        "Microsoft Xbox 360": "Xbox 360",
        "Sega Genesis": "Genesis",
        "Sega Mega Drive": "Genesis",
        "Sega Master System": "Master System",
        "Sega Dreamcast": "Dreamcast",
        "Atari 2600": "Atari 2600",
        "Atari 5200": "Atari 5200",
        "Atari 7800": "Atari 7800",
        "Atari Jaguar": "Jaguar",
        "Commodore 64": "C64",
        "Neo Geo": "Neo Geo",
        "TurboGrafx-16": "TG16",
        "PC Engine": "TG16",
        "MAME": "MAME",
    }

    return name_map.get(console_name.strip(), console_name.strip().upper())