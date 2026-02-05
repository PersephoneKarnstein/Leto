#!/usr/bin/env python3
"""
Check availability of Hermes analysis tools.
Outputs status for each tool and provides installation commands.

Usage:
    python check_tools.py [--json] [--install-help]
"""

import subprocess
import shutil
import sys
import json
import argparse
import os


TOOLS = {
    "radare2": {
        "check_cmd": ["r2", "-v"],
        "install": {
            "macos": "brew install radare2",
            "linux": "git clone https://github.com/radareorg/radare2 && cd radare2 && sys/install.sh",
        },
        "required_for": ["r2hermes"],
    },
    "maestro": {
        "check_cmd": ["maestro", "--version"],
        "install": {
            "all": 'curl -fsSL "https://get.maestro.mobile.dev" | bash',
        },
        "required_for": ["UI automation", "dynamic analysis"],
        "optional": True,
    },
    "burpsuite": {
        "check_paths": [
            "/Applications/Burp Suite Community Edition.app",
            "/Applications/Burp Suite Professional.app",
            "/usr/share/burpsuite",
            "/opt/BurpSuiteCommunity",
        ],
        "install": {
            "macos": "Download from https://portswigger.net/burp/communitydownload",
            "linux": "Download from https://portswigger.net/burp/communitydownload",
        },
        "required_for": ["traffic interception", "HTTPS analysis"],
        "optional": True,
    },
    "openssl": {
        "check_cmd": ["openssl", "version"],
        "install": {
            "macos": "brew install openssl",
            "linux": "apt install openssl",
        },
        "required_for": ["certificate conversion", "Burp setup"],
    },
    "java": {
        "check_cmd": ["java", "-version"],
        "install": {
            "macos": "brew install openjdk@17",
            "linux": "apt install openjdk-17-jdk",
        },
        "required_for": ["Maestro"],
    },
    "android-studio": {
        "check_paths": [
            "/Applications/Android Studio.app",
            "/usr/local/android-studio",
            "/opt/android-studio",
            os.path.expanduser("~/android-studio"),
        ],
        "install": {
            "macos": "Download from https://developer.android.com/studio",
            "linux": "Download from https://developer.android.com/studio",
        },
        "required_for": ["AVD creation", "emulator management", "SDK tools"],
    },
    "emulator": {
        "check_cmd": ["emulator", "-version"],
        "check_paths": [
            os.path.expanduser("~/Library/Android/sdk/emulator/emulator"),
            os.path.expanduser("~/Android/Sdk/emulator/emulator"),
            "/usr/local/share/android-sdk/emulator/emulator",
        ],
        "install": {
            "all": "Install via Android Studio SDK Manager or: sdkmanager 'emulator'",
        },
        "required_for": ["running Android VMs", "dynamic analysis"],
    },
    "avdmanager": {
        "check_cmd": ["avdmanager", "list", "avd"],
        "check_paths": [
            os.path.expanduser("~/Library/Android/sdk/cmdline-tools/latest/bin/avdmanager"),
            os.path.expanduser("~/Android/Sdk/cmdline-tools/latest/bin/avdmanager"),
        ],
        "install": {
            "all": "Install via Android Studio SDK Manager or: sdkmanager 'cmdline-tools;latest'",
        },
        "required_for": ["AVD creation/management"],
    },
    "sdkmanager": {
        "check_cmd": ["sdkmanager", "--version"],
        "check_paths": [
            os.path.expanduser("~/Library/Android/sdk/cmdline-tools/latest/bin/sdkmanager"),
            os.path.expanduser("~/Android/Sdk/cmdline-tools/latest/bin/sdkmanager"),
        ],
        "install": {
            "all": "Install via Android Studio SDK Manager",
        },
        "required_for": ["SDK component installation", "system images"],
    },
    "r2hermes": {
        "check_cmd": ["r2", "-qc", "pd:h?", "/dev/null"],
        "check_output": "Usage",
        "install": {"all": "r2pm -ci r2hermes"},
        "required_for": ["primary decompilation"],
    },
    "python3": {
        "check_cmd": ["python3", "--version"],
        "install": {
            "macos": "brew install python3",
            "linux": "apt install python3 python3-pip",
        },
        "required_for": ["hbctool", "hermes-dec"],
    },
    "hbctool": {
        "check_cmd": ["hbctool", "--help"],
        "install": {"all": "pip install hbctool"},
        "required_for": ["disassembly/reassembly"],
    },
    "hermes-dec": {
        "check_cmd": ["hbc-decompiler", "--help"],
        "install": {"all": "pip install git+https://github.com/P1sec/hermes-dec"},
        "required_for": ["pure Python decompilation"],
    },
    "cargo": {
        "check_cmd": ["cargo", "--version"],
        "install": {
            "all": "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
        },
        "required_for": ["hermes_rs"],
    },
    "hermes_rs": {
        "check_cmd": ["hermes_rs", "--help"],
        "install": {"all": "cargo install --git https://github.com/Pilfer/hermes_rs"},
        "required_for": ["module extraction", "string analysis"],
        "optional": True,
    },
    "frida": {
        "check_cmd": ["frida", "--version"],
        "install": {"all": "pip install frida-tools"},
        "required_for": ["runtime instrumentation"],
    },
    "r2frida": {
        "check_cmd": ["r2", "-qc", ":?", "frida://0"],
        "check_output": "Usage",
        "install": {"all": "r2pm -ci r2frida"},
        "required_for": ["Frida integration in radare2", "runtime process analysis"],
    },
    "r2ai": {
        "check_cmd": ["r2", "-qc", "r2ai -h", "--"],
        "install": {"all": "r2pm -ci r2ai"},
        "required_for": ["AI-assisted reverse engineering", "automated analysis"],
        "optional": True,
    },
    "adb": {
        "check_cmd": ["adb", "version"],
        "install": {
            "macos": "brew install android-platform-tools",
            "linux": "apt install adb",
        },
        "required_for": ["device interaction", "APK extraction"],
    },
    "apktool": {
        "check_cmd": ["apktool", "--version"],
        "install": {
            "macos": "brew install apktool",
            "linux": "apt install apktool",
        },
        "required_for": ["APK decompilation/repackaging"],
    },
    "jadx": {
        "check_cmd": ["jadx", "--version"],
        "install": {
            "macos": "brew install jadx",
            "linux": "Download from https://github.com/skylot/jadx/releases",
        },
        "required_for": ["Java decompilation", "BuildConfig secrets", "native code analysis"],
    },
    "mitmproxy": {
        "check_cmd": ["mitmproxy", "--version"],
        "install": {
            "all": "pip install mitmproxy",
        },
        "required_for": ["traffic interception", "API analysis"],
        "optional": True,
    },
    "objection": {
        "check_cmd": ["objection", "version"],
        "install": {
            "all": "pip install objection",
        },
        "required_for": ["APK patching", "Frida gadget injection", "SSL bypass"],
    },
    "apksigner": {
        "check_cmd": ["apksigner", "--version"],
        "check_paths": [
            os.path.expanduser("~/Library/Android/sdk/build-tools/34.0.0/apksigner"),
            os.path.expanduser("~/Library/Android/sdk/build-tools/33.0.0/apksigner"),
            os.path.expanduser("~/Android/Sdk/build-tools/34.0.0/apksigner"),
        ],
        "install": {
            "all": "Install via Android Studio SDK Manager: sdkmanager 'build-tools;34.0.0'",
        },
        "required_for": ["APK signing", "APK patching"],
    },
    "zipalign": {
        "check_cmd": ["zipalign", "-h"],
        "check_paths": [
            os.path.expanduser("~/Library/Android/sdk/build-tools/34.0.0/zipalign"),
            os.path.expanduser("~/Library/Android/sdk/build-tools/33.0.0/zipalign"),
            os.path.expanduser("~/Android/Sdk/build-tools/34.0.0/zipalign"),
        ],
        "install": {
            "all": "Install via Android Studio SDK Manager: sdkmanager 'build-tools;34.0.0'",
        },
        "required_for": ["APK alignment", "APK patching"],
    },
    "gitleaks": {
        "check_cmd": ["gitleaks", "version"],
        "install": {
            "macos": "brew install gitleaks",
            "linux": "brew install gitleaks",
        },
        "required_for": ["secret scanning", "API key detection"],
        "optional": True,
    },
    "trufflehog": {
        "check_cmd": ["trufflehog", "--version"],
        "install": {
            "macos": "brew install trufflehog",
            "linux": "brew install trufflehog",
        },
        "required_for": ["deep secret scanning", "credential detection"],
        "optional": True,
    },
    "semgrep": {
        "check_cmd": ["semgrep", "--version"],
        "install": {"all": "pip install semgrep"},
        "required_for": ["static analysis", "security rule scanning"],
        "optional": True,
    },
}


