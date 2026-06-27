"""Central configuration, driven by environment variables (see .env.example)."""
import os
from dotenv import load_dotenv

load_dotenv()


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


# Where downloaded songs are saved. A subfolder per playlist is created under this root.
DOWNLOAD_ROOT = os.getenv("DOWNLOAD_ROOT", r"C:\songs")

# Downloads land here first; confident matches move to DOWNLOAD_ROOT automatically,
# uncertain ones wait here until confirmed in review (then moved or deleted).
# Kept under DOWNLOAD_ROOT so finalizing is an instant same-disk rename.
CACHE_ROOT = os.getenv("CACHE_ROOT") or os.path.join(DOWNLOAD_ROOT, ".cache")

# Output audio format. "wav" by default (best CDJ/rekordbox compatibility).
AUDIO_FORMAT = os.getenv("AUDIO_FORMAT", "wav")

# Path to ffmpeg. Blank means "use whatever is on PATH".
FFMPEG_LOCATION = os.getenv("FFMPEG_LOCATION") or None

# Make ffmpeg/ffprobe discoverable on PATH too (needed for partial-download previews).
if FFMPEG_LOCATION:
    _ffmpeg_dir = FFMPEG_LOCATION
    if os.path.isfile(_ffmpeg_dir):
        _ffmpeg_dir = os.path.dirname(_ffmpeg_dir)
    if _ffmpeg_dir and _ffmpeg_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = _ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

# Tracks shorter/longer than these bounds are rejected (kills ads, clips and full podcasts).
MIN_SECONDS = _int("MIN_SECONDS", 60)
MAX_SECONDS = _int("MAX_SECONDS", 900)

# How many times to retry a failed download before giving up.
MAX_RETRIES = _int("MAX_RETRIES", 2)

# How many tracks to download at the same time. Kept modest to avoid rate-limiting/bans.
MAX_CONCURRENT_DOWNLOADS = _int("MAX_CONCURRENT_DOWNLOADS", 4)

# Files smaller than this are treated as corrupt/incomplete and discarded.
MIN_FILE_BYTES = _int("MIN_FILE_BYTES", 100_000)

# Spotify API credentials (optional). Without them, Spotify links are skipped gracefully.
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID") or None
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET") or None

# --- Matching accuracy knobs --------------------------------------------------
# A candidate scoring below this is downloaded anyway but flagged for manual review.
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.6"))
# Duration is considered a perfect match within this many seconds of the expected length.
DURATION_TOLERANCE_SECONDS = _int("DURATION_TOLERANCE_SECONDS", 15)
# How many shortlisted results to fully extract (verify) per search. Higher = more
# accurate and more available, but slower. These are the ones that get real URLs.
VERIFY_LIMIT = _int("VERIFY_LIMIT", 6)
# Relative weights of title / artist / duration when scoring candidates (should sum to 1).
TITLE_WEIGHT = 0.55
ARTIST_WEIGHT = 0.25
DURATION_WEIGHT = 0.20
