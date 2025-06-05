
import os


FINAL_FOLDER = r"\teste_musiquinhas"
DOWNLOAD_FOLDER = r'D:\songs' + FINAL_FOLDER
YOUTUBE_URLS = [
    "https://soundcloud.com/chapeleiro/bruxaria"
]
MAX_RETRIES = 5  # Número máximo de tentativas
YOUTUBE_CONF = {
    'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
    'format': 'bestaudio[ext=mp3]/bestaudio',
    'noplaylist': False,
    'ffmpeg_location': r'C:\ffmpeg\bin\ffmpeg.exe',
    'socket_timeout': 60,
    'concurrent_fragment_downloads': 5,
}
