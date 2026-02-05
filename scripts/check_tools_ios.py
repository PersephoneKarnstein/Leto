#!/usr/bin/env python3
"""
Check availability of iOS Hermes analysis tools.
Outputs status for each tool and provides installation commands.

Usage:
    python check_tools_ios.py [--json] [--install-help]
"""

import subprocess
import shutil
import sys
import json
import argparse
import os


TOOLS = {
    "xcode": {
        "check_cmd": ["xcode-select", "-p"],
        "check_output": "/Applications/Xcode.app",
        "install": {
            "macos": "Install Xcode from App Store (15GB+), then: sudo xcode-select -s /Applications/Xcode.app/Contents/Developer",
        },
        "required_for": ["iOS Simulator", "code signing", "xcrun commands"],
    },
    "xcrun": {
        "check_cmd": ["xcrun", "--version"],
        "install": {
            "macos": "Included with Xcode",
        },
        "required_for": ["simctl", "codesign", "plutil"],
    },
    "simctl": {
        "check_cmd": ["xcrun", "simctl", "list", "devices"],
        "install": {
            "macos": "Included with Xcode (requires full Xcode, not just Command Line Tools)",
        },
        "required_for": ["iOS Simulator management", "app installation", "deep link testing"],
    },
    "ios-simulator": {
        "check_cmd": ["xcrun", "simctl", "list", "runtimes"],
        "check_output": "iOS",
        "install": {
            "macos": "xcodebuild -downloadPlatform iOS",
        },
        "required_for": ["running iOS apps in simulator"],
    },
    "codesign": {
        "check_cmd": ["codesign", "--help"],
        "install": {
            "macos": "Included with Xcode Command Line Tools",
        },
        "required_for": ["entitlements extraction", "IPA signing"],
    },
    "plutil": {
        "check_cmd": ["plutil", "-help"],
        "install": {
            "macos": "Built into macOS",
        },
        "required_for": ["Info.plist parsing", "privacy manifest analysis"],
    },
    "radare2": {
        "check_cmd": ["r2", "-v"],
        "install": {
            "macos": "brew install radare2",
            "linux": "git clone https://github.com/radareorg/radare2 && cd radare2 && sys/install.sh",
        },
        "required_for": ["r2hermes"],
    },
    "r2hermes": {
        "check_cmd": ["r2", "-qc", "pd:h?", "/dev/null"],
        "check_output": "Usage",
        "install": {"all": "r2pm -ci r2hermes"},
        "required_for": ["Hermes bytecode decompilation"],
    },
    "python3": {
        "check_cmd": ["python3", "--version"],
        "install": {
            "macos": "brew install python3",
            "linux": "apt install python3 python3-pip",
        },
        "required_for": ["hbctool", "hermes-dec", "analysis scripts"],
    },
    "hbctool": {
        "check_cmd": ["hbctool", "--help"],
        "install": {"all": "pip install hbctool"},
        "required_for": ["Hermes disassembly/reassembly"],
    },
    "hermes-dec": {
        "check_cmd": ["hbc-decompiler", "--help"],
        "install": {"all": "pip install git+https://github.com/P1sec/hermes-dec"},
        "required_for": ["pure Python Hermes decompilation"],
    },
    "frida": {
        "check_cmd": ["frida", "--version"],
        "install": {"all": "pip install frida-tools"},
        "required_for": ["runtime instrumentation", "SSL bypass", "jailbreak bypass"],
    },
    "objection": {
        "check_cmd": ["objection", "version"],
        "install": {
            "all": "pip install objection",
        },
        "required_for": ["IPA patching", "Frida gadget injection", "keychain dumping"],
    },
    "ios-deploy": {
        "check_cmd": ["ios-deploy", "--version"],
        "install": {
            "macos": "brew install ios-deploy",
        },
        "required_for": ["deploying apps to physical devices"],
        "optional": True,
    },
    "maestro": {
        "check_cmd": ["maestro", "--version"],
        "install": {
            "all": 'curl -fsSL "https://get.maestro.mobile.dev" | bash',
        },
        "required_for": ["UI automation", "flow testing"],
        "optional": True,
    },
    "java": {
        "check_cmd": ["java", "-version"],
        "install": {
            "macos": "brew install openjdk@17",
            "linux": "apt install openjdk-17-jdk",
        },
        "required_for": ["Maestro"],
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
    "openssl": {
        "check_cmd": ["openssl", "version"],
        "install": {
            "macos": "brew install openssl",
            "linux": "apt install openssl",
        },
        "required_for": ["certificate analysis", "Burp setup"],
    },
    "burpsuite": {
        "check_paths": [
            "/Applications/Burp Suite Community Edition.app",
            "/Applications/Burp Suite Professional.app",
        ],
        "install": {
            "macos": "Download from https://portswigger.net/burp/communitydownload",
        },
        "required_for": ["traffic interception", "API testing"],
        "optional": True,
    },
    "mitmproxy": {
        "check_cmd": ["mitmproxy", "--version"],
        "install": {
            "all": "pip install mitmproxy",
        },
        "required_for": ["traffic interception", "API analysis"],
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
                    result["version"] = output.strip()[:100]
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


def check_xcode_setup() -> dict:
    """Check Xcode configuration details."""
    info = {
        "xcode_path": None,
        "command_line_tools_only": False,
        "simulators": [],
        "ios_runtimes": [],
    }

    try:
        # Check xcode-select path
        result = subprocess.run(
            ["xcode-select", "-p"],
            capture_output=True,
            text=True,
            timeout=5
        )
        info["xcode_path"] = result.stdout.strip()
        info["command_line_tools_only"] = "CommandLineTools" in result.stdout

        # List iOS runtimes
        if not info["command_line_tools_only"]:
            result = subprocess.run(
                ["xcrun", "simctl", "list", "runtimes", "--json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                info["ios_runtimes"] = [
                    r["name"] for r in data.get("runtimes", [])
                    if "iOS" in r.get("name", "")
                ]

            # List available simulators
            result = subprocess.run(
                ["xcrun", "simctl", "list", "devices", "available", "--json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                for runtime, devices in data.get("devices", {}).items():
                    if "iOS" in runtime:
                        for device in devices:
                            info["simulators"].append(f"{device['name']} ({runtime.split('.')[-1]})")
    except Exception:
        pass

    return info


def main():
    parser = argparse.ArgumentParser(description="Check iOS Hermes analysis tools")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--install-help", action="store_true", help="Show installation commands"
    )
    args = parser.parse_args()

    platform = get_platform()

    if platform != "macos":
        print("WARNING: iOS development tools require macOS")
        print()

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
        output = {
            "tools": results,
            "xcode_info": check_xcode_setup() if platform == "macos" else None
        }
        print(json.dumps(output, indent=2))
        return

    # Pretty print
    print("iOS Hermes Analysis Tool Status")
    print("=" * 55)

    installed = []
    missing = []

    for r in results:
        status = "OK" if r["installed"] else "MISSING"
        optional = " (optional)" if r["optional"] else ""
        print(f"  {r['name']:18} [{status}]{optional}")
        if r["installed"]:
            installed.append(r["name"])
        else:
            missing.append(r)

    print()
    print(f"Installed: {len(installed)}/{len(results)}")

    # Show Xcode setup info
    if platform == "macos":
        xcode_info = check_xcode_setup()
        print()
        print("Xcode Configuration:")
        print("-" * 55)
        if xcode_info["xcode_path"]:
            print(f"  Path: {xcode_info['xcode_path']}")
            if xcode_info["command_line_tools_only"]:
                print("  WARNING: Command Line Tools only - no Simulator support!")
                print("  Install full Xcode from App Store for Simulator")
            else:
                if xcode_info["ios_runtimes"]:
                    print(f"  iOS Runtimes: {', '.join(xcode_info['ios_runtimes'][:3])}")
                if xcode_info["simulators"]:
                    print(f"  Simulators: {len(xcode_info['simulators'])} available")
        else:
            print("  Xcode not configured")

    if missing and args.install_help:
        print()
        print("Installation Commands:")
        print("-" * 55)
        for r in missing:
            print(f"# {r['name']} - needed for: {', '.join(r['required_for'])}")
            print(f"  {r['install_cmd']}")
            print()


if __name__ == "__main__":
    main()
