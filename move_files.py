import os
import shutil

# Source and destination folder paths
source = r'D:\songs\set-neuro-pulse'
destination = r'D:\songs\14_june_set_hightech_dark'

# List of specific files to move
files_to_move = [
    "KiLLATK - Kwiz.mp3",
    "Psycho Alien (feat. Alien Chaos).mp3",
    "Akhila Journey (feat. KILLATK).mp3",
    "Koktavy - Sky Glitch - 180 (OVNI Records).mp3",
    "Special M & Marambá - Monster Breeze.mp3",
    "Technical Hitch & Dark Whisper - The String Theory.mp3",
    "Henrique Camacho, Sajanka, S3N0 - Om Namo 170BPM.mp3",
    "Darkness and Light of Godness (feat. Yoshua Em).mp3",
    "Cultura ca Tieni (feat. Alpscore).mp3",
    "Kumbh Rastafari (Har Har Mahadev).mp3"
]

# Create the destination folder if it doesn't exist
os.makedirs(destination, exist_ok=True)

# Move each file in the list
for file_name in files_to_move:
    source_path = os.path.join(source, file_name)
    destination_path = os.path.join(destination, file_name)

    # Move only if file exists
    if os.path.exists(source_path):
        shutil.move(source_path, destination_path)
        print(f"Moved: {file_name}")
    else:
        print(f"File not found: {file_name}")
