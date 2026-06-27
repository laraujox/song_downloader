"""Find the correct upload for a track we only have metadata for (the accuracy core).

Two-stage search for precision *and* speed:
1. A fast flat search on each platform (YouTube + SoundCloud) to gather a shortlist.
2. A full extraction of only the best few shortlisted results, which gives the real
   page URL, the true duration and the uploader/artist — and quietly drops anything
   that's DRM-locked, deleted or geo-blocked, so we only ever offer downloadable links.

Candidates are then scored on title similarity, artist match and duration closeness,
deduped, and returned best-first.
"""
from difflib import SequenceMatcher

import yt_dlp

from . import config

_FLAT_OPTIONS = {
    "quiet": True,
    "no_warnings": True,
    "extract_flat": True,
    "skip_download": True,
}
_FULL_OPTIONS = {
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
    "noplaylist": True,
    "socket_timeout": 30,
}
_RESULTS_PER_PLATFORM = 5
# Cruft that platforms (mostly YouTube) bolt onto titles and that shouldn't affect
# matching. Version words (remix, extended, original, edit, radio) are kept on purpose.
_NOISE_WORDS = {
    "official", "video", "audio", "hd", "hq", "lyrics", "lyric", "visualizer",
    "visualiser", "mv", "premiere", "out", "now", "free",
}


def _platform(url: str) -> str:
    lowered = url.lower()
    if "soundcloud.com" in lowered:
        return "soundcloud"
    if "youtube.com" in lowered or "youtu.be" in lowered:
        return "youtube"
    return "other"


def _normalize(text: str) -> str:
    cleaned = "".join(char.lower() if char.isalnum() else " " for char in text)
    words = [word for word in cleaned.split() if word not in _NOISE_WORDS]
    return " ".join(words)


def _title_similarity(query: str, candidate_title: str) -> float:
    """Blend sequence ratio with query-coverage so extra label tags don't hurt."""
    query_norm, candidate_norm = _normalize(query), _normalize(candidate_title)
    if not query_norm or not candidate_norm:
        return 0.0
    sequence = SequenceMatcher(None, query_norm, candidate_norm).ratio()
    query_words, candidate_words = set(query_norm.split()), set(candidate_norm.split())
    coverage = len(query_words & candidate_words) / len(query_words)
    return max(sequence, coverage)


def _artist_match(artist: str | None, candidate_title: str, uploader: str | None) -> float:
    """How many of the expected artist's name-words show up in the result."""
    if not artist:
        return 0.5  # unknown — stay neutral
    haystack = _normalize(f"{candidate_title} {uploader or ''}")
    artist_words = [word for word in _normalize(artist).split() if len(word) > 2]
    if not artist_words:
        return 0.5
    hits = sum(1 for word in artist_words if word in haystack)
    return hits / len(artist_words)


def _duration_score(expected: int | None, actual: int | None) -> float:
    """1.0 when within tolerance, decaying toward 0 the further off it is."""
    if not expected or not actual:
        return 0.5  # unknown — stay neutral
    difference = abs(expected - actual)
    if difference <= config.DURATION_TOLERANCE_SECONDS:
        return 1.0
    return max(0.0, 1.0 - difference / expected)


def _score(query, artist, title, uploader, expected_duration, duration) -> float:
    return (
        config.TITLE_WEIGHT * _title_similarity(query, title)
        + config.ARTIST_WEIGHT * _artist_match(artist, title, uploader)
        + config.DURATION_WEIGHT * _duration_score(expected_duration, duration)
    )


def _flat_search(query_prefix: str, query: str) -> list[dict]:
    search_term = f"{query_prefix}{_RESULTS_PER_PLATFORM}:{query}"
    try:
        with yt_dlp.YoutubeDL(_FLAT_OPTIONS) as ydl:
            info = ydl.extract_info(search_term, download=False)
        return info.get("entries", []) or []
    except Exception as error:
        print(f"[match] flat search failed for '{search_term}': {error}")
        return []


def _verify(url: str) -> dict | None:
    """Fully extract one result to get its real page URL + true metadata.

    Returns None for anything unavailable (DRM, deleted, geo-blocked) — which is
    exactly what we want, since we only ever present links that can be downloaded.
    """
    try:
        with yt_dlp.YoutubeDL(_FULL_OPTIONS) as ydl:
            return ydl.extract_info(url, download=False)
    except Exception:
        return None


def search_candidates(query: str, expected_duration: int | None = None,
                      artist: str | None = None) -> list[dict]:
    """Search YouTube + SoundCloud and return verified candidates ranked best-first.

    Each candidate is {"url" (real page URL), "title", "source", "score", "duration"}.
    The downloader tries them in order; the review UI uses the same list to audition.
    """
    raw = _flat_search("ytsearch", query) + _flat_search("scsearch", query)

    # Pre-rank cheaply on title alone so we only pay for full extraction on the best few.
    shortlist = sorted(
        (entry for entry in raw if entry.get("url") or entry.get("webpage_url")),
        key=lambda entry: _title_similarity(query, entry.get("title", "")),
        reverse=True,
    )[:config.VERIFY_LIMIT]

    candidates = []
    seen = set()
    for entry in shortlist:
        info = _verify(entry.get("url") or entry.get("webpage_url"))
        if not info:
            continue
        page_url = info.get("webpage_url") or entry.get("url")
        duration = info.get("duration")
        title = info.get("title", "")
        # Drop unavailable, implausible-length, or duplicate results.
        if not page_url or page_url in seen:
            continue
        if duration and not (config.MIN_SECONDS <= duration <= config.MAX_SECONDS):
            continue
        dedupe_key = (_normalize(title), round((duration or 0) / 5))
        if dedupe_key in seen:
            continue
        seen.update({page_url, dedupe_key})

        uploader = info.get("uploader") or info.get("artist") or info.get("channel")
        candidates.append({
            "url": page_url,
            "title": title,
            "source": _platform(page_url),
            "score": _score(query, artist, title, uploader, expected_duration, duration),
            "duration": duration,
        })

    candidates.sort(key=lambda candidate: candidate["score"], reverse=True)
    return candidates
