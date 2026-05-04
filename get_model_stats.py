# /// script
# requires-python = ">=3.10"
# dependencies = ["trimesh", "tqdm"]
# ///

"""
Get vertex and triangle count from compiled .vmdl_c files.
Requires Source2Viewer-CLI.exe in Source2Viewer-cli directory.

Usage:
    uv run get_model_stats.py
    uv run get_model_stats.py --model-dir "F:\\CS2-ModelBuilder\\compiled\\agents\\models"
    uv run get_model_stats.py --cli-path "F:\\CS2-ModelBuilder\\Source2Viewer-cli\\Source2Viewer-CLI.exe"
"""

import argparse
import subprocess
import sys
import os
import csv
from pathlib import Path
from typing import Dict, List

# ============================================================
# Configuration
# ============================================================
DEFAULT_MODEL_DIR = r"F:\CS2-ModelBuilder\compiled\agents\models"
CLI_PATH = Path(__file__).parent / "Source2Viewer-cli" / "Source2Viewer-CLI.exe"


def parse_args():
    parser = argparse.ArgumentParser(description="Get model vertex/triangle stats")
    parser.add_argument(
        "--model-dir",
        default=DEFAULT_MODEL_DIR,
        help=f"Directory containing compiled models (default: {DEFAULT_MODEL_DIR})",
    )
    parser.add_argument(
        "--cli-path",
        default=str(CLI_PATH),
        help=f"Path to Source2Viewer-CLI.exe (default: {CLI_PATH})",
    )
    return parser.parse_args()


def export_to_glb(vmdl_c_path: Path, cli_path: str) -> tuple:
    """Export .vmdl_c to GLB using Source2Viewer-CLI."""
    output_glb = vmdl_c_path.with_suffix(".glb")
    temp_dir = vmdl_c_path.parent

    try:
        cmd = [
            cli_path,
            "-i", str(vmdl_c_path),
            "-o", str(output_glb),
            "--gltf_export_format", "glb",
            "-d",  # -d is a flag, not followed by path
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=90,
            encoding="utf-8",
            errors="replace"
        )

        if output_glb.exists() and output_glb.stat().st_size > 1000:
            return True, output_glb, ""
        else:
            stderr_msg = result.stderr.strip() if result.stderr else "No stderr output"
            stdout_msg = result.stdout.strip() if result.stdout else "No stdout output"
            return False, None, f"Export failed - stderr: {stderr_msg[:150]} | stdout: {stdout_msg[:150]}"

    except subprocess.TimeoutExpired:
        return False, None, "Export timeout (90s)"
    except Exception as e:
        return False, None, str(e)


def get_model_stats(glb_path: Path, model_dir: Path) -> Dict:
    """Get vertex and triangle count from GLB file using trimesh."""
    try:
        import trimesh
        scene = trimesh.load(str(glb_path), force='scene')

        total_tris = 0
        total_verts = 0
        mesh_count = 0

        for name, mesh in scene.geometry.items():
            if hasattr(mesh, 'faces'):
                total_tris += len(mesh.faces)
                total_verts += len(mesh.vertices)
                mesh_count += 1

        # Clean up
        if glb_path.exists():
            glb_path.unlink()

        # Get folder size and file count
        folder_size_mb = 0
        file_count = 0
        if model_dir.exists():
            for f in model_dir.rglob("*"):
                if f.is_file():
                    folder_size_mb += f.stat().st_size
                    file_count += 1
            folder_size_mb = round(folder_size_mb / (1024 * 1024), 2)

        return {
            "filename": glb_path.stem.replace(".vmdl", "").replace(".vmdl_c", ""),
            "meshes": mesh_count,
            "triangles": total_tris,
            "vertices": total_verts,
            "folder_size_mb": folder_size_mb,
            "file_count": file_count,
            "status": "Success"
        }

    except Exception as e:
        return {
            "filename": glb_path.stem.replace(".vmdl", ""),
            "meshes": 0,
            "triangles": 0,
            "vertices": 0,
            "folder_size_mb": 0,
            "file_count": 0,
            "status": f"Error: {str(e)[:100]}"
        }


def main():
    args = parse_args()
    model_dir = Path(args.model_dir)
    cli_path = args.cli_path

    if not model_dir.exists():
        print(f"[ERROR] Model directory not found: {model_dir}")
        sys.exit(1)

    if not Path(cli_path).exists():
        print(f"[ERROR] Source2Viewer-CLI.exe not found at: {cli_path}")
        print("Please download from: https://github.com/ValveResourceFormat/Source2Viewer")
        print(f"Place Source2Viewer-CLI.exe in: {Path(__file__).parent / 'Source2Viewer-cli'}\\")
        sys.exit(1)

    print("=" * 60)
    print("  Get Model Vertex/Triangle Stats")
    print("=" * 60)
    print(f"  Model dir: {model_dir}")
    print(f"  CLI:      {cli_path}")
    print()

    # Find all .vmdl_c files
    vmdl_c_files = sorted(model_dir.rglob("*.vmdl_c"))
    # Filter only model files (not materials)
    vmdl_c_files = [f for f in vmdl_c_files if f.stem.replace(".vmdl", "") and "_" not in f.stem]

    if not vmdl_c_files:
        print("[WARNING] No .vmdl_c files found")
        sys.exit(0)

    print(f"  Found {len(vmdl_c_files)} compiled models")
    print()

    results = []
    for i, vmdl_c in enumerate(vmdl_c_files, 1):
        model_name = vmdl_c.stem.replace(".vmdl_c", "").replace(".vmdl", "")
        print(f"  [{i}/{len(vmdl_c_files)}] Processing: {vmdl_c.relative_to(model_dir)}...")

        # Export to GLB
        success, glb_path, error = export_to_glb(vmdl_c, cli_path)

        if not success:
            print(f"    ERROR: {error[:80]}")
            results.append({
                "filename": model_name,
                "meshes": 0,
                "triangles": 0,
                "vertices": 0,
                "folder_size_mb": 0,
                "file_count": 0,
                "status": error
            })
            continue

        # Get stats
        vmdl_c_dir = vmdl_c.parent
        stats = get_model_stats(glb_path, vmdl_c_dir)
        results.append(stats)

        if stats['status'] == "Success":
            print(f"    Meshes: {stats['meshes']}, Tris: {stats['triangles']:,}, Verts: {stats['vertices']:,}")
        else:
            print(f"    ERROR: {stats['status'][:80]}")

    # Save to CSV
    output_csv = model_dir.parent.parent / "model_stats.csv"
    if results:
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["filename", "meshes", "triangles", "vertices", "folder_size_mb", "file_count", "status"])
            writer.writeheader()
            writer.writerows(results)

        print()
        print("=" * 60)
        print(f"  Saved to: {output_csv}")
    else:
        print()
        print("[WARNING] No results to save")

    print("=" * 60)
    print("  Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
