"""Write ID3 tags and embed cover art into a downloaded file.

Tagging is format-aware (WAV, MP3 and FLAC store tags differently) and entirely
best-effort: any failure is logged, never raised, so it can't fail a download.
"""
import os

import requests
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TDRC, TCON
from mutagen.wave import WAVE
from mutagen.mp3 import MP3
from mutagen.flac import FLAC, Picture


def _build_id3(info: dict, cover: bytes | None) -> ID3:
    tags = ID3()
    title = info.get("title")
    artist = info.get("artist") or info.get("uploader")
    year = (info.get("upload_date") or "")[:4]
    genre = (info.get("categories") or info.get("tags") or [None])[0]

    if title:
        tags["TIT2"] = TIT2(encoding=3, text=title)
    if artist:
        tags["TPE1"] = TPE1(encoding=3, text=artist)
    if year:
        tags["TDRC"] = TDRC(encoding=3, text=year)
    if genre:
        tags["TCON"] = TCON(encoding=3, text=genre)
    if cover:
        tags["APIC"] = APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=cover)
    return tags


def _fetch_cover(info: dict) -> bytes | None:
    cover_url = info.get("thumbnail")
    if not cover_url:
        return None
    try:
        return requests.get(cover_url, timeout=15).content
    except Exception:
        return None


def add_metadata(file_path: str, info: dict) -> None:
    try:
        extension = os.path.splitext(file_path)[1].lower()
        cover = _fetch_cover(info)

        if extension == ".flac":
            audio = FLAC(file_path)
            audio["title"] = info.get("title", "")
            audio["artist"] = info.get("artist") or info.get("uploader") or ""
            if cover:
                picture = Picture()
                picture.type, picture.mime, picture.data = 3, "image/jpeg", cover
                audio.add_picture(picture)
            audio.save()
            return

        # WAV and MP3 both carry an ID3 chunk that mutagen manages for us.
        audio = WAVE(file_path) if extension == ".wav" else MP3(file_path)
        audio.tags = _build_id3(info, cover)
        audio.save()
    except Exception as error:
        print(f"Could not tag {file_path}: {error}")
