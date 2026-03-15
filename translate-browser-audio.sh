#!/bin/bash
# Real-time browser audio translation to English CLI
# This script captures audio playing in your browser and translates it to English text in real-time

# Configuration
WHISPER_BIN="/home/steve/whisper.cpp/whisper.cpp/build/bin/whisper-cli"
MODEL="/home/steve/whisper.cpp/whisper.cpp/models/ggml-base.bin"
AUDIO_SOURCE="alsa_output.pci-0000_00_1b.0.analog-stereo.monitor"
CHUNK_DURATION=5  # Process audio in 5-second chunks
TEMP_DIR="/tmp/whisper-live"

# Create temp directory
mkdir -p "$TEMP_DIR"

echo "==== Browser Audio Translation ===="
echo "Source: System audio monitor (captures browser audio)"
echo "Model: Whisper base (auto-detects language, translates to English)"
echo "Processing in ${CHUNK_DURATION}s chunks..."
echo ""
echo "Start playing audio in your browser now!"
echo "Press Ctrl+C to stop"
echo "===================================="
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo "Stopping translation..."
    rm -rf "$TEMP_DIR"
    exit 0
}

trap cleanup INT TERM

# Counter for chunk files
counter=0

while true; do
    # Capture audio chunk
    ffmpeg -f pulse -i "$AUDIO_SOURCE" -t "$CHUNK_DURATION" -ar 16000 -ac 1 -y "$TEMP_DIR/chunk.wav" -loglevel quiet 2>/dev/null

    # Process with whisper if chunk exists and has content
    if [ -f "$TEMP_DIR/chunk.wav" ]; then
        file_size=$(stat -f%z "$TEMP_DIR/chunk.wav" 2>/dev/null || stat -c%s "$TEMP_DIR/chunk.wav" 2>/dev/null)

        # Only process if file has actual audio data (> 1KB)
        if [ "$file_size" -gt 1024 ]; then
            # Run whisper with translation
            "$WHISPER_BIN" -m "$MODEL" -f "$TEMP_DIR/chunk.wav" --translate --no-timestamps --print-colors 2>/dev/null | grep -v "^$"
        fi
    fi

    counter=$((counter + 1))
done
