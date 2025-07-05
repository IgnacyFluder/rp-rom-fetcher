# RetroPi ROM Downloader

A self-hosted Flask application that enables you to search, download, and manage game ROMs directly on your RetroPie.

## Features

* Search multiple ROM websites simultaneously (RomHustler, Vimm's Lair by default).
* Unified results view; games with multiple sources show a single entry with multiple download buttons.
* Background downloading with progress feedback via flash messages.
* Library view that displays all downloaded games with options to download the file or delete it (with confirmation prompt).
* Mobile-friendly and modern UI built with Bootstrap 5.

## ⚠️ Legal Notice

Downloading ROMs for games you do not own may violate copyright law in your jurisdiction. Use this tool responsibly and only download ROMs for which you have the legal right to do so.

## Requirements

* Python 3.9+
* Raspberry Pi running RetroPie (or any Linux/Windows machine)

Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Running on the Pi

```bash
export FLASK_APP=app.server
python -m flask run --host=0.0.0.0 --port=8000
```

Then navigate to `http://<pi-ip>:8000` on your phone or computer.

## Configuration

* `LIBRARY_DIR` is set to `library/` in the project root. You can move or symlink this to your ROMs directory so the games appear automatically in RetroPie.
* Add or remove scraper classes in `app/scrapers/__init__.py` to customize which ROM websites are queried.

## Roadmap / Ideas

* Show download progress bar in UI.
* Support additional ROM websites.
* Automatic extraction and placement into respective console folders.
* Caching search results to reduce repeated queries. 