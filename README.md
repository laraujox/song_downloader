# 🎧 Song Downloader

Download songs and playlists from **YouTube, SoundCloud and Spotify** in high
quality, with accuracy checks so you don't end up with the wrong track. Built for
a DJ workflow: paste links in a simple web UI, get clean audio files per playlist.

## Architecture

```
React (Vite)  ──POST /api/download──▶  FastAPI
   single page   ◀──GET /api/jobs/{id}──   │
                                            ▼
                resolver ─▶ matching ─▶ downloader ─▶ metadata
                (URLs →    (verify the   (yt-dlp →    (tags +
                 tracks)    right song)   WAV file)    cover art)
```

- **resolver** — detects the source and expands playlists into individual tracks.
  A single URL is just a one-item list, so playlists and singles share one path.
- **matching** — for Spotify (and searches), finds the song on YouTube/SoundCloud,
  rejects implausible lengths, and scores by title + duration so a "similar name,
  different song" is caught. Low-confidence picks are flagged **needs review**.
- **downloader** — pulls the best audio stream and converts it with ffmpeg.
- **metadata** — writes ID3 tags and embeds cover art (format-aware).

Spotify is DRM-protected, so its links are re-found on YouTube/SoundCloud and
verified before downloading.

## Features

- Playlists **and** single tracks, from YouTube / SoundCloud / Spotify.
- Configurable output format — **WAV** by default, FLAC or MP3 available.
- Accuracy guards: duration bounds reject ads/clips/podcasts; matches are scored
  and uncertain ones are flagged in the UI for manual review.
- Parallel downloads (capped by `MAX_CONCURRENT_DOWNLOADS`).
- If a track's source fails (DRM, geo-block), it's automatically re-found and
  downloaded from another platform.
- **Review modal**: audition flagged tracks (short previews) against alternatives,
  pick the right version or discard, then confirm.
- One folder created per playlist, with tags + cover art.
- Live per-track progress in the browser.

> **On WAV:** YouTube/SoundCloud only serve lossy audio, so WAV doesn't *add*
> quality — it's a lossless container for maximum CDJ/rekordbox compatibility.
> For the same audio at half the size, choose **FLAC**.

## Setup

**Requirements:** Python 3.10+, Node 18+, and **ffmpeg** on your PATH
(`ffmpeg -version` should work).

```bash
make setup        # creates .venv, installs Python + npm deps
cp .env.example .env   # then edit paths / optional Spotify creds
```

Spotify is optional — without `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET`
(free from the [Spotify dashboard](https://developer.spotify.com/dashboard)),
Spotify links are simply skipped.

## Run

In two terminals:

```bash
make backend      # FastAPI on http://localhost:8000
make frontend     # Vite UI on http://localhost:5173
```

Open the Vite URL, paste links (one per line or comma-separated), pick a format,
hit **Download**, and watch progress. Files land under `DOWNLOAD_ROOT`.

## Future ideas

- **Auto BPM / key / genre tagging** for the rekordbox flow. `dj_analysis.py`
  prototypes this with `librosa`. To make it accurate, detect key with
  [`essentia`](https://essentia.upf.edu/) (KeyExtractor) or `keyfinder` instead
  of raw chroma, and genre with a pretrained model (e.g. `musicnn`). Write
  Camelot key + BPM into ID3 `TKEY`/`TBPM` so rekordbox reads them on import.
- **Auto set-building** — order tracks by Camelot-compatible keys and BPM bands
  to suggest harmonically mixable sets.
- **Duplicate / already-in-library detection** via audio fingerprinting
  (`chromaprint` / `acoustid`).
- **Loudness normalization** to a target LUFS for consistent set levels.
- **Re-search button** for `needs review` tracks, plus download history.
