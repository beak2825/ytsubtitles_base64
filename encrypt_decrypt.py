import os
import sys
import base64
import gzip
import hashlib
import subprocess
import random
import time
import pickle

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding
except ImportError:
    print("❌ Missing dependency: cryptography")
    print("   Run: pip install cryptography")
    sys.exit(1)


def encrypt(data: bytes, password: str) -> bytes:
    key = hashlib.sha256(password.encode()).digest()
    iv = os.urandom(16)
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded = padder.update(data) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    ct = encryptor.update(padded) + encryptor.finalize()
    return iv + ct


def decrypt(encrypted_data: bytes, password: str) -> bytes:
    key = hashlib.sha256(password.encode()).digest()
    iv = encrypted_data[:16]
    ct = encrypted_data[16:]
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    padded = decryptor.update(ct) + decryptor.finalize()
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    return unpadder.update(padded) + unpadder.finalize()


def detect_extension(data: bytes) -> str:
    if not data: return ".bin"
    magic = {b'\x89PNG\r\n\x1a\n': '.png', b'\xFF\xD8\xFF': '.jpg', b'%PDF-': '.pdf',
             b'PK\x03\x04': '.zip', b'GIF87a': '.gif', b'GIF89a': '.gif', b'\x42\x4D': '.bmp',
             b'RIFF': '.wav', b'MZ': '.exe', b'\x7fELF': '.elf'}
    for sig, ext in magic.items():
        if data.startswith(sig): return ext
    try:
        data.decode('utf-8', errors='strict')
        return '.txt'
    except:
        return '.bin'


def load_youtube_service():
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        return InstalledAppFlow, Request, build, MediaFileUpload
    except ImportError:
        print("❌ Missing Google API libraries.")
        print("   Run: pip install google-api-python-client google-auth-oauthlib google-auth-httplib2")
        sys.exit(1)


print("🔐 YT Subtitle Steganography Tool (v6.4 - Custom Track Name)")
print("   Multi-file • Public Upload • Custom Subtitle Name\n")

mode = input("Enter 'e' to EMBED or 'x' to EXTRACT: ").strip().lower()

