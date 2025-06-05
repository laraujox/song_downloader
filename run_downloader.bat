@"
@echo off
cd /d "C:\Users\Lucas\Desktop"
call env\Scripts\activate
python "D:\songs\downloader\downloader.py"
"@ | Out-File -Encoding ASCII "C:\Users\Lucas\Desktop\run_downloader.bat"
