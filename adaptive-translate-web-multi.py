#!/usr/bin/env python3
"""
Adaptive multi-instance browser audio translation with language detection
Auto-detects language, locks in for accuracy, and adapts when language changes
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
REDETECT_INTERVAL = 20  # Check for language change every N chunks

print("╔════════════════════════════════════════════════════════════════╗")
print("║    ADAPTIVE Audio Translation (3 Overlapping Streams)         ║")
print("╠════════════════════════════════════════════════════════════════╣")
print("║ 1. Auto-detects language being spoken                         ║")
print("║ 2. Locks into detected language for accuracy                  ║")
print("║ 3. Re-detects and adapts when language changes                ║")
print("║ Google Speech Recognition + Translation API                   ║")
print("╠════════════════════════════════════════════════════════════════╣")
print("║ Play audio in your browser - adaptive translation!            ║")
print("║ Press Ctrl+C to stop all instances                            ║")
print("╚════════════════════════════════════════════════════════════════╝")
print("")

# Shared state for detected language
current_language = {"code": None, "name": "Unknown"}
language_lock = threading.Lock()

def translate_instance(instance_id, start_delay):
    """Run a single adaptive translation instance"""
    time.sleep(start_delay)

    recognizer = sr.Recognizer()
    temp_dir = tempfile.mkdtemp(prefix=f"whisper_inst{instance_id}_")

    counter = 0
    local_language = None

    while True:
        audio_file = os.path.join(temp_dir, f"chunk_{counter}.wav")

        # Decide whether to auto-detect or use locked language
        should_detect = (counter % REDETECT_INTERVAL == 0) or (local_language is None)

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
                    if should_detect:
                        # Auto-detect language
                        text = recognizer.recognize_google(audio_data, show_all=True)

                        if text and 'alternative' in text:
                            detected_text = text['alternative'][0]['transcript']

                            # Try to get language from response (Google sometimes includes it)
                            # If not available, we'll use another method
                            # For now, use the detected text and translate it
                            import urllib.request
                            import urllib.parse
                            import json

                            # Use translate API to detect language
                            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&q={urllib.parse.quote(detected_text)}"
                            response = urllib.request.urlopen(url)
                            result = json.loads(response.read().decode('utf-8'))

                            translated = result[0][0][0]
                            detected_lang = result[2] if len(result) > 2 else "unknown"

                            # Update language if changed
                            if detected_lang != local_language and detected_lang != "unknown":
                                local_language = detected_lang
                                with language_lock:
                                    if current_language["code"] != detected_lang:
                                        current_language["code"] = detected_lang
                                        current_language["name"] = detected_lang.upper()
                                        print(f"\n{'='*64}")
                                        print(f"🔍 [LANGUAGE DETECTED] Stream-{instance_id}: {detected_lang.upper()}")
                                        print(f"🔒 [LOCKED IN] Now optimized for {detected_lang.upper()} recognition")
                                        print(f"{'='*64}\n")

                            print(f"[{timestamp}][Stream-{instance_id}][{detected_lang.upper()}] {translated}")
                    else:
                        # Use locked-in language for better accuracy
                        with language_lock:
                            lang_code = current_language["code"]

                        if lang_code:
                            text = recognizer.recognize_google(audio_data, language=lang_code)
                        else:
                            text = recognizer.recognize_google(audio_data)

                        # Translate to English using Google Translate
                        import urllib.request
                        import urllib.parse
                        import json

                        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&q={urllib.parse.quote(text)}"
                        response = urllib.request.urlopen(url)
                        result = json.loads(response.read().decode('utf-8'))
                        translated = result[0][0][0]

                        lang_display = lang_code.upper() if lang_code else "AUTO"
                        print(f"[{timestamp}][Stream-{instance_id}][{lang_display}] {translated}")

                except sr.UnknownValueError:
                    pass  # Silence, don't print
                except sr.RequestError as e:
                    print(f"[{timestamp}][Stream-{instance_id}] API Error: {e}")

            except Exception as e:
                pass  # Ignore errors silently

        # Cleanup
        if os.path.exists(audio_file):
            os.remove(audio_file)

        counter += 1

# Start instances in threads
threads = []
try:
    print(f"Starting {NUM_INSTANCES} adaptive translation streams...\n")
    print(f"🔍 Auto-detection active - listening for any language...\n")

    for i in range(NUM_INSTANCES):
        delay = i * OFFSET
        thread = threading.Thread(target=translate_instance, args=(i+1, delay), daemon=True)
        thread.start()
        threads.append(thread)
        print(f"  Stream {i+1} started (offset: {delay:.1f}s)")

    print("\nAll streams active! Waiting to detect language...\n")
    print("─" * 64)

    # Keep main thread alive
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\n" + "─" * 64)
    print("\nStopping all streams...")
    sys.exit(0)
