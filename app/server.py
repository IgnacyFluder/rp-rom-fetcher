import os
import threading
from urllib.parse import quote_plus, unquote_plus

import requests
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory

from .scrapers import SCRAPERS
from .utils import (
    unify_results,
    slugify_title,
    is_downloaded,
    get_downloaded_games,
    safe_filename,
    LIBRARY_DIR,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change_this_secret")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    if not query:
        flash("Please enter a game title to search.")
        return redirect(url_for("index"))

    all_results = []
    # Run scrapers sequentially to avoid blocking the Pi with too many threads
    for scraper in SCRAPERS:
        all_results.extend(scraper.search(query))
    games = unify_results(all_results)
    downloaded = set(get_downloaded_games())
    # Flag already downloaded
    for game in games:
        game["downloaded"] = game["slug"] in downloaded
    return render_template("search.html", query=query, games=games)


@app.route("/game/<slug>")
def game_detail(slug):
    title = slug.replace("-", " ")  # crude, but good enough for re-search
    all_results = []
    for scraper in SCRAPERS:
        all_results.extend(scraper.search(title))
    games = unify_results(all_results)
    game = next((g for g in games if g["slug"] == slug), None)
    if not game:
        flash("Game not found. Try searching again.")
        return redirect(url_for("index"))
    downloaded = is_downloaded(slug)
    return render_template("game.html", game=game, downloaded=downloaded)


def _download_file(url: str, dest_path: str):
    """Stream download to disk in a background thread."""
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
    except Exception as e:
        print(f"Failed download {url}: {e}")
        if os.path.exists(dest_path):
            os.remove(dest_path)


@app.route("/download")
def download():
    url = request.args.get("url")
    title = request.args.get("title")
    if not url or not title:
        flash("Invalid download request.")
        return redirect(url_for("index"))
    slug = slugify_title(title)
    if is_downloaded(slug):
        flash("You already downloaded this game.")
        return redirect(url_for("game_detail", slug=slug))
    filename = safe_filename(f"{slug}{os.path.splitext(url)[-1] or '.zip'}")
    dest_path = os.path.join(LIBRARY_DIR, filename)
    flash("Download started in background. It may take a while depending on file size.")
    threading.Thread(target=_download_file, args=(url, dest_path), daemon=True).start()
    return redirect(url_for("game_detail", slug=slug))


@app.route("/library")
def library():
    files = os.listdir(LIBRARY_DIR)
    # Build objects: title, slug, filename
    games = []
    for fname in files:
        slug = fname.split(".")[0]
        title = slug.replace("-", " ").title()
        games.append({"title": title, "slug": slug, "filename": fname})
    return render_template("library.html", games=games)


@app.route("/delete/<path:filename>", methods=["POST"])
def delete_file(filename):
    path = os.path.join(LIBRARY_DIR, filename)
    if os.path.exists(path):
        os.remove(path)
        flash("Game deleted successfully.")
    else:
        flash("File not found.")
    return redirect(url_for("library"))


@app.route("/library/downloads/<path:filename>")
def serve_download(filename):
    return send_from_directory(LIBRARY_DIR, filename, as_attachment=True)


if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    app.run(host=host, port=port, debug=True) 