if mode == "e":
    # ====================== EMBED ======================
    files = [f for f in os.listdir(".") if os.path.isfile(f) and not f.endswith((".srt", ".py", ".pyc"))]
    files.sort()
    if not files:
        print("❌ No files found!"); sys.exit(1)

    for i, f in enumerate(files, 1):
        print(f"   {i:2d}. {f}")

    multi = input("\nEmbed MULTIPLE files? (y/n): ").strip().lower() == 'y'
    if multi:
        nums = input("Enter numbers separated by commas: ").strip()
        try:
            indices = [int(x.strip()) - 1 for x in nums.split(",") if x.strip().isdigit()]
            target_files = [files[i] for i in indices if 0 <= i < len(files)]
        except:
            target_files = []
    else:
        try:
            choice = int(input("\nSelect file number: "))
            target_files = [files[choice - 1]]
        except:
            print("❌ Invalid selection."); sys.exit(1)

    if not target_files:
        print("❌ No files selected."); sys.exit(1)

    print(f"✅ Selected: {', '.join(target_files)}")

    use_custom = input("\nUse custom password? (y/n): ").strip().lower() == 'y'
    password = input("Enter password: ").strip() if use_custom else "ytencrypted"
    if not password: password = "ytencrypted"

    b64_list = []
    for tf in target_files:
        with open(tf, "rb") as f:
            raw = f.read()
        compressed = gzip.compress(raw)
        encrypted = encrypt(compressed, password)
        b64_list.append(base64.b64encode(encrypted).decode("utf-8"))

    combined_b64 = ":::YTSUBSEP:::".join(b64_list)

    # Build SRT
    with open("temp.srt", "w", encoding="utf-8") as f:
        for i in range(1, 121):
            start_sec = (i-1)*4
            sm = start_sec // 60; ss = start_sec % 60
            em = sm; es = ss + 3
            if es >= 60: es -= 60; em += 1
            f.write(f"{i}\n")
            f.write(f"00:{sm:02d}:{ss:02d},000 --> 00:{em:02d}:{es:02d},000\n")
            f.write("github/beak2825/ytsubtitles_base64\n\n")

    with open("temp.srt", "r", encoding="utf-8") as f:
        lines = f.readlines()

    if len(target_files) == 1:
        put_name = input("\nPut original filename on first text line? (y/n): ").strip().lower() == 'y'
        first_text = target_files[0] if put_name else "github/beak2825/ytsubtitles_base64"
    else:
        first_text = ",".join(target_files)

    lines[2] = first_text + "\n"
    lines[94] = combined_b64 + "\n"

    base_name = os.path.splitext(target_files[0])[0] if len(target_files)==1 else "multi"
    output_srt = f"{base_name}.srt"

    with open(output_srt, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"\n🎉 Hidden subtitle created → {output_srt}")

    # ====================== AUTO UPLOAD ======================
    if os.path.exists("client_secrets.json"):
        ch = input("\n1 = Upload NEW public video    2 = Add to last video : ").strip()
        upload_choice = "2" if ch == "2" else "1"

        InstalledAppFlow, Request, build, MediaFileUpload = load_youtube_service()

        credentials = None
        if os.path.exists("youtube_token.pickle"):
            with open("youtube_token.pickle", "rb") as token:
                credentials = pickle.load(token)

        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file("client_secrets.json", scopes=["https://www.googleapis.com/auth/youtube.force-ssl"])
                credentials = flow.run_local_server(port=0)
            with open("youtube_token.pickle", "wb") as token:
                pickle.dump(credentials, token)

        youtube = build("youtube", "v3", credentials=credentials)

        if upload_choice == "1":
            video_file = "blank_1920x1080_5s.mp4"
            if not os.path.exists(video_file):
                print("Creating blank video...")
                os.system('ffmpeg -f lavfi -i color=c=black:s=1920x1080:d=5 -c:v libx264 -t 5 -pix_fmt yuv420p blank_1920x1080_5s.mp4 -y')

            rand_num = random.randint(1000, 9999)
            title = f"Blank Video with embedded subtitles {rand_num}"

            body = {
                "snippet": {
                    "title": title,
                    "description": "github/beak2825/ytsubtitles_base64",
                    "tags": ["stego", "hidden"],
                    "categoryId": "22"
                },
                "status": {"privacyStatus": "public"}
            }

            media = MediaFileUpload(video_file, chunksize=-1, resumable=True)
            print(f"Uploading new public video: {title} ...")
            resp = youtube.videos().insert(part="snippet,status", body=body, media_body=media).execute()
            video_id = resp["id"]
            print(f"✅ New public video uploaded! ID: {video_id}")

        else:
            print("Fetching your most recent video...")
            resp = youtube.search().list(part="snippet", forMine=True, type="video", maxResults=1, order="date").execute()
            if not resp.get("items"):
                print("No videos found."); sys.exit(1)
            video_id = resp["items"][0]["id"]["videoId"]
            print(f"Using latest video: {video_id}")

        # Wait for processing
        print("⏳ Waiting for video to be ready...")
        for _ in range(20):
            try:
                st = youtube.videos().list(part="status", id=video_id).execute()
                if st["items"][0]["status"]["uploadStatus"] == "processed":
                    print("✅ Video ready.")
                    break
            except: pass
            time.sleep(10)

        # === CUSTOM TRACK NAME ===
        default_name = "Hidden Data Track"
        track_name = input(f"\nEnter custom subtitle track name (or press Enter for '{default_name}'): ").strip()
        if not track_name:
            track_name = default_name

        # Choose random unused language
        used = []
        try:
            caps = youtube.captions().list(part="snippet", videoId=video_id).execute()
            used = [c["snippet"]["language"] for c in caps.get("items", [])]
        except: pass

        available = [l for l in ["en","en-US","es","fr","de","ja","ko","ru","zh-CN","pt","it","ar"] if l not in used]
        lang = random.choice(available if available else ["en"])

        print(f"Attaching as language: {lang} | Track name: \"{track_name}\" ...")

        caption_body = {
            "snippet": {
                "videoId": video_id,
                "language": lang,
                "name": track_name,      # <-- Custom name here
                "isDraft": False
            }
        }

        media_caption = MediaFileUpload(output_srt, mimetype="application/x-subrip", resumable=True)

        try:
            cap_resp = youtube.captions().insert(part="snippet", body=caption_body, media_body=media_caption).execute()
            print(f"✅ Subtitles uploaded successfully!")
            print(f"   Language: {lang} | Track name: \"{track_name}\"")
            print(f"   Video: https://www.youtube.com/watch?v={video_id}")
        except Exception as e:
            print(f"❌ Caption upload failed: {e}")

    else:
        if input("\nclient_secrets.json not found. Continue anyway? (y/n): ").strip().lower() != 'y':
            sys.exit(0)

