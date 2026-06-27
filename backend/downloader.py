"""Download a resolved Track to disk as the configured audio format.

Strategy: probe the track's own source for metadata (title + artist), try to
download it, and if that fails (DRM, geo-block, removed, etc.) fall back to
searching other platforms with an artist-aware query and try each verified
candidate until one downloads. Always grabs the best available audio.

Everything lands in a per-job cache folder first. Confident matches are moved to
their final folder right away; uncertain ones stay in the cache until the review
modal confirms them (then they're moved or deleted). Short previews let those
uncertain matches be auditioned before they're kept.
"""
import glob
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field

import yt_dlp

from . import config, matching, metadata, resolver, soundcloud

_PREVIEW_DIR = os.path.join(tempfile.gettempdir(), "song_downloader_previews")
_PREVIEW_SECONDS = 45
_REVIEW_CANDIDATES = 3


@dataclass
class Outcome:
    needs_review: bool
    file_path: str | None = None       # where the file is right now (the cache folder)
    final_folder: str | None = None    # where it belongs once confirmed
    chosen_index: int | None = None    # index into candidates that was downloaded
    candidates: list = field(default_factory=list)  # alternatives for review


def _sanitize(name: str) -> str:
    forbidden = '<>:"/\\|?*'
    for char in forbidden:
        name = name.replace(char, "")
    return name.strip() or "unknown"


def final_folder_for(track) -> str:
    """Where a track ultimately belongs: a per-playlist subfolder under the root."""
    if track.playlist_name:
        return os.path.join(config.DOWNLOAD_ROOT, _sanitize(track.playlist_name))
    return config.DOWNLOAD_ROOT


def _ytdlp_options(folder: str, audio_format: str) -> dict:
    options = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(folder, "%(title)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "socket_timeout": 60,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": audio_format,
            "preferredquality": "0",  # best available
        }],
    }
    if config.FFMPEG_LOCATION:
        options["ffmpeg_location"] = config.FFMPEG_LOCATION
    return options


def _probe(url: str) -> dict | None:
    """Read metadata for a URL without downloading. Returns None if it can't."""
    options = {"quiet": True, "no_warnings": True, "noprogress": True, "skip_download": True}
    if config.FFMPEG_LOCATION:
        options["ffmpeg_location"] = config.FFMPEG_LOCATION
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            return ydl.extract_info(url, download=False)
    except Exception:
        return None


def _artist_from_info(info: dict) -> str | None:
    for key in ("artist", "creator", "uploader", "channel"):
        value = info.get(key)
        if value:
            return value
    return None


def _join_query(artist: str | None, title: str | None) -> str | None:
    if not title:
        return artist
    # Avoid "Artist Artist - Title" when the title already names the artist.
    if artist and artist.lower() not in title.lower():
        return f"{artist} {title}"
    return title


def _download_url(url: str, folder: str, audio_format: str, info: dict | None = None) -> str:
    """Download a single URL and return the file path. Raises on any failure."""
    options = _ytdlp_options(folder, audio_format)
    with yt_dlp.YoutubeDL(options) as ydl:
        if info is None:
            info = ydl.extract_info(url, download=False)

        duration = info.get("duration")
        if duration and not (config.MIN_SECONDS <= duration <= config.MAX_SECONDS):
            raise RuntimeError(f"Rejected: length {duration}s outside allowed range")

        ydl.download([url])
        source_path = ydl.prepare_filename(info)

    file_path = os.path.splitext(source_path)[0] + f".{audio_format}"
    if not os.path.exists(file_path) or os.path.getsize(file_path) < config.MIN_FILE_BYTES:
        raise RuntimeError("Downloaded file missing or too small")

    metadata.add_metadata(file_path, info)
    return file_path


