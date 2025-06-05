# 🎧 SoundCloud MP3 Downloader

A Python script to download high-quality `.mp3` files from SoundCloud, supporting:

- 🔍 Top tracks from artist profiles  
- 🔗 Direct track URLs  
- 📜 Full playlists (sets)

---

## 🚀 Getting Started

```bash
# 1. Navigate to the project folder
cd path/to/your/folder

# 2. Create a virtual environment
python -m venv venv

# 3. Activate the virtual environment

# On Windows:
.\venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the script
python downloader.py
```

---

## 🎛️ Usage Options

When running the script, you will be prompted to choose one of the options:

- `1` — 🎵 **Artist Mode**  
  Enter one or more SoundCloud artist profile URLs (comma-separated).  
  The script will fetch and download the top 10 tracks from each artist.

- `2` — 🔗 **Direct Track URLs**  
  Enter one or more individual SoundCloud track URLs (comma-separated).  
  The script will download each track directly.

- `3` — 📜 **Playlist Mode**  
  Enter one or more SoundCloud playlist/set URLs (comma-separated).  
  The script will expand each playlist and download all tracks inside.

---

🎉 Once finished, your downloaded `.mp3` files will be saved in the configured output folder with proper metadata.
