import subprocess
import re
import os
import sys
import time
import qrcode

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
URL_FILE = os.path.join(PROJECT_ROOT, "tunnel_url.txt")
QR_FILE = os.path.join(PROJECT_ROOT, "mobile_qr.png")
CLOUDFLARED = os.path.join(PROJECT_ROOT, "cloudflared.exe")

def generate_qr(url: str):
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#0F172A", back_color="#FFFFFF")
        img.save(QR_FILE)
        
        # Also copy to artifact dir if exists
        artifact_dir = r"C:\Users\jvnsi\.gemini\antigravity\brain\00216b1a-3e63-4c41-ac7f-a33d94a6bbbb"
        if os.path.exists(artifact_dir):
            art_qr = os.path.join(artifact_dir, "mobile_qr.png")
            img.save(art_qr)
        print(f"[OK] QR code updated for: {url}")
    except Exception as e:
        print(f"[!] Error generating QR code: {e}")

def main():
    if not os.path.exists(CLOUDFLARED):
        print(f"[!] Error: {CLOUDFLARED} not found.")
        sys.exit(1)

    print("[*] Starting Cloudflare Tunnel for Mobile Network Access...")
    cmd = [CLOUDFLARED, "tunnel", "--url", "http://127.0.0.1:8501"]
    
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        encoding="utf-8",
        errors="replace"
    )

    url_found = False
    tunnel_regex = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")

    for line in iter(proc.stdout.readline, ''):
        line = line.strip()
        if not line:
            continue
        
        match = tunnel_regex.search(line)
        if match and not url_found:
            url = match.group(0)
            url_found = True
            with open(URL_FILE, "w", encoding="utf-8") as f:
                f.write(url)
            print("=" * 60)
            print("  [OK] Mobile Network Access Tunnel Active!")
            print(f"  [OK] Public URL: {url}")
            print("  [OK] Works on 4G, 5G, and any mobile data network worldwide.")
            print("=" * 60)
            generate_qr(url)
            sys.stdout.flush()

    proc.wait()

if __name__ == "__main__":
    main()
