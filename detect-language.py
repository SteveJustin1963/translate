#!/usr/bin/env python3
"""
Simple language detection from live audio stream
Captures a few seconds and tells you what language is being spoken
"""

import subprocess
import tempfile
import os
import sys

try:
    import speech_recognition as sr
except ImportError:
    print("Installing speech_recognition library...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--break-system-packages", "SpeechRecognition"])
    import speech_recognition as sr

# Configuration
AUDIO_SOURCE = "alsa_output.pci-0000_00_1b.0.analog-stereo.monitor"
CAPTURE_DURATION = 8  # seconds - capture enough to get good speech sample

print("╔════════════════════════════════════════════════════════════════╗")
print("║                   LANGUAGE DETECTOR                            ║")
print("╠════════════════════════════════════════════════════════════════╣")
print("║ Listening to your audio stream to detect language...          ║")
print("╚════════════════════════════════════════════════════════════════╝")
print("")
print(f"🎧 Capturing {CAPTURE_DURATION} seconds of audio...")
print("   (Make sure audio is playing!)\n")

# Create temp file
temp_dir = tempfile.mkdtemp(prefix="lang_detect_")
audio_file = os.path.join(temp_dir, "sample.wav")

# Capture audio chunk using ffmpeg
capture_cmd = [
    "ffmpeg",
    "-f", "pulse",
    "-i", AUDIO_SOURCE,
    "-t", str(CAPTURE_DURATION),
    "-ar", "16000",
    "-ac", "1",
    "-y", audio_file,
    "-loglevel", "error"
]

try:
    subprocess.run(capture_cmd, timeout=CAPTURE_DURATION + 2, check=True)
    print("✓ Audio captured successfully\n")
except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
    print(f"✗ Failed to capture audio: {e}")
    sys.exit(1)

# Check if file has content
if not os.path.exists(audio_file) or os.path.getsize(audio_file) < 5000:
    print("✗ No audio detected or file too small")
    print("  Make sure audio is playing from your browser!")
    sys.exit(1)

print("🔍 Analyzing audio and detecting language...\n")

recognizer = sr.Recognizer()

try:
    # Load audio file
    with sr.AudioFile(audio_file) as source:
        audio_data = recognizer.record(source)

    # Try to recognize with show_all to get language info
    try:
        text = recognizer.recognize_google(audio_data, show_all=True)

        if text and 'alternative' in text:
            detected_text = text['alternative'][0]['transcript']

            # Use translate API to detect language
            import urllib.request
            import urllib.parse
            import json

            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&q={urllib.parse.quote(detected_text)}"
            response = urllib.request.urlopen(url)
            result = json.loads(response.read().decode('utf-8'))

            translated = result[0][0][0]
            detected_lang = result[2] if len(result) > 2 else "unknown"

            print("=" * 64)
            print(f"🌍 DETECTED LANGUAGE: {detected_lang.upper()}")
            print("=" * 64)
            print(f"\n📝 Original text: {detected_text}")
            print(f"🇬🇧 English translation: {translated}")
            print("\n" + "=" * 64)
            print(f"\n💡 To translate this language, run:")
            print(f"   ./{detected_lang}-translate-web-multi.py")
            print("=" * 64)
        else:
            print("✗ Could not detect speech in the audio")
            print("  Try again with clearer audio or ensure someone is speaking")

    except sr.UnknownValueError:
        print("✗ Could not understand the audio")
        print("  The audio might be too quiet, unclear, or no speech detected")
    except sr.RequestError as e:
        print(f"✗ API Error: {e}")

except Exception as e:
    print(f"✗ Error processing audio: {e}")

# Cleanup
if os.path.exists(audio_file):
    os.remove(audio_file)
if os.path.exists(temp_dir):
    os.rmdir(temp_dir)
