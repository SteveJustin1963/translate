#!/bin/bash
# Quick test to see if we can capture audio

echo "Testing audio capture for 5 seconds..."
echo "Make sure audio is playing in your browser NOW!"
echo ""

# Try to capture from the monitor source
ffmpeg -f pulse -i alsa_output.pci-0000_00_1b.0.analog-stereo.monitor -t 5 -ar 16000 -ac 1 -y /tmp/test-capture.wav 2>&1 | grep -E "(Duration|Stream|Input|error)"

if [ -f /tmp/test-capture.wav ]; then
    size=$(stat -c%s /tmp/test-capture.wav 2>/dev/null)
    echo ""
    echo "✓ Captured file size: $size bytes"

    if [ "$size" -gt 10000 ]; then
        echo "✓ File has data - testing with Whisper..."
        /home/steve/whisper.cpp/whisper.cpp/build/bin/whisper-cli -m /home/steve/whisper.cpp/whisper.cpp/models/ggml-base.bin -f /tmp/test-capture.wav --translate --no-timestamps 2>&1 | grep -v "^whisper_" | grep -v "^system_info" | grep -v "^main:" | tail -5
    else
        echo "✗ File is too small - no audio captured"
        echo ""
        echo "This means audio is not going through this device."
        echo "Let's check what audio devices are available:"
        pactl list sources short
    fi
else
    echo "✗ Failed to create capture file"
fi
