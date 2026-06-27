"""Turn raw user URLs into a flat list of Tracks ready to download.

A single URL and a playlist URL are handled the same way: a single URL simply
produces a one-item list, so the rest of the pipeline never special-cases it.
"""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from urllib.parse import urlparse

import yt_dlp

from . import soundcloud, spotify


@dataclass
class Track:
    """One song flowing through the pipeline."""
    title: str
    source: str  # "youtube" | "soundcloud" | "spotify" | "direct"
    source_url: str | None = None  # known download URL (None when we must search)
    artist: str | None = None
    expected_duration: int | None = None  # seconds, used to verify the match
    needs_search: bool = False  # True when we only have metadata (e.g. Spotify)
    playlist_name: str | None = None  # subfolder to save into


_FLAT_OPTIONS = {
    "quiet": True,
    "no_warnings": True,
    "extract_flat": True,
    "skip_download": True,
}


def title_from_url(url: str) -> str:
    """Readable name guessed from a URL slug, e.g. .../01-indira-paganotto-kalima.

    Used as an instant placeholder (and as a search query) when the platform's
    flat playlist listing doesn't include track titles.
    """
    slug = urlparse(url or "").path.rstrip("/").split("/")[-1]
    words = slug.replace("_", " ").replace("-", " ").split()
    if words and words[0].isdigit():  # drop a leading "01" track number
        words = words[1:]
    return " ".join(word.capitalize() for word in words) if words else "unknown"


def _detect_source(url: str) -> str:
    lowered = url.lower()
    if "spotify.com" in lowered:
        return "spotify"
    if "soundcloud.com" in lowered:
        return "soundcloud"
    if "youtube.com" in lowered or "youtu.be" in lowered:
        return "youtube"
    return "direct"


def _expand_with_ytdlp(url: str, source: str) -> list[Track]:
    """Expand a YouTube/SoundCloud URL into tracks (one item if it's a single song)."""
    with yt_dlp.YoutubeDL(_FLAT_OPTIONS) as ydl:
        info = ydl.extract_info(url, download=False)

    entries = info.get("entries")
    if not entries:  # single track
        return [Track(
            title=info.get("title", "unknown"),
            source=source,
            source_url=url,
            expected_duration=info.get("duration"),
        )]

    playlist_name = info.get("title")
    tracks = []
    for entry in entries:
        if not entry:
            continue
        entry_url = entry.get("url")
        # Flat listings (especially SoundCloud) often omit titles; fall back to the slug.
        tracks.append(Track(
            title=entry.get("title") or title_from_url(entry_url),
            source=source,
            source_url=entry_url,
            artist=entry.get("uploader") or entry.get("channel"),
            expected_duration=entry.get("duration"),
            playlist_name=playlist_name,
        ))

    if source == "soundcloud":
        _enrich_soundcloud(tracks)
    return tracks


def _enrich_soundcloud(tracks: list[Track]) -> None:
    """Fill in real title/artist/duration (and a clean page URL) from SoundCloud's API.

    SoundCloud flat listings give us no titles and bare api-v2 track-id URLs, so
    without this most tracks would read "unknown" and DRM ones couldn't be re-found.
    Done in parallel since it's one HTTP call per track. Best-effort per track.
    """
    needing = [track for track in tracks if not track.expected_duration or not track.artist]
    soundcloud.warm_client_id()  # resolve the shared client_id once, before the burst

    def fill(track: Track) -> None:
        meta = soundcloud.track_meta(track.source_url)
        if not meta:
            return
        track.title = meta["title"] or track.title
        track.artist = meta["artist"] or track.artist
        track.expected_duration = meta["duration"] or track.expected_duration
        if meta["permalink"]:
            track.source_url = meta["permalink"]  # real page beats the api-v2 id URL

    # Modest concurrency: SoundCloud rate-limits bursts, and track_meta already retries.
    with ThreadPoolExecutor(max_workers=3) as pool:
        pool.map(fill, needing)


def _spotify_tracks(url: str) -> list[Track]:
    """Spotify songs become search jobs: we only have metadata, not a download URL."""
    tracks = []
    for song in spotify.fetch_tracks(url):
        tracks.append(Track(
            title=song["title"],
            artist=song["artist"],
            source="spotify",
            expected_duration=song["duration"],
            needs_search=True,
            playlist_name=song.get("playlist_name"),
        ))
    return tracks


def resolve_inputs(urls: list[str]) -> list[Track]:
    """Resolve every input URL into concrete Tracks, skipping any that fail."""
    resolved: list[Track] = []
    for url in (u.strip() for u in urls if u.strip()):
        source = _detect_source(url)
        try:
            if source == "spotify":
                resolved.extend(_spotify_tracks(url))
            else:
                resolved.extend(_expand_with_ytdlp(url, source))
        except Exception as error:
            print(f"Could not resolve {url}: {error}")
    return resolved
