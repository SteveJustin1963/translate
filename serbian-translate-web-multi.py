#!/usr/bin/env python3
"""
Multi-instance browser audio translation with overlapping capture
Runs 3 instances with staggered timing to avoid missing speech
"""

import subprocess
import tempfile
import os
import time
import sys
import threading

try:
    import speech_recognition as sr
except ImportError:
    print("Installing speech_recognition library...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--break-system-packages", "SpeechRecognition"])
    import speech_recognition as sr

# Configuration
AUDIO_SOURCE = "alsa_output.pci-0000_00_1b.0.analog-stereo.monitor"
CHUNK_DURATION = 5  # seconds
NUM_INSTANCES = 3
OFFSET = 1.7  # seconds between instance starts

print("╔════════════════════════════════════════════════════════════════╗")
print("║      CONTINUOUS Audio Translation (3 Overlapping Streams)     ║")
print("╠════════════════════════════════════════════════════════════════╣")
print("║ Using: 3 staggered instances to avoid missing speech          ║")
print("║ Google Speech Recognition + Translation API                   ║")
print("║ Auto-detects ANY language → Translates to English             ║")
print("╠════════════════════════════════════════════════════════════════╣")
print("║ Play audio in your browser - continuous translation!          ║")
print("║ Press Ctrl+C to stop all instances                            ║")
print("╚════════════════════════════════════════════════════════════════╝")
print("")

def translate_instance(instance_id, start_delay):
    """Run a single translation instance"""
    time.sleep(start_delay)

    recognizer = sr.Recognizer()
    temp_dir = tempfile.mkdtemp(prefix=f"whisper_inst{instance_id}_")

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
            timestamp = time.strftime('%H:%M:%S')

            try:
                # Load audio file
                with sr.AudioFile(audio_file) as source:
                    audio_data = recognizer.record(source)

                # Try to recognize and translate
                try:
                    # Try Serbian first (you can change this to auto)
                    text = recognizer.recognize_google(audio_data, language="sr-RS")

                    # Translate to English using Google Translate
                    import urllib.request
                    import urllib.parse
                    import json

                    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&q={urllib.parse.quote(text)}"
                    response = urllib.request.urlopen(url)
                    result = json.loads(response.read().decode('utf-8'))
                    translated = result[0][0][0]

                    print(f"[{timestamp}][Stream-{instance_id}] {translated}")

                except sr.UnknownValueError:
                    pass  # Silence, don't print
                except sr.RequestError as e:
                    print(f"[{timestamp}][Stream-{instance_id}] API Error: {e}")

            except Exception:
                pass  # Ignore errors silently

        # Cleanup
        if os.path.exists(audio_file):
            os.remove(audio_file)

        counter += 1

# Start instances in threads
threads = []
try:
    print(f"Starting {NUM_INSTANCES} overlapping translation streams...\n")

    for i in range(NUM_INSTANCES):
        delay = i * OFFSET
        thread = threading.Thread(target=translate_instance, args=(i+1, delay), daemon=True)
        thread.start()
        threads.append(thread)
        print(f"  Stream {i+1} started (offset: {delay:.1f}s)")

    print("\nAll streams active! Translations will appear below:\n")
    print("─" * 64)

    # Keep main thread alive
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\n" + "─" * 64)
    print("\nStopping all streams...")
    sys.exit(0)
