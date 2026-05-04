# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""
Upload models to Steam Workshop using SteamCMD.
Requires SteamCMD and Steam Workshop tool.

Usage:
    uv run upload_steam_workshop.py
    uv run upload_steam_workshop.py --workshop-dir "F:/SteamLibrary/steamapps/common/Counter-Strike Global Offensive/game/csgo_addons/upkkmodelpack2026_agents"
    uv run upload_steam_workshop.py --steamcmd-dir "F:/SteamCMD"
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

# ============================================================
# DEFAULT CONFIGURATION
# ============================================================
DEFAULT_WORKSHOP_DIR = r"F:/SteamLibrary/steamapps/common/Counter-Strike Global Offensive/game/csgo_addons/upkkmodelpack2026_agents"
DEFAULT_STEAMCMD_DIR = r"F:/SteamCMD"
DEFAULT_STEAM_USER = "anonymous"  # Use your Steam username for non-anonymous upload


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Upload to Steam Workshop via SteamCMD")
    parser.add_argument(
        "--workshop-dir",
        default=DEFAULT_WORKSHOP_DIR,
        help=f"Path to workshop addon directory (default: {DEFAULT_WORKSHOP_DIR})",
    )
    parser.add_argument(
        "--steamcmd-dir",
        default=DEFAULT_STEAMCMD_DIR,
        help=f"Path to SteamCMD directory (default: {DEFAULT_STEAMCMD_DIR})",
    )
    parser.add_argument(
        "--steam-user",
        default=DEFAULT_STEAM_USER,
        help=f"Steam username (default: {DEFAULT_STEAM_USER} for anonymous)",
    )
    parser.add_argument(
        "--steam-password",
        default="",
        help="Steam password (leave empty for anonymous or cached login)",
    )
    return parser.parse_args()


def check_steamcmd(steamcmd_dir):
    """Check if SteamCMD exists."""
    steamcmd_exe = Path(steamcmd_dir) / "steamcmd.exe"
    if not steamcmd_exe.exists():
        print(f"[ERROR] SteamCMD not found at: {steamcmd_exe}")
        print("Please make sure SteamCMD is installed.")
        return None
    return steamcmd_exe


def check_workshop_dir(workshop_dir):
    """Check if workshop directory exists and is valid."""
    workshop_path = Path(workshop_dir)
    if not workshop_path.exists():
        print(f"[ERROR] Workshop directory not found: {workshop_path}")
        return False

    # Check for addoninfo.txt or similar workshop metadata
    metadata_files = list(workshop_path.glob("addoninfo.txt")) + \
                    list(workshop_path.glob("info.vdf")) + \
                    list(workshop_path.glob("*.vdf"))
    if not metadata_files:
        print(f"[WARNING] No workshop metadata found in: {workshop_path}")
        print("Make sure this is a valid workshop addon directory.")

    return True


def upload_to_workshop(steamcmd_exe, workshop_dir, steam_user, steam_password):
    """Upload workshop addon using SteamCMD."""
    print("=" * 60)
    print("  Upload to Steam Workshop via SteamCMD")
    print("=" * 60)
    print(f"  Workshop dir: {workshop_dir}")
    print(f"  Steam user:  {steam_user}")
    print()

    # Build SteamCMD command
    cmd = [
        str(steamcmd_exe),
        "+login", steam_user,
    ]

    # Add password if provided
    if steam_password:
        cmd.extend([steam_password])

    # Add upload command
    cmd.extend([
        "+workshop_build_item", str(workshop_dir),
        "+quit"
    ])

    print(f"  Running SteamCMD...")
    print(f"  Command: {' '.join(cmd[:3])} [credentials hidden] ...")
    print()

    try:
        result = subprocess.run(
            cmd,
            cwd=steamcmd_exe.parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=600,  # 10 minutes timeout
        )

        output = result.stdout or ""

        # Print output (filter sensitive info)
        for line in output.split("\n"):
            # Skip lines with password or sensitive info
            if "password" in line.lower() or "login" in line.lower():
                print(f"  [SteamCMD] {line[:50]}...")
            else:
                print(f"  [SteamCMD] {line}")

        # Check for success indicators
        if "Success" in output or "Published" in output or "Uploaded" in output:
            print()
            print("  Upload successful!")
            return True
        elif "Error" in output or "Failed" in output:
            print()
            print("[ERROR] Upload failed. Check SteamCMD output above.")
            return False
        else:
            print()
            print("[WARNING] Upload status unclear. Check SteamCMD output above.")
            return True  # Assume success if no explicit error

    except subprocess.TimeoutExpired:
        print("[ERROR] SteamCMD timed out after 10 minutes")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to run SteamCMD: {e}")
        return False


def main():
    args = parse_args()

    print("=" * 60)
    print("  Steam Workshop Uploader")
    print("=" * 60)
    print()

    # Check SteamCMD
    steamcmd_exe = check_steamcmd(args.steamcmd_dir)
    if not steamcmd_exe:
        sys.exit(1)

    # Check workshop directory
    if not check_workshop_dir(args.workshop_dir):
        sys.exit(1)

    # Upload
    success = upload_to_workshop(
        steamcmd_exe,
        args.workshop_dir,
        args.steam_user,
        args.steam_password
    )

    print()
    print("=" * 60)
    if success:
        print("  Done!")
    else:
        print("  Failed!")
    print("=" * 60)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
