import os

# Pasta onde estão os arquivos
folder_path = r'D:\songs\14_june_set_hightech_dark'

# Lista na ordem desejada
ordered_files = [
    "Angry Rocket feat. Gen-Ohm - Space Loneliness.mp3",
    "Kumbh Rastafari (Har Har Mahadev).mp3",
    "Cultura ca Tieni (feat. Alpscore).mp3",
    "Darkness and Light of Godness (feat. Yoshua Em).mp3",
    "Henrique Camacho, Sajanka, S3N0 - Om Namo 170BPM.mp3",
    "KDrew - Last Train to Paradise (iamindigo Remix) [175Bpm].mp3",
    "Technical Hitch & Dark Whisper - The String Theory.mp3",
    "Mirage.mp3",
    "175 BPM Gambit - Spirit , Art, Science (Collateral Beauty Album).mp3",
    "Point Break.mp3",
    "Savage - Masquerade.mp3",
    "Mãe Terra & Sagrado Feminino (Bootleg Necropsycho).mp3",
    "Special M & Marambá - Monster Breeze.mp3",
    "OxiDaksi - We Are Two 180.mp3",
    "Koktavy - Sky Glitch - 180 (OVNI Records).mp3",
    "Akhila Journey (feat. KILLATK).mp3",
    "Psycho Alien (feat. Alien Chaos).mp3",
    "KiLLATK - Kwiz.mp3",
    "Mentalecho - Let's Hope For The Best ! (200 BPM).mp3",
    "Kayros Live - China ◢◤(DØN4lĐ T Я U m P is Ⱥ F＊＊＊＊N' I D I Ø͓T) [200BPM].mp3",
    "Odyn hero (180 bpm 👽) Free Dowload⧸NO MASTER⧸.mp3",
    "What's this smell？？ [FREE DOWNLOAD].mp3",
    "Marambá - Raggatek Live Band - Get Up Stand Up N' Fight (Marambá Remix)[180].mp3"
]

# Renomeia os arquivos com prefixo de ordem
index=1
for _, file_name in enumerate(ordered_files, start=1):
# for file_name in os.listdir(folder_path):
    old_path = os.path.join(folder_path, file_name)
    new_name = f"{index:02d}_{file_name}"
    # new_name = f"{file_name.split("_")[-1]}"

    new_path = os.path.join(folder_path, new_name)

    if os.path.exists(old_path):
        os.rename(old_path, new_path)
        index+=1
        print(f"Renamed: {file_name} -> {new_name}")
    else:
        print(f"File not found: {file_name}")
