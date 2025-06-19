
import os


FINAL_FOLDER = r"\hightech-"
DOWNLOAD_FOLDER = r'D:\songs' + FINAL_FOLDER
MAX_RETRIES = 2  # Número máximo de tentativas
YOUTUBE_CONF = {
    'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
    'format': 'bestaudio[ext=mp3]/bestaudio',
    'noplaylist': False,
    'ffmpeg_location': r'C:\ffmpeg\bin\ffmpeg.exe',
    'socket_timeout': 60,
    'concurrent_fragment_downloads': 5,
}
