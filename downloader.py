import yt_dlp
import os
import time
from configs import MAX_RETRIES, MIN_SECONDS, MAX_SECONDS, ROOT_FOLDER
from helpers import add_metadata, build_url_list, get_top_tracks_from_dj, sanitize_filename, expand_soundcloud_playlist_url, \
    is_spotify_url, download_with_spotdl
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm


def download_mp3(url, folder_name):
    attempts = 0
    download_folder = ROOT_FOLDER + folder_name


    youtube_conf = {
        'outtmpl': os.path.join(download_folder, '%(title)s.%(ext)s'),
        'format': 'bestaudio[ext=mp3]/bestaudio',
        'noplaylist': False,
        'ffmpeg_location': r'C:\ffmpeg\bin\ffmpeg.exe',
        'socket_timeout': 60,
        'concurrent_fragment_downloads': 5,
        'continuedl': True,
        'quiet': True,
        'no_warnings': True,
        'progress_hooks': [],
        'logger': None,
        'verbose': False,
    }

    while attempts < MAX_RETRIES:
        try:
            with yt_dlp.YoutubeDL(youtube_conf) as ydl:
                info_dict = ydl.extract_info(url, download=False)

                title = info_dict.get('title', 'unknown_title')

                duration = info_dict.get('duration', 0)
                if MAX_SECONDS > duration < MIN_SECONDS:
                    print(f"⏩ Skipping ad (invalid length): {title} ({duration}s)")
                    return

                title = sanitize_filename(title)
                final_file_path = os.path.join(download_folder, f"{title}.mp3")

                if os.path.exists(final_file_path):
                    return
                else:
                    ydl.download([url])

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
            print(f"❌ Error downloading {url} (attempt {attempts}/{MAX_RETRIES}): {e}")
            time.sleep(5)
    print(f"🚫 Failed to download {url} after {MAX_RETRIES} attempts.")


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
    playlist_urls = [url.strip() for url in input_urls.split(',')]

    for playlist_url in playlist_urls:
        if is_spotify_url(playlist_url):
            download_with_spotdl(playlist_url)
        else:
            print(f"🔄 Expanding SoundCloud playlist: {playlist_url}")
            try:
                song_urls, folder_name  = expand_soundcloud_playlist_url(playlist_url)

                if song_urls:
                    print(f"\n📦 Total URLs to download: {len(song_urls)}\n")
                    parsed_urls = build_url_list(song_urls)

                    with ThreadPoolExecutor(max_workers=8) as executor:
                        futures = []

                        for song_url in song_urls:
                            futures.append(executor.submit(download_mp3, song_url, folder_name))

                        for future in tqdm(as_completed(futures), total=len(futures)):
                            try:
                                future.result()
                            except Exception as exc:
                                print(f"❌ Download failed: {exc}")
                    print("\n🎉 All downloads completed!")

                else:
                    print("🚫 No valid URLs to download.")

            except Exception as e:
                print(f"❌ Failed to expand playlist {playlist_url}: {e}")

else:
    print("⚠ Invalid option. Exiting.")
