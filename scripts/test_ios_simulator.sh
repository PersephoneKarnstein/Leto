#!/bin/bash
# iOS Simulator and Maestro/Frida Test Script
# Requires: Xcode with iOS Simulator

set -e

echo "=== iOS Simulator Test Script ==="
echo ""

# Check Xcode installation
echo "[1/7] Checking Xcode installation..."
if ! xcode-select -p &>/dev/null; then
    echo "ERROR: Xcode not installed. Install from App Store or:"
    echo "  xcode-select --install  (for command line tools only)"
    echo "  Full Xcode required for iOS Simulator"
    exit 1
fi

XCODE_PATH=$(xcode-select -p)
echo "  Xcode path: $XCODE_PATH"

# Check simctl
echo ""
echo "[2/7] Checking simctl..."
if ! xcrun simctl list devices &>/dev/null; then
    echo "ERROR: simctl not available. Make sure full Xcode is installed."
    echo "  Try: sudo xcode-select -s /Applications/Xcode.app/Contents/Developer"
    exit 1
fi
echo "  simctl available"

# List available simulators
echo ""
echo "[3/7] Available iOS Simulators:"
xcrun simctl list devices available | grep -E "iPhone|iPad" | head -10

# Boot a simulator (iPhone 15 Pro or first available)
echo ""
echo "[4/7] Booting iOS Simulator..."
DEVICE_NAME="iPhone 15 Pro"
DEVICE_ID=$(xcrun simctl list devices available | grep "$DEVICE_NAME" | grep -oE '[A-F0-9-]{36}' | head -1)

if [ -z "$DEVICE_ID" ]; then
    echo "  $DEVICE_NAME not found, using first available iPhone..."
    DEVICE_ID=$(xcrun simctl list devices available | grep "iPhone" | grep -oE '[A-F0-9-]{36}' | head -1)
fi

if [ -z "$DEVICE_ID" ]; then
    echo "ERROR: No iOS Simulator found. Install iOS runtime:"
    echo "  xcodebuild -downloadPlatform iOS"
    exit 1
fi

echo "  Booting device: $DEVICE_ID"
xcrun simctl boot "$DEVICE_ID" 2>/dev/null || echo "  (already booted)"

# Open Simulator app
echo ""
echo "[5/7] Opening Simulator app..."
open -a Simulator

# Wait for simulator to be ready
echo "  Waiting for simulator to be ready..."
sleep 5

# Install Wikipedia sample app (if available)
echo ""
echo "[6/7] Installing sample app..."
SAMPLE_APP="/tmp/maestro_sample/Wikipedia.app"
if [ -d "$SAMPLE_APP" ]; then
    xcrun simctl install booted "$SAMPLE_APP"
    echo "  Installed Wikipedia.app"
else
    echo "  Sample app not found. Extract with:"
    echo "  unzip -o samples/sample.zip -d /tmp/maestro_sample/"
fi

# Test Maestro
echo ""
echo "[7/7] Testing Maestro..."
if command -v maestro &>/dev/null || [ -x "$HOME/.maestro/bin/maestro" ]; then
    MAESTRO="${HOME}/.maestro/bin/maestro"
    echo "  Maestro version: $($MAESTRO --version)"
    echo ""
    echo "  Run Maestro test with:"
    echo "    $MAESTRO test samples/ios-flow.yaml"
else
    echo "  Maestro not found. Install with:"
    echo "  curl -fsSL \"https://get.maestro.mobile.dev\" | bash"
fi

echo ""
echo "=== iOS Simulator Ready ==="
echo ""
echo "Useful commands:"
echo "  xcrun simctl list devices              # List simulators"
echo "  xcrun simctl boot 'iPhone 15 Pro'      # Boot specific device"
echo "  xcrun simctl install booted app.app    # Install .app (NOT .ipa)"
echo "  xcrun simctl launch booted bundle.id   # Launch app"
echo "  xcrun simctl screenshot booted out.png # Take screenshot"
echo "  maestro test flow.yaml                 # Run Maestro flow"
echo ""
echo "NOTE: App Store IPAs (arm64 device) cannot run in simulator!"
echo "      Simulator requires apps built for simulator architecture."
