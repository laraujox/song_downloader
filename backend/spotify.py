"""Read track metadata from Spotify (title, artist, duration).

Spotify audio is DRM-protected, so we never download from Spotify directly: we
only read metadata here, then `matching.py` re-finds the song on YouTube/SoundCloud.
Requires SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET; without them this is disabled.
"""
from . import config

_client = None


def _get_client():
    """Lazily build a Spotify client, or return None if credentials are missing."""
    global _client
    if _client is not None:
        return _client
    if not (config.SPOTIFY_CLIENT_ID and config.SPOTIFY_CLIENT_SECRET):
        print("Spotify credentials not set; skipping Spotify links.")
        return None

    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials

    _client = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=config.SPOTIFY_CLIENT_ID,
        client_secret=config.SPOTIFY_CLIENT_SECRET,
    ))
    return _client


def _format_track(item: dict, playlist_name: str | None = None) -> dict:
    return {
        "title": item["name"],
        "artist": ", ".join(artist["name"] for artist in item["artists"]),
        "duration": round(item["duration_ms"] / 1000),
        "playlist_name": playlist_name,
    }


def fetch_tracks(url: str) -> list[dict]:
    """Return metadata dicts for a Spotify track, album or playlist URL."""
    client = _get_client()
    if client is None:
        return []

    if "/track/" in url:
        return [_format_track(client.track(url))]

    if "/album/" in url:
        album = client.album(url)
        return [_format_track(item, album["name"]) for item in album["tracks"]["items"]]

    if "/playlist/" in url:
        playlist = client.playlist(url)
        name = playlist["name"]
        tracks = []
        page = playlist["tracks"]
        while page:
            for row in page["items"]:
                if row.get("track"):
                    tracks.append(_format_track(row["track"], name))
            page = client.next(page) if page.get("next") else None
        return tracks

    print(f"Unsupported Spotify URL: {url}")
    return []
