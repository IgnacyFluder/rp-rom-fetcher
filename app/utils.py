import os
from typing import List, Dict
from slugify import slugify

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