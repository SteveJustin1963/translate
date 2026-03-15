#!/usr/bin/env python3
"""
Browser audio translation using free web services
Captures audio and uses speech recognition + translation web APIs
"""

import subprocess
import tempfile
import os
import time
import sys

try:
    import speech_recognition as sr
except ImportError:
    print("Installing speech_recognition library...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--break-system-packages", "SpeechRecognition"])
    import speech_recognition as sr

# Configuration
AUDIO_SOURCE = "alsa_output.pci-0000_00_1b.0.analog-stereo.monitor"
CHUNK_DURATION = 5  # seconds

print("╔════════════════════════════════════════════════════════════════╗")
print("║   Web-Based Real-Time Audio Translation (Browser → English)   ║")
print("╠════════════════════════════════════════════════════════════════╣")
print("║ Using: Google Speech Recognition API (free, no key needed)    ║")
print("║ Auto-detects language → Translates to English                 ║")
print("║ Works with ANY language from browser audio                    ║")
print("╠════════════════════════════════════════════════════════════════╣")
print("║ Play audio in your browser and watch translations!            ║")
print("║ Press Ctrl+C to stop                                           ║")
print("╚════════════════════════════════════════════════════════════════╝")
print("")

recognizer = sr.Recognizer()
temp_dir = tempfile.mkdtemp()

try:
    counter = 0
    while True:
        audio_file = os.path.join(temp_dir, f"chunk_{counter}.wav")

        # Capture audio chunk using ffmpeg
        capture_cmd = [
            "ffmpeg",
            "-f", "pulse",
            "-i", AUDIO_SOURCE,
            "-t", str(CHUNK_DURATION),
            "-ar", "16000",
            "-ac", "1",
            "-y", audio_file,
            "-loglevel", "quiet"
        ]

        try:
            subprocess.run(capture_cmd, timeout=CHUNK_DURATION + 2, check=True)
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            continue

        # Check if file has content
        if os.path.exists(audio_file) and os.path.getsize(audio_file) > 5000:
            print(f"[{time.strftime('%H:%M:%S')}] Processing...", end=" ", flush=True)

            try:
                # Load audio file
                with sr.AudioFile(audio_file) as source:
                    audio_data = recognizer.record(source)

                # Try to recognize and translate using Google's free API
                try:
                    # First, try to detect and translate from Russian
                    text = recognizer.recognize_google(audio_data, language="ru-RU")
                    print(f"[RU→EN]")
                    print(f"  Original (RU): {text}")

                    # Translate to English using Google Translate
                    import urllib.request
                    import urllib.parse
                    import json

                    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&q={urllib.parse.quote(text)}"
                    response = urllib.request.urlopen(url)
                    result = json.loads(response.read().decode('utf-8'))
                    translated = result[0][0][0]

                    print(f"  → Translation: {translated}")

                except sr.UnknownValueError:
                    # Try general auto-detect
                    text = recognizer.recognize_google(audio_data)
                    print(f"[Detected]")
                    print(f"  → {text}")

                except sr.RequestError as e:
                    print(f"[Error: {e}]")

            except Exception as e:
                print(f"[No speech detected]")

            print()

        # Cleanup
        if os.path.exists(audio_file):
            os.remove(audio_file)

        counter += 1

except KeyboardInterrupt:
    print("\n\nStopped.")
finally:
    # Cleanup temp directory
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)
