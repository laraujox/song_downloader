"""Recover real metadata for SoundCloud tracks straight from SoundCloud's API.

Why this exists: SoundCloud playlists expand (via yt-dlp flat extraction) into bare
`api-v2.soundcloud.com/tracks/<id>` URLs with no title, and DRM-protected tracks
refuse extraction entirely — so we'd be left searching for "unknown". The public
SoundCloud API still returns the title, artist, duration and a real page URL for
those tracks, which is exactly what we need to re-find them on YouTube and to show
the user a useful name. Best-effort: every call degrades gracefully to None.
"""
import re
import threading
import time

import requests
import yt_dlp

_API = "https://api-v2.soundcloud.com"
_TRACK_ID = re.compile(r"/tracks/(\d+)")
_TRAILING_LABEL = re.compile(r"\s*\([^)]*\)\s*$")  # "Jumpstreet (Looney Moon)" -> "Jumpstreet"
_RETRIES = 4  # SoundCloud rate-limits bursts; retry with backoff so enrichment is reliable.

_client_id = None
_client_id_lock = threading.Lock()
_session = requests.Session()


def _get_client_id() -> str | None:
    """Reuse yt-dlp's resolver to obtain a working SoundCloud client_id (cached, once)."""
    global _client_id
    with _client_id_lock:
        if _client_id:
            return _client_id
        try:
            ydl = yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "skip_download": True})
            extractor = ydl.get_info_extractor("Soundcloud")
            extractor.set_downloader(ydl)
            extractor._CLIENT_ID = None
            extractor._update_client_id()
            _client_id = getattr(extractor, "_CLIENT_ID", None)
        except Exception as error:
            print(f"[soundcloud] could not resolve client_id: {error}")
            _client_id = None
        return _client_id


def warm_client_id() -> None:
    """Resolve and cache the client_id up front so parallel callers don't all race for it."""
    _get_client_id()


def _get_json(url: str, params: dict) -> dict | None:
    """GET with retry/backoff so SoundCloud's aggressive rate limiting doesn't lose tracks."""
    for attempt in range(_RETRIES):
        try:
            response = _session.get(url, params=params, timeout=20)
            if response.status_code == 429:  # rate limited — wait and retry
                time.sleep(1.5 * (attempt + 1))
                continue
            if response.ok:
                return response.json()
        except Exception:
            time.sleep(1.0 * (attempt + 1))
    return None


def _track_id(url: str, client_id: str) -> str | None:
    match = _TRACK_ID.search(url or "")
    if match:
        return match.group(1)
    data = _get_json(f"{_API}/resolve", {"url": url, "client_id": client_id})
    track_id = data.get("id") if data else None
    return str(track_id) if track_id else None


def track_meta(url: str) -> dict | None:
    """Return {title, artist, duration, permalink} for a SoundCloud URL, or None."""
    client_id = _get_client_id()
    if not client_id:
        return None
    track_id = _track_id(url, client_id)
    if not track_id:
        return None
    data = _get_json(f"{_API}/tracks/{track_id}", {"client_id": client_id})
    if not data or not data.get("title"):
        return None
    username = (data.get("user") or {}).get("username")
    # Go+ tracks expose a short preview as `duration`; `full_duration` is the real length.
    milliseconds = data.get("full_duration") or data.get("duration") or 0
    return {
        "title": data["title"],
        "artist": _TRAILING_LABEL.sub("", username) if username else None,
        "duration": round(milliseconds / 1000) or None,
        "permalink": data.get("permalink_url"),
    }
