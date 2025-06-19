
import os


FINAL_FOLDER = r"\dark"
DOWNLOAD_FOLDER = r'D:\songs' + FINAL_FOLDER
MAX_RETRIES = 2  # Número máximo de tentativas
MIN_SECONDS = 180
MAX_SECONDS = 900
YOUTUBE_CONF = {
    'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
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
ALLOWED_EXTENSIONS = tuple('.mp3')

HARMONIC_COMPATIBILITY = {
    'C': ['C', 'G', 'F', 'Am', 'Em', 'Dm'],
    'C#': ['C#', 'G#', 'F#', 'A#m', 'Fm', 'D#m'],
    'D': ['D', 'A', 'G', 'Bm', 'F#m', 'Em'],
    'D#': ['D#', 'A#', 'G#', 'Cm', 'Gm', 'Fm'],
    'E': ['E', 'B', 'A', 'C#m', 'G#m', 'F#m'],
    'F': ['F', 'C', 'A#', 'Dm', 'Am', 'Gm'],
    'F#': ['F#', 'C#', 'B', 'D#m', 'A#m', 'G#m'],
    'G': ['G', 'D', 'C', 'Em', 'Bm', 'Am'],
    'G#': ['G#', 'D#', 'C#', 'Fm', 'Cm', 'A#m'],
    'A': ['A', 'E', 'D', 'F#m', 'C#m', 'Bm'],
    'A#': ['A#', 'F', 'D#', 'Gm', 'Dm', 'Cm'],
    'B': ['B', 'F#', 'E', 'G#m', 'D#m', 'C#m'],
    'Am': ['Am', 'Em', 'C', 'Dm', 'G', 'F'],
    'A#m': ['A#m', 'Fm', 'C#', 'D#m', 'G#', 'F#'],
    'Bm': ['Bm', 'F#m', 'D', 'Em', 'A', 'G'],
    'Cm': ['Cm', 'Gm', 'D#', 'Fm', 'A#', 'G#'],
    'C#m': ['C#m', 'G#m', 'E', 'F#m', 'B', 'A'],
    'Dm': ['Dm', 'Am', 'F', 'Gm', 'C', 'A#'],
    'D#m': ['D#m', 'A#m', 'F#', 'G#m', 'C#', 'B'],
    'Em': ['Em', 'Bm', 'G', 'Am', 'D', 'C'],
    'Fm': ['Fm', 'Cm', 'G#', 'A#m', 'D#', 'C#'],
    'F#m': ['F#m', 'C#m', 'A', 'Bm', 'E', 'D'],
    'Gm': ['Gm', 'Dm', 'A#', 'Cm', 'F', 'D#'],
    'G#m': ['G#m', 'D#m', 'B', 'C#m', 'F#', 'E'],
}

KEY_GROUPS = {
    "Bright_Uplifting": {
        "description": "Major keys with bright, cheerful, and feel-good energy. Great for daytime, uplifting, or melodic transitions.",
        "keys": ['C', 'G', 'D', 'A', 'E']
    },
    "Warm_Melodic": {
        "description": "Keys that carry warm and smooth vibes, both major and minor. Good for groovy or progressive builds.",
        "keys": ['F', 'Am', 'Em', 'F#', 'C#m']
    },
    "Melancholic_Ethereal": {
        "description": "Minor keys with emotional or dreamy atmospheres. Ideal for emotional depth or introspective moments.",
        "keys": ['Dm', 'Bm', 'G#m', 'D#m', 'Fm']
    },
    "Dark_Mystical": {
        "description": "Keys with a mysterious, deep or ritualistic tone. Often used in forest, dark prog, or moody tech.",
        "keys": ['F#m', 'G#m', 'Gm', 'A#m', 'Cm']
    },
    "Aggressive_Hypnotic": {
        "description": "Intense and driving keys, commonly used in darkpsy, hi-tech, industrial or high-BPM transitions.",
        "keys": ['A#', 'C#', 'B', 'G#', 'A']
    }
}

BPM_RANGES = {
    "BPM_60_89": range(60, 90),
    "BPM_90_120": range(00, 121),
    "BPM_121_150": range(121, 151),
    "BPM_151_180": range(151, 181),
    "BPM_181_210": range(181, 211),
    "BPM_210_PLUS": range(211, 1000),
}
