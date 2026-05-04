# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""
Upload compiled models to CS2 workshop addon directory.
Copies compiled models from output directory to workshop addon folder.

Usage:
    uv run upload_to_workshop.py
    uv run upload_to_workshop.py --workshop-dir "F:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive\game\csgo_addons\upkkmodelpack2026_agents"
    uv run upload_to_workshop.py --compiled-dir "F:\CS2-ModelBuilder\compiled"
"""

import argparse
import shutil
import sys
from pathlib import Path
from time import sleep

# ============================================================
# DEFAULT CONFIGURATION
# ============================================================
DEFAULT_COMPILED_DIR = r"F:\CS2-ModelBuilder\compiled"
DEFAULT_WORKSHOP_DIR = r"F:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive\game\csgo_addons\upkkmodelpack2026_agents"
DEFAULT_MODELS_FOLDER = "agents"


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Upload compiled models to CS2 workshop addon")
    parser.add_argument(
        "--compiled-dir",
        default=DEFAULT_COMPILED_DIR,
        help=f"Path to compiled files directory (default: {DEFAULT_COMPILED_DIR})",
    )
    parser.add_argument(
        "--workshop-dir",
        default=DEFAULT_WORKSHOP_DIR,
        help=f"Path to workshop addon directory (default: {DEFAULT_WORKSHOP_DIR})",
    )
    parser.add_argument(
        "--models-folder",
        default=DEFAULT_MODELS_FOLDER,
        help="Subfolder name under compiled directory (default: agents)",
    )
    return parser.parse_args()


def upload_to_workshop(compiled_dir, workshop_dir, models_folder):
    """Upload compiled models to workshop addon directory."""
    compiled_path = Path(compiled_dir)
    workshop_path = Path(workshop_dir)

    print("=" * 60)
    print("  Upload Compiled Models to Workshop")
    print("=" * 60)
    print(f"  Compiled: {compiled_path}")
    print(f"  Workshop: {workshop_path}")
    print()

    if not compiled_path.exists():
        print(f"[ERROR] Compiled directory not found: {compiled_path}")
        return False

    if not workshop_path.exists():
        print(f"[ERROR] Workshop directory not found: {workshop_path}")
        return False

    # Source: compiled/agents/models/*
    src_models = compiled_path / models_folder / "models"
    if not src_models.exists():
        print(f"[ERROR] No models found in: {src_models}")
        return False

    # Destination: workshop_addon/agents/models/*
    dest_models = workshop_path / models_folder / "models"
    dest_models.mkdir(parents=True, exist_ok=True)

    print(f"  Copying from: {src_models}")
    print(f"  Copying to:   {dest_models}")
    print()

    copied = 0
    for model_dir in src_models.iterdir():
        if not model_dir.is_dir():
            continue

        dest_dir = dest_models / model_dir.name

        # Remove existing directory
        if dest_dir.exists():
            try:
                shutil.rmtree(dest_dir)
            except PermissionError:
                sleep(0.5)
                shutil.rmtree(dest_dir, ignore_errors=True)

        # Copy directory
        try:
            shutil.copytree(model_dir, dest_dir)
            print(f"  Copied: {model_dir.name}")
            copied += 1
        except Exception as e:
            print(f"  ERROR copying {model_dir.name}: {e}")

    print()
    print(f"  Successfully copied {copied} model directories to workshop")
    print("=" * 60)
    return True


def main():
    args = parse_args()

    success = upload_to_workshop(
        args.compiled_dir,
        args.workshop_dir,
        args.models_folder
    )

    if not success:
        sys.exit(1)

    print("\n  Done!")


if __name__ == "__main__":
    main()