elif mode == "x":
    # Extraction code (same reliable version as before)
    url = input("\nYouTube URL or video ID: ").strip()
    if not url.startswith("http"):
        url = f"https://www.youtube.com/watch?v={url}"

    print("📥 Downloading subtitles...")
    try:
        subprocess.run(["yt-dlp", "--skip-download", "--all-subs", "--sub-format", "srt", "--quiet", url], check=True)
    except Exception as e:
        print(f"❌ yt-dlp failed: {e}")
        sys.exit(1)

    srt_files = [f for f in os.listdir(".") if f.lower().endswith(".srt")]
    if not srt_files:
        print("❌ No subtitles downloaded."); sys.exit(1)

    print(f"\nFound {len(srt_files)} track(s):")
    for i, f in enumerate(srt_files, 1):
        print(f"   {i:2d}. {f}")

    sel = input("\nTrack number or 'all': ").strip().lower()
    selected = srt_files if sel == "all" else [srt_files[int(sel)-1]] if sel.isdigit() else []

    print("\n🔍 Searching for hidden data...\n")

    found_any = False
    for srt_file in selected:
        try:
            with open(srt_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = [line.rstrip('\n') for line in f.readlines()]

            payload = None
            for line in lines:
                stripped = line.strip()
                if len(stripped) > 400 or ":::YTSUBSEP:::" in stripped:
                    payload = stripped
                    break

            if not payload: continue

            filename_list = None
            if len(lines) > 2:
                first_text = lines[2].strip()
                if first_text and first_text != "github/beak2825/ytsubtitles_base64":
                    filename_list = [x.strip() for x in first_text.split(",") if x.strip()]

            b64_parts = payload.split(":::YTSUBSEP:::")

            password = "ytencrypted"
            try:
                test = base64.b64decode(b64_parts[0], validate=True)
                gzip.decompress(decrypt(test, password))
            except:
                print(f"⚠️ Default password failed on {srt_file}")
                password = input("Enter custom password: ").strip()
                if not password: continue
                try:
                    test = base64.b64decode(b64_parts[0], validate=True)
                    gzip.decompress(decrypt(test, password))
                except:
                    print("❌ Wrong password."); continue

            print(f"🎉 SUCCESS → Found {len(b64_parts)} file(s) in {srt_file}")

            for idx, part in enumerate(b64_parts):
                enc = base64.b64decode(part, validate=True)
                data = gzip.decompress(decrypt(enc, password))

                out_name = filename_list[idx] if filename_list and idx < len(filename_list) else f"recovered_{idx}{detect_extension(data)}"

                counter = 1
                final_name = out_name
                while os.path.exists(final_name):
                    name, ext = os.path.splitext(out_name)
                    final_name = f"{name}_{counter}{ext}"
                    counter += 1

                with open(final_name, "wb") as f:
                    f.write(data)
                print(f"   → Saved: {final_name} ({len(data):,} bytes)")
                found_any = True

        except Exception as e:
            print(f"   Error on {srt_file}: {e}")

    if not found_any:
        print("⚠️ No valid hidden data found.")

    print("\n🧹 Deleting downloaded .srt files...")
    for f in srt_files:
        try:
            os.remove(f)
            print(f"   Deleted {f}")
        except: pass

else:
    print("Use 'e' or 'x'.")

print("\nDone.")