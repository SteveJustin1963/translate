#!/bin/bash
# Improved real-time browser audio translation using continuous processing
# This version has lower latency by using shorter chunks

WHISPER_BIN="/home/steve/whisper.cpp/whisper.cpp/build/bin/whisper-cli"
MODEL="/home/steve/whisper.cpp/whisper.cpp/models/ggml-base.bin"
AUDIO_SOURCE="alsa_output.pci-0000_00_1b.0.analog-stereo.monitor"
CHUNK_DURATION=3  # Shorter chunks for lower latency
TEMP_DIR="/tmp/whisper-live"

mkdir -p "$TEMP_DIR"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         Real-Time Browser Audio Translation to English         ║"
echo "╠════════════════════════════════════════════════════════════════╣"
echo "║ Source: System audio (captures all browser audio)             ║"
echo "║ Model: Whisper base (auto-detects any language)               ║"
echo "║ Translation: Automatic to English                             ║"
echo "║ Latency: ~${CHUNK_DURATION} seconds                                           ║"
echo "╠════════════════════════════════════════════════════════════════╣"
echo "║ Play audio in your browser and watch translations appear below║"
echo "║ Press Ctrl+C to stop                                           ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

cleanup() {
    echo ""
    echo "Stopped."
    rm -rf "$TEMP_DIR"
    pkill -P $$ 2>/dev/null
    exit 0
}

trap cleanup INT TERM

counter=0
while true; do
    chunk_file="$TEMP_DIR/chunk_${counter}.wav"

    # Capture audio
    ffmpeg -f pulse -i "$AUDIO_SOURCE" -t "$CHUNK_DURATION" -ar 16000 -ac 1 -y "$chunk_file" -loglevel error 2>/dev/null

    # Check if file has audio
    if [ -f "$chunk_file" ]; then
        size=$(stat -c%s "$chunk_file" 2>/dev/null || stat -f%z "$chunk_file" 2>/dev/null)

        if [ "$size" -gt 2048 ]; then
            # Process with Whisper - suppress most output, show only translation
            echo "[$(date +%H:%M:%S)] Translating..."
            "$WHISPER_BIN" -m "$MODEL" -f "$chunk_file" --translate --no-timestamps --language auto -t 4 2>/dev/null | \
                grep -v "^whisper_" | \
                grep -v "^system_info" | \
                grep -v "^main:" | \
                grep -v "^$" | \
                sed 's/^[[:space:]]*/  → /'
            echo ""
        fi

        rm -f "$chunk_file"
    fi

    counter=$((counter + 1))
done