def download_track(track, audio_format: str, cache_folder: str, report_title=None) -> Outcome:
    """Download a track into `cache_folder`, falling back to other platforms if needed.

    Returns an Outcome with the cached file, its intended final folder, and (when
    uncertain) the alternative candidates to audition. Raises if nothing downloaded.
    """
    os.makedirs(cache_folder, exist_ok=True)
    final_folder = final_folder_for(track)
    tried_urls = set()
    errors = []
    query = _join_query(track.artist, track.title) or resolver.title_from_url(track.source_url or "")

    # 1. The track's own source (skipped for metadata-only tracks like Spotify).
    if track.source_url and not track.needs_search:
        tried_urls.add(track.source_url)
        info = _probe(track.source_url)
        if info:
            real_title = info.get("title")
            if real_title and report_title:
                report_title(real_title)  # upgrade a placeholder to the real name
            # Refine the fallback query with the real artist + title we just read.
            query = _join_query(_artist_from_info(info), real_title) or query
            track.artist = track.artist or _artist_from_info(info)
        elif track.source == "soundcloud":
            # Probe failed (likely DRM) — recover title/artist from SoundCloud's API
            # so the fallback search can still find the song elsewhere.
            meta = soundcloud.track_meta(track.source_url)
            if meta:
                track.title = meta["title"] or track.title
                track.artist = meta["artist"] or track.artist
                track.expected_duration = meta["duration"] or track.expected_duration
                if report_title and meta["title"]:
                    report_title(meta["title"])
                query = _join_query(track.artist, track.title) or query
        try:
            path = _download_url(track.source_url, cache_folder, audio_format, info)
            return Outcome(needs_review=False, file_path=path, final_folder=final_folder)
        except Exception as error:
            errors.append(str(error))
            print(f"[download] direct source failed for '{track.title}': {error}")

    # 2. Fall back to searching other platforms for the same song.
    if query:
        is_fallback = bool(track.source_url and not track.needs_search)
        candidates = [
            candidate
            for candidate in matching.search_candidates(query, track.expected_duration, track.artist)
            if candidate["url"] not in tried_urls
        ][:_REVIEW_CANDIDATES]

        for index, candidate in enumerate(candidates):
            try:
                path = _download_url(candidate["url"], cache_folder, audio_format)
                # Keep the track's real name for display; the matched candidate's
                # title is shown separately in the review modal.
                needs_review = is_fallback or candidate["score"] < config.CONFIDENCE_THRESHOLD
                return Outcome(
                    needs_review=needs_review,
                    file_path=path,
                    final_folder=final_folder,
                    chosen_index=index if needs_review else None,
                    candidates=candidates if needs_review else [],
                )
            except Exception as error:
                errors.append(str(error))
                print(f"[download] candidate failed for '{track.title}': {error}")

    raise RuntimeError(errors[-1] if errors else "No source could be downloaded")


def download_into(url: str, folder: str, audio_format: str) -> str:
    """Download one URL into a folder (used to fetch a swapped-in reviewed pick)."""
    os.makedirs(folder, exist_ok=True)
    return _download_url(url, folder, audio_format)


def move_to_folder(path: str, folder: str) -> str:
    """Move a finished download from the cache into its final folder. Returns new path."""
    os.makedirs(folder, exist_ok=True)
    destination = os.path.join(folder, os.path.basename(path))
    if os.path.abspath(path) == os.path.abspath(destination):
        return path
    if os.path.exists(destination):
        os.remove(destination)
    shutil.move(path, destination)
    return destination


def remove_file(path: str | None) -> None:
    if path and os.path.exists(path):
        os.remove(path)


def cleanup_folder(folder: str) -> None:
    """Remove a (now-empty) cache folder, ignoring any failure."""
    shutil.rmtree(folder, ignore_errors=True)


def _preview_options(base_path: str, ranged: bool) -> dict:
    options = {
        "format": "bestaudio/best",
        "outtmpl": base_path + ".%(ext)s",
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "128",
        }],
    }
    if ranged:
        from yt_dlp.utils import download_range_func
        options["download_ranges"] = download_range_func(None, [(0, _PREVIEW_SECONDS)])
        options["force_keyframes_at_cuts"] = True
    if config.FFMPEG_LOCATION:
        options["ffmpeg_location"] = config.FFMPEG_LOCATION
    return options


def preview_from_file(cache_key: str, source_path: str) -> str:
    """Make a short mp3 preview from a file already on disk (no re-download)."""
    os.makedirs(_PREVIEW_DIR, exist_ok=True)
    out_path = os.path.join(_PREVIEW_DIR, _sanitize(cache_key)) + ".mp3"
    if os.path.exists(out_path):
        return out_path

    ffmpeg = config.FFMPEG_LOCATION or "ffmpeg"
    subprocess.run(
        [ffmpeg, "-y", "-i", source_path, "-t", str(_PREVIEW_SECONDS), "-b:a", "128k", out_path],
        check=True, capture_output=True,
    )
    return out_path


def get_preview(cache_key: str, url: str) -> str:
    """Return a path to a short mp3 preview of `url`, generating + caching it once.

    Tries a fast 45s ranged clip first; if that fails (some HLS streams don't
    support ranges) it falls back to a full download so the preview is reliable.
    """
    os.makedirs(_PREVIEW_DIR, exist_ok=True)
    base_path = os.path.join(_PREVIEW_DIR, _sanitize(cache_key))
    final_path = base_path + ".mp3"
    if os.path.exists(final_path):
        return final_path

    for ranged in (True, False):
        for leftover in glob.glob(base_path + ".*"):
            os.remove(leftover)
        try:
            with yt_dlp.YoutubeDL(_preview_options(base_path, ranged)) as ydl:
                ydl.download([url])
            if os.path.exists(final_path):
                return final_path
        except Exception:
            continue

    raise RuntimeError("Could not generate preview")
