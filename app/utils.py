import os
from typing import List, Dict
from slugify import slugify

LIBRARY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "library")
os.makedirs(LIBRARY_DIR, exist_ok=True)


def slugify_title(title: str) -> str:
    """Generate a URL-safe slug from a game title."""
    return slugify(title, lowercase=True)


def is_downloaded(slug: str) -> bool:
    """Check if a ROM with the given slug is already downloaded."""
    for fname in os.listdir(LIBRARY_DIR):
        if fname.startswith(slug):
            return True
    return False


def get_downloaded_games() -> List[str]:
    """Return a list of slugs for downloaded games."""
    games = []
    for fname in os.listdir(LIBRARY_DIR):
        if fname.endswith((".zip", ".7z", ".rar", ".nes", ".sfc", ".gba", ".gb", ".gbc")):
            slug = fname.split(".")[0]
            games.append(slug)
    return games


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
            }
        merged[slug]["sources"].append({
            "source": item["source"],
            "url": item["url"],
            "size": item.get("size"),
        })
    # Convert to list sorted by title
    return sorted(merged.values(), key=lambda x: x["title"].lower())


def safe_filename(filename: str) -> str:
    """Sanitize filenames to avoid filesystem issues."""
    keep = "_.-() "
    return "".join(c for c in filename if c.isalnum() or c in keep) 