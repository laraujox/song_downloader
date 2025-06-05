from flask import Flask, request, jsonify
from helpers import get_top_tracks_from_dj, expand_soundcloud_sets, build_url_list
from downloader import download_mp3  # Assuming you have a separate download_mp3 function

app = Flask(__name__)

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    option = str(data.get("option"))
    input_urls = data.get("urls", [])

    if not input_urls:
        return jsonify({"error": "No URLs provided."}), 400

    urls = []

    if option == "1":
        for dj_url in input_urls:
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
        urls = [url.strip() for url in input_urls]

    elif option == "3":
        print("🔄 Expanding playlists...")
        urls = expand_soundcloud_sets(input_urls)

    else:
        return jsonify({"error": "Invalid option."}), 400

    if not urls:
        return jsonify({"message": "🚫 No valid URLs to download."}), 200

    print(f"\n📦 Total URLs to download: {len(urls)}\n")
    parsed_urls = build_url_list(urls)

    for index, video_url in enumerate(parsed_urls, start=1):
        print(f"\n➡️ Downloading ({index}/{len(parsed_urls)}): {video_url}")
        download_mp3(video_url)

    return jsonify({"message": f"🎉 All {len(parsed_urls)} downloads completed!"}), 200


if __name__ == '__main__':
    app.run(debug=True)
