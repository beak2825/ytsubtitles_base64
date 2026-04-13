To upload automatically, you need client_secrets.json from google cloud.

This allows you to upload any files to a single video encrypted and compressed in base64 using 'e'
You can extract files from any video id using 'x'

Extract files from this example: https://youtu.be/buKxhVuHdrY

To use it, just download as zip, run python encrypt_decrypt.py

I was able to upload 15mb of data to ONE language track.
You can upload **3645mb** to a single video because there is 243 language tracks.
And modifiying the data is possible by deleting the language track and uploading the new data but it is not implemented here yet.

## Requirements

- Python 3.8+
- `ffmpeg` (for creating blank videos)
- `yt-dlp` (for downloading subtitles)

### Python Packages
```bash
pip install cryptography yt-dlp google-api-python-client google-auth-oauthlib google-auth-httplib2
```

runlog

>python encrypt_decrypt.py
🔐 YT Subtitle Steganography Tool (v6.4 - Custom Track Name)
   Multi-file • Public Upload • Custom Subtitle Name

Enter 'e' to EMBED or 'x' to EXTRACT: e
    1. blank_1920x1080_5s.mp4
    2. client_secrets.json
    3. pearl.mp4
    4. pearl_1.mp4
    5. test.mp4
    6. test_1.mp4
    7. youtube_token.pickle

Embed MULTIPLE files? (y/n): y
Enter numbers separated by commas: 1,5
✅ Selected: blank_1920x1080_5s.mp4, test.mp4

Use custom password? (y/n): y
Enter password: abc

🎉 Hidden subtitle created → multi.srt
