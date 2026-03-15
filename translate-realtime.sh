#!/bin/bash
# Real-time browser audio translation using whisper-stream
# Optimized for speed with tiny model

WHISPER_STREAM="/home/steve/whisper.cpp/whisper.cpp/build/bin/whisper-stream"
MODEL="/home/steve/whisper.cpp/whisper.cpp/models/ggml-tiny.bin"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         Real-Time Audio Translation (Browser → English)        ║"
echo "╠════════════════════════════════════════════════════════════════╣"
echo "║ Using: Whisper tiny model (fast, lower accuracy)              ║"
echo "║ Mode: Real-time streaming with auto language detection        ║"
echo "║ Translation: ANY language → English                            ║"
echo "╠════════════════════════════════════════════════════════════════╣"
echo "║ Make sure audio is playing in your browser!                   ║"
echo "║ Press Ctrl+C to stop                                           ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Run whisper-stream with system audio monitor
# The -c flag specifies audio capture device (SDL will use system audio)
# --translate forces translation to English
"$WHISPER_STREAM" \
    -m "$MODEL" \
    --translate \
    -t 2 \
    --step 2000 \
    --length 8000 \
    --keep 200

