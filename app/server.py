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
    ROMS_BASE_DIR,
    console_to_dir,
    is_downloadable,
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


import os
import threading
import requests
from urllib.parse import unquote
from flask import flash, redirect, url_for

def _get_filename_from_cd(content_disposition: str) -> str:
    """
    Extract filename from Content-Disposition header.
    """
    if not content_disposition:
        return None
    parts = content_disposition.split(';')
    for part in parts:
        if "filename=" in part:
            filename = part.split("filename=")[-1].strip(' "\'')
            return unquote(filename)
    return None

def _download_file(url: str, dest_dir: str, slug: str = None, console: str = None):
    """Stream download to disk in a background thread."""
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()

            # Get filename from Content-Disposition or fallback to URL
            content_disposition = r.headers.get("Content-Disposition")
            filename = _get_filename_from_cd(content_disposition)

            if not filename:
                filename = os.path.basename(url.split("?")[0]) or f"{slug}.zip"

            if slug:
                filename = safe_filename(f"{slug}{os.path.splitext(filename)[-1]}")

            # Create directory
            console_dir_name = console_to_dir(console) if console else "unsorted"
            full_dir = os.path.join(ROMS_BASE_DIR, console_dir_name)
            os.makedirs(full_dir, exist_ok=True)

            # Write file
            dest_path = os.path.join(full_dir, filename)
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
    console = request.args.get("console")  # optional hint from scraper/UI
    scraper_name = request.args.get("source")

    if not url or not title:
        flash("Invalid download request.")
        return redirect(url_for("index"))
    
    slug = slugify_title(title)
    if is_downloaded(slug):
        flash("You already downloaded this game.")
        return redirect(url_for("game_detail", slug=slug))
    
    download_url = None

    for scraper in SCRAPERS:
        if scraper.name == scraper_name:
            try:
                download_url = scraper.get_download_url(url)
            except TypeError:
                flash("This game is restricted, download did not start.")
                return redirect(url_for("game_detail", slug=slug))
            except ValueError:
                flash("This game is restricted, download did not start.")
                return redirect(url_for("game_detail", slug=slug))
            except Exception as e:
                flash(f"Error downloading game: {str(e)}")
                return redirect(url_for("game_detail", slug=slug))

    console_dir_name = console_to_dir(console) if console else "unsorted"
    dest_dir = os.path.join(ROMS_BASE_DIR, console_dir_name)

    os.makedirs(dest_dir, exist_ok=True)
    # if not is_downloadable(url):
    #     flash("This game is restricted, download did not start.")
    #     return redirect(url_for("game_detail", slug=slug))
    flash("Download started in background. It may take a while depending on file size.")
    threading.Thread(target=_download_file, args=(download_url, ROMS_BASE_DIR), kwargs={"slug": slug, "console": console}, daemon=True).start()
    return redirect(url_for("game_detail", slug=slug))


@app.route("/library")
def library():
    games = []
    for console in os.listdir(ROMS_BASE_DIR):
        console_path = os.path.join(ROMS_BASE_DIR, console)
        if not os.path.isdir(console_path):
            continue
        for fname in os.listdir(console_path):
            slug = fname.split(".")[0]
            title = slug.replace("-", " ").title()
            games.append({
                "title": title,
                "slug": slug,
                "filename": fname,
                "console": console,
            })
    return render_template("library.html", games=games)


@app.route("/delete/<console>/<path:filename>", methods=["POST"])
def delete_file(console, filename):
    path = os.path.join(ROMS_BASE_DIR, console, filename)
    if os.path.exists(path):
        os.remove(path)
        flash("Game deleted successfully.")
    else:
        flash("File not found.")
    return redirect(url_for("library"))


@app.route("/library/downloads/<console>/<path:filename>")
def serve_download(console, filename):
    directory = os.path.join(ROMS_BASE_DIR, console)
    return send_from_directory(directory, filename, as_attachment=True)


if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    app.run(host=host, port=port, debug=True) 