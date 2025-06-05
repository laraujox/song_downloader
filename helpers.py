
from urllib.parse import parse_qs, urlparse

import yt_dlp
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3


def sanitize_filename(name):
    """Remove caracteres proibidos no Windows."""
    forbidden_chars = '<>:"/\\|?*'
    for c in forbidden_chars:
        name = name.replace(c, '')
    return name.strip()


def add_metadata(file_path, artist=None, album=None, genre=None, year=None):
    """Adiciona metadados ao arquivo MP3."""
    try:
        audio = MP3(file_path, ID3=EasyID3)
        if artist:
            audio['artist'] = artist
        if album:
            audio['album'] = album
        if genre:
            audio['genre'] = genre
        if year:
            audio['date'] = year
        audio.save()
        print(f"Metadata added to: {file_path}")
    except Exception as e:
        print(f"Failed to add metadata: {e}")


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
