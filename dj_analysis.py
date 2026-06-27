"""FUTURE / EXPERIMENTAL — offline BPM + key analysis and folder organizing.

This is a standalone prototype for the DJ workflow (analyze downloaded tracks,
then sort them into key-group / BPM-band folders). It is NOT part of the web app
and is not installed by `make setup`. To use it:

    pip install librosa numpy soundfile
    python dj_analysis.py

See the README "Future ideas" section for how to make key/genre detection
accurate (essentia / keyfinder / musicnn) before relying on this for real sets.
"""
import os
import shutil
from concurrent.futures import ProcessPoolExecutor, as_completed

import librosa
import numpy as np

ALLOWED_EXTENSIONS = (".wav", ".mp3", ".flac", ".aiff")

KEY_GROUPS = {
    "Bright_Uplifting": ["C", "G", "D", "A", "E"],
    "Warm_Melodic": ["F", "Am", "Em", "F#", "C#m"],
    "Melancholic_Ethereal": ["Dm", "Bm", "G#m", "D#m", "Fm"],
    "Dark_Mystical": ["F#m", "G#m", "Gm", "A#m", "Cm"],
    "Aggressive_Hypnotic": ["A#", "C#", "B", "G#", "A"],
}

BPM_RANGES = {
    "BPM_60_150": range(60, 151),
    "BPM_151_180": range(151, 181),
    "BPM_181_PLUS": range(181, 1000),
}

NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def analyze_track(path: str, duration: int = 60) -> tuple[str, dict] | None:
    try:
        samples, sample_rate = librosa.load(path, duration=duration)
        tempo, _ = librosa.beat.beat_track(y=samples, sr=sample_rate)
        chroma = librosa.feature.chroma_stft(y=samples, sr=sample_rate)
        key = NOTES[int(np.argmax(np.mean(chroma, axis=1)))]
        return os.path.basename(path), {"bpm": int(tempo), "key": key}
    except Exception as error:
        print(f"Error analyzing {path}: {error}")
        return None


def _group_for_key(key: str) -> str | None:
    for group_name, keys in KEY_GROUPS.items():
        if key in keys:
            return group_name
    return None


def _band_for_bpm(bpm: int) -> str | None:
    for band_name, band_range in BPM_RANGES.items():
        if bpm in band_range:
            return band_name
    return None


def organize_tracks(analyzed: list[tuple[str, dict]], source_folder: str) -> None:
    for filename, data in analyzed:
        group = _group_for_key(data["key"])
        band = _band_for_bpm(data["bpm"])
        if not group or not band:
            print(f"Skipping {filename}: key/bpm not in a defined group.")
            continue

        target_folder = os.path.join(source_folder, group, band)
        os.makedirs(target_folder, exist_ok=True)
        source_path = os.path.join(source_folder, filename)
        if os.path.exists(source_path):
            shutil.move(source_path, os.path.join(target_folder, filename))
            print(f"Moved {filename} -> {group}/{band}")


def main() -> None:
    folder = input("Enter folder to analyze: ").strip()
    paths = [
        os.path.join(folder, name)
        for name in os.listdir(folder)
        if name.lower().endswith(ALLOWED_EXTENSIONS)
    ]
    print(f"Found {len(paths)} tracks. Analyzing...")

    analyzed = []
    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(analyze_track, path) for path in paths]
        for future in as_completed(futures):
            result = future.result()
            if result:
                filename, data = result
                analyzed.append(result)
                print(f"{filename} — bpm: {data['bpm']}, key: {data['key']}")

    organize_tracks(analyzed, folder)


if __name__ == "__main__":
    main()
