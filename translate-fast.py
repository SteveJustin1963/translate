#!/usr/bin/env python3
"""
Real-time browser audio translation using faster-whisper
Captures system audio and translates ANY language to English in CLI
"""

import subprocess
import tempfile
import os
import time
from faster_whisper import WhisperModel

# Configuration
AUDIO_SOURCE = "alsa_output.pci-0000_00_1b.0.analog-stereo.monitor"
CHUNK_DURATION = 4  # seconds
MODEL_SIZE = "tiny"  # tiny, base, small, medium, large

print("╔════════════════════════════════════════════════════════════════╗")
print("║    FAST Real-Time Browser Audio Translation to English        ║")
print("╠════════════════════════════════════════════════════════════════╣")
print(f"║ Model: Whisper {MODEL_SIZE} (faster-whisper optimized)              ║")
print(f"║ Chunk size: {CHUNK_DURATION} seconds (lower latency)                       ║")
print("║ Auto-detects ANY language → Translates to English             ║")
print("╠════════════════════════════════════════════════════════════════╣")
print("║ Play audio in your browser and watch translations appear!     ║")
print("║ Press Ctrl+C to stop                                           ║")
print("╚════════════════════════════════════════════════════════════════╝")
print("")
print("Loading Whisper model... (first time may download ~75MB)")

# Load model (CPU, int8 for speed)
model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
print("✓ Model loaded! Starting capture...\n")

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

            # Transcribe and translate
            segments, info = model.transcribe(
                audio_file,
                task="translate",  # Force translation to English
                language=None,  # Auto-detect
                beam_size=1,  # Faster (less accurate)
                vad_filter=True,  # Skip silence
            )

            # Print results
            has_speech = False
            for segment in segments:
                text = segment.text.strip()
                if text:
                    if not has_speech:
                        print(f"[{info.language.upper()}→EN]")
                        has_speech = True
                    print(f"  → {text}")

            if not has_speech:
                print("[No speech detected]")
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
