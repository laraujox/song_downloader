import yt_dlp
import os
import time
from configs import DOWNLOAD_FOLDER, MAX_RETRIES, YOUTUBE_CONF, MIN_SECONDS, MAX_SECONDS
from helpers import add_metadata, build_url_list, get_top_tracks_from_dj, sanitize_filename, expand_soundcloud_sets, \
    is_spotify_url, download_with_spotdl
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm


def download_mp3(urls):
    attempts = 0
    while attempts < MAX_RETRIES:
        try:
            with yt_dlp.YoutubeDL(YOUTUBE_CONF) as ydl:
                info_dict = ydl.extract_info(urls, download=False)

                title = info_dict.get('title', 'unknown_title')

                duration = info_dict.get('duration', 0)
                if MAX_SECONDS > duration < MIN_SECONDS:
                    print(f"⏩ Skipping ad (invalid length): {title} ({duration}s)")
                    return

                title = sanitize_filename(title)
                final_file_path = os.path.join(DOWNLOAD_FOLDER, f"{title}.mp3")

                if os.path.exists(final_file_path):
                    return
                else:
                    ydl.download([urls])

                    if os.path.exists(final_file_path):
                        if os.path.getsize(final_file_path) < 50_000:  # evita arquivos muito pequenos (provavelmente inválidos)
                            print(f"⚠️ Skipping corrupted or incomplete file: {title}")
                            return

                        try:
                            add_metadata(final_file_path, info_dict=info_dict)
                        except Exception as e:
                            print(f"⚠️ Failed to add metadata to {title}: {e}")

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
    input_urls = input("Enter SoundCloud or Spotify playlist URLs (comma-separated): ")
    urls_raw = [url.strip() for url in input_urls.split(',')]

    for url in urls_raw:
        if is_spotify_url(url):
            download_with_spotdl(url)
        else:
            print(f"🔄 Expanding SoundCloud playlist: {url}")
            try:
                urls.extend(expand_soundcloud_sets([url]))
            except Exception as e:
                print(f"❌ Failed to expand playlist {url}: {e}")

else:
    print("⚠ Invalid option. Exiting.")

if urls:
    print(f"\n📦 Total URLs to download: {len(urls)}\n")
    parsed_urls = build_url_list(urls)

    with ThreadPoolExecutor(max_workers=8) as executor:
        future_to_url = {executor.submit(download_mp3, url): url for url in urls}

        for i, future in enumerate(tqdm(as_completed(future_to_url), total=len(urls)), 1):
            url = future_to_url[future]
            try:
                future.result()
            except Exception as exc:
                print(f"❌ Download failed for {url}: {exc}")

    print("\n🎉 All downloads completed!")

else:
    print("🚫 No valid URLs to download.")
