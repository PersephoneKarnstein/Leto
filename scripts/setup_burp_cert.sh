#!/bin/bash
# Setup Burp Suite certificate for Android emulator HTTPS interception
#
# Usage:
#   ./setup_burp_cert.sh /path/to/burp_cert.der
#
# Prerequisites:
#   - Burp Suite certificate exported as DER format
#   - Android emulator running (without Play Store for root access)
#   - ADB available and connected

set -e

CERT_PATH="${1:-burp_cert.der}"
WORK_DIR="/tmp/burp_cert_setup"

echo "=== Burp Suite Certificate Setup for Android ==="
echo

# Check prerequisites
if ! command -v adb &> /dev/null; then
    echo "ERROR: adb not found. Install Android SDK platform-tools."
    exit 1
fi

if ! command -v openssl &> /dev/null; then
    echo "ERROR: openssl not found. Install with: brew install openssl"
    exit 1
fi

if [ ! -f "$CERT_PATH" ]; then
    echo "ERROR: Certificate not found: $CERT_PATH"
    echo
    echo "Export from Burp Suite:"
    echo "  Proxy > Options > Import/Export CA Certificate > Export in DER format"
    exit 1
fi

# Check ADB connection
if ! adb get-state &> /dev/null; then
    echo "ERROR: No Android device connected. Start an emulator first."
    exit 1
fi

echo "[*] Using certificate: $CERT_PATH"
mkdir -p "$WORK_DIR"

# Convert DER to PEM
echo "[*] Converting certificate format..."
openssl x509 -inform DER -in "$CERT_PATH" -out "$WORK_DIR/burp_cert.pem"

# Get hash for Android filename
HASH=$(openssl x509 -inform PEM -subject_hash_old -in "$WORK_DIR/burp_cert.pem" | head -1)
echo "[*] Certificate hash: $HASH"

# Create Android-format certificate
cp "$WORK_DIR/burp_cert.pem" "$WORK_DIR/${HASH}.0"

# Try to install on device
echo "[*] Installing certificate on device..."

# Try adb root first
if adb root 2>/dev/null | grep -q "adbd is already running as root\|restarting adbd as root"; then
    echo "[*] ADB running as root"
    sleep 2

    # Try remount
    if adb remount 2>&1 | grep -q "remount succeeded\|Remount succeeded"; then
        echo "[*] System remounted as writable"
        adb push "$WORK_DIR/${HASH}.0" /system/etc/security/cacerts/
        adb shell chmod 644 /system/etc/security/cacerts/${HASH}.0
        echo "[+] Certificate installed to system store"
        echo "[*] Rebooting device..."
        adb reboot
        echo "[+] Done! Wait for device to reboot."
    else
        echo "[!] Remount failed, trying tmpfs overlay method..."
        adb shell "mount -t tmpfs tmpfs /system/etc/security/cacerts" 2>/dev/null || true
        adb shell "cp /system_ext/etc/security/cacerts/* /system/etc/security/cacerts/" 2>/dev/null || \
        adb shell "cp /apex/com.android.conscrypt/cacerts/* /system/etc/security/cacerts/" 2>/dev/null || true
        adb push "$WORK_DIR/${HASH}.0" /system/etc/security/cacerts/
        adb shell chmod 644 /system/etc/security/cacerts/${HASH}.0
        echo "[+] Certificate installed (tmpfs - won't persist after reboot)"
    fi
else
    echo "[!] Cannot get root access. Options:"
    echo "    1. Use an emulator without Google Play Store"
    echo "    2. Use rootAVD: https://github.com/newbit1/rootAVD"
    echo "    3. Install cert in user store (may not work for all apps):"
    echo "       adb push $WORK_DIR/${HASH}.0 /sdcard/"
    echo "       Settings > Security > Install from storage"
    exit 1
fi

# Show proxy setup instructions
echo
echo "=== Next Steps ==="
echo
echo "1. Configure Burp Suite:"
echo "   Proxy > Options > Proxy Listeners > Add"
echo "   Bind to port: 8080"
echo "   Bind to address: All interfaces"
echo
echo "2. Set proxy on emulator:"
IP=$(ifconfig 2>/dev/null | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')
if [ -n "$IP" ]; then
    echo "   adb shell settings put global http_proxy $IP:8080"
    echo
    echo "   Or run:"
    echo "   adb shell settings put global http_proxy $IP:8080"
fi
echo
echo "3. To clear proxy when done:"
echo "   adb shell settings put global http_proxy :0"
echo

# Cleanup
rm -rf "$WORK_DIR"
