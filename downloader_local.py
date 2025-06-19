import yt_dlp
import os
import time
from configs import DOWNLOAD_FOLDER, MAX_RETRIES, YOUTUBE_CONF
from helpers import add_metadata, build_url_list, get_top_tracks_from_dj, sanitize_filename, expand_soundcloud_sets


def download_mp3(urls):
    attempts = 0
    while attempts < MAX_RETRIES:
        try:
            with yt_dlp.YoutubeDL(YOUTUBE_CONF) as ydl:
                info_dict = ydl.extract_info(urls, download=False)
                title = info_dict.get('title', 'unknown_title')

                duration = info_dict.get('duration', 0)
                if 900 > duration < 60:
                    print(f"⏩ Skipping ad (invalid length): {title} ({duration}s)")
                    return

                title = sanitize_filename(title)
                final_file_path = os.path.join(DOWNLOAD_FOLDER, f"{title}.mp3")

                if os.path.exists(final_file_path):
                    print(f"⚠️ Skipping download: '{final_file_path}' already exists.")
                    return
                else:
                    print(f"⬇️ Downloading: {title}")
                    ydl.download([urls])

                    if os.path.exists(final_file_path):
                        artist = info_dict.get('uploader', 'Unknown Artist')
                        year = info_dict.get('upload_date', '')[:4] if info_dict.get('upload_date') else None
                        genre = None
                        if info_dict.get('categories'):
                            genre = info_dict['categories'][0]
                        elif info_dict.get('tags'):
                            genre = info_dict['tags'][0]

                        add_metadata(final_file_path, artist=artist, genre=genre, year=year)

                        print(f"✅ Finished downloading and tagging: {title}\nSaved to: {final_file_path}")
                    return
        except Exception as e:
            attempts += 1
            print(f"❌ Error downloading {urls} (attempt {attempts}/{MAX_RETRIES}): {e}")
            time.sleep(5)
    print(f"🚫 Failed to download {urls} after {MAX_RETRIES} attempts.")


print("🎧 Welcome to the SoundCloud Downloader")

option = input(
    "Choose an option:\n"
    "1 - Fetch top tracks by artist\n"
    "2 - Download direct URLs\n"
    "3 - Expand SoundCloud playlists\n"
    "Option: "
)

urls = []

if option == "1":
    input_artist_url = input("Enter the artist URLs (comma-separated): ")
    artist_urls = [url.strip() for url in input_artist_url.split(',')]

    for dj_url in artist_urls:
        try:
            print(f"🔍 Searching top tracks for: {dj_url}")
            top_tracks = get_top_tracks_from_dj(dj_url, limit=10)
            print(f"🎵 Top tracks found for {dj_url}:")
            for track in top_tracks:
                print(f"✔ {track['title']} - {track['url']}")
                urls.append(track['url'])
        except Exception as e:
            print(f"❌ Failed to fetch tracks from {dj_url}: {e}")

elif option == "2":
    input_urls = input("Enter the track URLs (comma-separated): ")
    urls = [url.strip() for url in input_urls.split(',')]

elif option == "3":
    input_urls = input("Enter SoundCloud playlist URLs (comma-separated): ")
    urls_raw = [url.strip() for url in input_urls.split(',')]
    print("🔄 Expanding playlists...")
    urls = expand_soundcloud_sets(urls_raw)

else:
    print("⚠ Invalid option. Exiting.")

if urls:
    print(f"\n📦 Total URLs to download: {len(urls)}\n")
    parsed_urls = build_url_list(urls)

    # print(f"\n➡️ Downloading ({index}/{len(parsed_urls)}): {video_url}")
    download_mp3(parsed_urls)

    print("\n🎉 All downloads completed!")
else:
    print("🚫 No valid URLs to download.")
