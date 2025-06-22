from urllib.parse import parse_qs, urlparse

import requests
from mutagen.id3 import ID3, APIC
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3


def sanitize_filename(name):
    """Remove caracteres proibidos no Windows."""
    forbidden_chars = '<>:"/\\|?*'
    for c in forbidden_chars:
        name = name.replace(c, '')
    return name.strip()





def clean_url(url):
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    video_id = query.get('v')
    if video_id:
        return f"https://www.youtube.com/watch?v={video_id[0]}"
    return None


def build_url_list(url_list):
    # Primeiro: remover vazios
    # Segundo: limpar as urls
    # urls = [clean_url(url) for url in urls if clean_url(url)]
    # urls = list(filter(None, url_list))
    # Terceiro: remover duplicadas
    return list(set(url_list))


def get_top_tracks_from_dj(dj_url, limit=5):
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'dump_single_json': True,
        'playlistend': limit
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        data = ydl.extract_info(dj_url, download=False)
        tracks = data.get("entries", [])[:limit]
        return tracks  # cada 'track' é um dict com 'title' e 'url'
import yt_dlp


def expand_soundcloud_sets(urls):
    """
    Recebe uma lista de URLs (que podem ser faixas ou playlists do SoundCloud),
    e retorna uma nova lista onde cada playlist foi substituída pelas URLs
    das faixas que a compõem.
    """
    expanded = []
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,       # pega apenas metadados sem baixar o áudio
        'dump_single_json': True    # força a saída em JSON rígido
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for url in urls:
            try:
                info = ydl.extract_info(url, download=False)
                # Se for uma playlist, 'entries' existe e é lista de faixas
                if 'entries' in info and isinstance(info['entries'], list):
                    # Cada item em info['entries'] terá ao menos: 'url' e 'title'
                    for entry in info['entries']:
                        # 'url' já é o link direto para a faixa no SoundCloud
                        expanded.append(entry['url'])
                else:
                    # Não é playlist; entra a URL como faixa única
                    expanded.append(url)
            except Exception as e:
                print(f"❌ Erro ao expandir {url}: {e}")
    return expanded

def add_metadata(file_path, artist=None, genre=None, year=None, cover_url=None):
    audio = EasyID3(file_path)
    if artist:
        audio['artist'] = artist
    if genre:
        audio['genre'] = genre
    if year:
        audio['date'] = year
    audio.save()

    if cover_url:
        try:
            img_data = requests.get(cover_url).content
            audio = ID3(file_path)
            audio['APIC'] = APIC(
                encoding=3,         # UTF-8
                mime='image/jpeg',  # or image/png
                type=3,             # Cover (front)
                desc='Cover',
                data=img_data
            )
            audio.save()
            print(f"🖼️ Cover art added from: {cover_url}")
        except Exception as e:
            print(f"⚠️ Failed to add cover art: {e}")