def check_tool(name: str, config: dict) -> dict:
    """Check if a tool is available."""
    result = {
        "name": name,
        "installed": False,
        "version": None,
        "error": None,
    }

    # First try command-based check if available
    if "check_cmd" in config:
        try:
            proc = subprocess.run(
                config["check_cmd"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            output = proc.stdout + proc.stderr

            # Some tools need specific output check
            if "check_output" in config:
                if config["check_output"] in output:
                    result["installed"] = True
                    result["version"] = output.strip()[:50]
                    return result
            elif proc.returncode == 0:
                result["installed"] = True
                result["version"] = output.strip().split("\n")[0][:50]
                return result

        except FileNotFoundError:
            pass  # Try path-based check next
        except subprocess.TimeoutExpired:
            result["error"] = "timeout"
            return result
        except Exception as e:
            pass  # Try path-based check next

    # Fall back to path-based checks if command not found
    if "check_paths" in config:
        for path in config["check_paths"]:
            expanded_path = os.path.expanduser(path) if "~" in path else path
            if os.path.exists(expanded_path):
                result["installed"] = True
                result["version"] = f"found at {expanded_path}"
                return result

    # Neither check succeeded
    if not result["error"]:
        result["error"] = "not found"

    return result


def get_platform() -> str:
    """Detect current platform."""
    import platform

    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    elif system == "linux":
        return "linux"
    return "unknown"


def main():
    parser = argparse.ArgumentParser(description="Check Hermes analysis tools")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--install-help", action="store_true", help="Show installation commands"
    )
    args = parser.parse_args()

    platform = get_platform()
    results = []

    for name, config in TOOLS.items():
        result = check_tool(name, config)
        result["install_cmd"] = config["install"].get(
            platform, config["install"].get("all", "see docs")
        )
        result["required_for"] = config.get("required_for", [])
        result["optional"] = config.get("optional", False)
        results.append(result)

    if args.json:
        print(json.dumps(results, indent=2))
        return

    # Pretty print
    print("Hermes Analysis Tool Status")
    print("=" * 50)

    installed = []
    missing = []

    for r in results:
        status = "OK" if r["installed"] else "MISSING"
        optional = " (optional)" if r["optional"] else ""
        print(f"  {r['name']:15} [{status}]{optional}")
        if r["installed"]:
            installed.append(r["name"])
        else:
            missing.append(r)

    print()
    print(f"Installed: {len(installed)}/{len(results)}")

    if missing and args.install_help:
        print()
        print("Installation Commands:")
        print("-" * 50)
        for r in missing:
            print(f"# {r['name']} - needed for: {', '.join(r['required_for'])}")
            print(f"  {r['install_cmd']}")
            print()


if __name__ == "__main__":
    main()
