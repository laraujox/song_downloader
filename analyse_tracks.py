import os
from concurrent.futures import ProcessPoolExecutor, as_completed

import librosa
import numpy as np
import shutil
from configs import ALLOWED_EXTENSIONS, BPM_RANGES, KEY_GROUPS


def analyze_track(path, duration=60):
    try:
        y, sr = librosa.load(path, duration=duration)

        # BPM
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)

        # Key
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        mean_chroma = np.mean(chroma, axis=1)
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F',
                 'F#', 'G', 'G#', 'A', 'A#', 'B']
        key = notes[int(np.argmax(mean_chroma))]

        return os.path.basename(path), {"bpm": int(tempo), "key": key}
    except Exception as e:
        print(f"Erro em {path}: {e}")
        return None


def organize_tracks_by_key_and_bpm(analized_tracks: list, source_folder: str):
    moved = set()

    for track_dict in analized_tracks:
        if not track_dict:
            continue

        filename, data = next(iter(track_dict.items()))
        key = data.get("key")
        key = key.replace('D#', 'D#m').replace('A#', 'A#m').replace('G#', 'G#m').replace('F#', 'F#m').replace('C#',
                                                                                                              'C#m')

        bpm = data.get("bpm")

        if not key or not bpm or filename in moved:
            continue

        key_group_name = None
        for group_name, group_data in KEY_GROUPS.items():
            if key in group_data["keys"]:
                key_group_name = group_name
                break

        if not key_group_name:
            print(f"Key '{key}' not found in any group. Skipping {filename}.")
            continue

        bpm_folder_name = None
        for bpm_name, bpm_range in BPM_RANGES.items():
            if bpm in bpm_range:
                bpm_folder_name = bpm_name
                break

        if not bpm_folder_name:
            print(f"BPM '{bpm}' not in defined ranges. Skipping {filename}.")
            continue

        key_folder = os.path.join(source_folder, key_group_name)
        bpm_folder = os.path.join(key_folder, bpm_folder_name)
        os.makedirs(bpm_folder, exist_ok=True)

        source_path = os.path.join(source_folder, filename)
        destination_path = os.path.join(bpm_folder, filename)

        if os.path.exists(source_path):
            shutil.move(source_path, destination_path)
            print(f"Moved {filename} → {key_group_name}/{bpm_folder_name}")
            moved.add(filename)
        else:
            print(f"File not found: {source_path}")


def main():
    folder = input("Enter folder to be analysed: ")
    all_files = [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith(ALLOWED_EXTENSIONS)
    ]

    analized_tracks = []
    total = len(all_files)
    print(f"Found {total} tracks. Starting parallel analysis...")

    with ProcessPoolExecutor() as executor:
        futures = {executor.submit(analyze_track, path): path for path in all_files}

        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            if result:
                filename, data = result
                analized_tracks.append({filename: data})
                print(f"{i}/{total} analyzed – {filename} – bpm: {data['bpm']}, key: {data['key']}")

    organize_tracks_by_key_and_bpm(analized_tracks, folder)

if __name__ == "__main__":
    main()
