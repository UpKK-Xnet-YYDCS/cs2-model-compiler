# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""
Source 2 Model Compiler for CS2
Compiles .vmdl files using resourcecompiler.exe

Usage::

    uv run compile_models.py
    uv run compile_models.py --cs2-dir "F:/SteamLibrary/steamapps/common/Counter-Strike Global Offensive"
    uv run compile_models.py --source-dir "F:/models" --output-dir "C:/compiled"
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

# ============================================================
# DEFAULT CONFIGURATION
# Change these or override via command-line arguments
# ============================================================
DEFAULT_CS2_DIR = r"F:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive"
DEFAULT_SOURCE_DIR = os.path.join(os.getcwd())
DEFAULT_OUTPUT_DIR = os.path.join(os.getcwd(), "compiled")
# ============================================================


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Source 2 Model Compiler for CS2")
    parser.add_argument(
        "--cs2-dir",
        default=DEFAULT_CS2_DIR,
        help=f"Path to CS2 game directory (default: {DEFAULT_CS2_DIR})",
    )
    parser.add_argument(
        "--source-dir",
        default=DEFAULT_SOURCE_DIR,
        help=f"Path to source models folder containing agents/ (default: {DEFAULT_SOURCE_DIR})",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Path to output compiled files (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--models-folder",
        default="agents",
        help="Subfolder name under source-dir containing models (default: agents)",
    )
    return parser.parse_args()


def find_resourcecompiler(cs2_dir):
    """Find resourcecompiler.exe in CS2 installation."""
    compiler = Path(cs2_dir) / "game" / "bin" / "win64" / "resourcecompiler.exe"
    if not compiler.exists():
        print(f"[ERROR] resourcecompiler.exe not found at: {compiler}")
        return None
    return compiler


def get_content_dir(cs2_dir):
    """Get CS2 content directory."""
    return Path(cs2_dir) / "content" / "csgo"


def get_game_dir(cs2_dir):
    """Get CS2 game directory."""
    return Path(cs2_dir) / "game" / "csgo"


def copy_to_content(source_dir, content_dir, models_folder):
    """Copy source models to CS2 content directory under <models_folder>/models/."""
    print(f"\n[1/5] Copying source files to content directory...")

    # Clean previous source copy
    dest_models = content_dir / models_folder
    if dest_models.exists():
        shutil.rmtree(dest_models)

    # Copy models folder from source
    src_models = Path(source_dir) / models_folder
    if not src_models.exists():
        print(f"[ERROR] {models_folder} folder not found in {source_dir}")
        return False

    shutil.copytree(src_models, dest_models)
    print(f"  Copied {src_models} -> {dest_models}")
    return True


def fix_vmdl_files(content_dir, models_folder):
    """Fix common issues in .vmdl files."""
    print(f"\n[2/5] Fixing .vmdl files...")

    vmdl_files = list(content_dir.glob(f"{models_folder}/**/*.vmdl"))
    fixed_count = 0

    for vmdl in vmdl_files:
        content = vmdl.read_text(encoding="utf-8")
        original = content

        # Remove tools_preview AnimFile blocks (common missing dependency)
        pattern = r'\s*{\s*_class\s*=\s*"AnimFile"\s*name\s*=\s*"tools_preview"[^}]*},\s*'
        content = re.sub(pattern, "", content)

        # Remove source_filename reference for tools_preview
        pattern2 = r'source_filename\s*=\s*"agents/models/s2ze/master_chief/_dmx/anims/tools_preview\.dmx"'
        content = re.sub(pattern2, 'source_filename = ""', content)

        if content != original:
            vmdl.write_text(content, encoding="utf-8")
            fixed_count += 1
            print(f"  Fixed: {vmdl.name}")

    print(f"  Fixed {fixed_count}/{len(vmdl_files)} files")
    return True


def copy_textures_to_characters(content_dir, models_folder):
    """
    Copy textures from <models_folder>/models/<author>/<model>/materials to characters/models/<author>/<model>/materials.
    Some models reference textures in characters/models/ path.
    """
    print("\n[3/5] Copying textures to expected paths...")

    models_dir = content_dir / models_folder / "models"
    if not models_dir.exists():
        print(f"  No {models_folder}/models found, skipping")
        return True

    copied = 0
    for author_folder in models_dir.iterdir():
        if not author_folder.is_dir():
            continue

        for model_folder in author_folder.iterdir():
            if not model_folder.is_dir():
                continue

            mat_src = model_folder / "materials"
            if not mat_src.exists():
                continue

            mat_dest = content_dir / "characters" / "models" / author_folder.name / model_folder.name / "materials"
            mat_dest.mkdir(parents=True, exist_ok=True)
            for item in mat_src.iterdir():
                dest_item = mat_dest / item.name
                if item.is_dir():
                    shutil.copytree(item, dest_item, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest_item)
            copied += 1

    print(f"  Copied textures for {copied} model folders")
    return True


def compile_models(compiler, content_dir, game_info_path, models_folder, cs2_dir, output_dir):
    """Compile all .vmdl files using resourcecompiler.exe.
    Returns: (failures, success_count, failed_count, skipped_count, build_times)
    build_times is a dict: {model_name: {'time': build_time_str, 'duration': duration_seconds}}
    """
    print("\n[4/5] Compiling models...")

    vmdl_files = list(content_dir.glob(f"{models_folder}/**/*.vmdl"))
    if not vmdl_files:
        print("  No .vmdl files found!")
        return {}, 0, 0, 0, {}

    print(f"  Found {len(vmdl_files)} models to compile\n")

    failures = {}
    success_count = 0
    failed_count = 0
    skipped_count = 0
    build_times = {}  # {model_name: {'time': build_time_str, 'duration': duration_seconds}}

    game_models_dir = get_game_dir(cs2_dir) / models_folder / "models"

    for i, vmdl in enumerate(vmdl_files, 1):
        rel_path = vmdl.relative_to(content_dir)
        model_name = vmdl.stem
        # rel_path is like "agents\models\upkk\curren_chan\curren_chan.vmdl"
        # We need the path relative to "agents\models" for the game directory
        rel_to_models = rel_path.relative_to(f"{models_folder}/models")
        compiled_path = game_models_dir / rel_to_models.with_suffix(".vmdl_c")
        game_model_dir = game_models_dir / rel_to_models.parent

        # Force recompilation by touching the source file
        vmdl.touch()
        time.sleep(0.2)

        print(f"  [{i}/{len(vmdl_files)}] Compiling: {rel_path}")

        # Start timing
        start_time = time.time()
        build_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

        result = subprocess.run(
            [
                str(compiler),
                "-game", str(game_info_path),
                str(rel_path),
            ],
            cwd=content_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=300,
            encoding="utf-8",
            errors="replace",
        )

        output = result.stdout or ""

        # Calculate duration
        end_time = time.time()
        duration = round(end_time - start_time, 2)

        # Store build time and duration for this model
        build_times[model_name] = {'time': build_time_str, 'duration': duration}

        # Wait for file to be flushed
        time.sleep(0.5)

        # Extract error lines - only real error lines, not summary stats
        error_lines = [line.strip() for line in output.split("\n") if "RESOURCE COMPILE ERROR" in line]
        if not error_lines:
            # Lines that start with ERROR: but not summary lines like "ERROR: 0 compiled"
            error_lines = [
                line.strip() for line in output.split("\n")
                if line.strip().startswith("ERROR:") and not re.search(r"ERROR:\s*\d+\s*compiled", line.strip())
            ]

        # Check for actual fatal errors (not summary lines)
        fatal_errors = [
            line.strip() for line in output.split("\n")
            if ("FATAL ERROR" in line or "ERROR:" in line)
            and not re.search(r"ERROR:\s*\d+\s*compiled", line.strip())
        ]

        # Check if compiled file was created (primary success indicator)
        if compiled_path.exists():
            print(f"    SUCCESS")
            success_count += 1
        elif error_lines or fatal_errors:
            # Combine all error lines
            all_errors = error_lines + fatal_errors
            error_reason = "\n".join(all_errors)
            model_path = f"{models_folder}/models/{str(rel_to_models.parent).replace(chr(92), '/')}/{model_name}.vmdl"
            failures[model_path] = error_reason
            failed_count += 1
            print(f"    FAILED: {all_errors[0][:120]}")

            # Delete failed compiled files only (not the source folder)
            try:
                # Delete compiled files in game model directory
                if game_model_dir.exists():
                    for item in game_model_dir.rglob("*_c"):
                        item.unlink()
                        print(f"    Deleted: {item.name}")
                # Also delete from output directory
                output_model_dir = Path(output_dir) / models_folder / "models" / rel_to_models.parent
                if output_model_dir.exists():
                    for item in output_model_dir.rglob("*_c"):
                        item.unlink()
                    print(f"    Cleaned output: {output_model_dir}")
            except Exception as e:
                print(f"    WARNING: Could not clean failed files: {e}")

            # Read detailed error from log if available
            try:
                # Try to find resourcecompiler log
                log_dir = Path(cs2_dir) / "game" / "bin" / "win64" / "logs"
                if log_dir.exists():
                    recent_logs = sorted(log_dir.glob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True)
                    if recent_logs:
                        log_content = recent_logs[0].read_text(encoding="utf-8", errors="ignore")
                        # Extract relevant error section
                        lines = log_content.split("\n")
                        error_section = []
                        capture = False
                        for line in lines:
                            if "ERROR" in line or "FATAL" in line:
                                capture = True
                            if capture and len(error_section) < 10:
                                error_section.append(line.strip())
                            if len(error_section) >= 10:
                                break
                        if error_section:
                            enhanced_error = "\n".join(error_section)
                            # Update failure reason
                            failures[model_path] = enhanced_error
                            error_reason = enhanced_error
            except Exception as e:
                print(f"    WARNING: Could not enhance error message: {e}")
        else:
            # Check game directory for compiled files (may exist from previous runs)
            if game_model_dir.exists() and any(game_model_dir.rglob("*_c")):
                print(f"    SUCCESS (from cache)")
                success_count += 1
            else:
                skipped_count += 1
                print(f"    SKIPPED")

    print(f"\n  Summary: {success_count} compiled, {failed_count} failed, {skipped_count} skipped")
    return failures, success_count, failed_count, skipped_count, build_times


def collect_compiled(content_dir, game_dir, output_dir, source_dir, models_folder, failures):
    """Collect compiled files from game directory and copy to output, preserving agents/models/ structure.
    Also writes compile_failed.txt for each failed model.
    """
    print("\n[5/5] Collecting compiled files...")

    # Clean output directory
    out_path = Path(output_dir)
    if out_path.exists():
        for retry in range(3):
            try:
                shutil.rmtree(out_path)
                break
            except PermissionError:
                time.sleep(0.5)
        else:
            print("  WARNING: Could not clean output directory, appending to existing")
    out_path.mkdir(parents=True, exist_ok=True)

    # Source models structure
    src_models = Path(source_dir) / models_folder / "models"
    if not src_models.exists():
        print("  No source models found")
        return False

    collected = 0
    game_models = game_dir / models_folder / "models"

    if not game_models.exists():
        print("  No compiled models in game directory")
        return False

    # Preserve models/<author>/<model>/... structure
    for compiled_file in game_models.rglob("*_c"):
        rel_path = compiled_file.relative_to(game_models)
        dest = out_path / models_folder / "models" / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(compiled_file, dest)
        collected += 1

    # Write compile_failed.txt for each failed model directory
    failure_count = 0
    dir_failures = {}
    for model_rel_path, error_reason in failures.items():
        # model_rel_path is like "agents/models/upkk/origami_v2/origami_v2.vmdl"
        model_dir = str(Path(model_rel_path).parent).replace(chr(92), "/")
        model_name = Path(model_rel_path).name
        if model_dir not in dir_failures:
            dir_failures[model_dir] = []
        dir_failures[model_dir].append((model_name, error_reason))

    for model_dir, model_errors in dir_failures.items():
        failed_dir = out_path / model_dir.replace("/", "\\")
        failed_dir.mkdir(parents=True, exist_ok=True)

        failed_file = failed_dir / "compile_failed.txt"
        content_lines = [f"Compilation failures in: {model_dir}", "=" * 50, ""]
        for model_name, error_reason in model_errors:
            content_lines.append(f"File: {model_name}")
            content_lines.append(f"Error:")
            content_lines.append(error_reason)
            content_lines.append("")

        failed_file.write_text("\n".join(content_lines), encoding="utf-8")
        failure_count += 1
        print(f"  Wrote failure log: {failed_file}")

    print(f"  Collected {collected} compiled files to {output_dir}")
    if failure_count > 0:
        print(f"  Wrote {failure_count} compile_failed.txt files")
    return collected > 0


def get_toolchain_version(cs2_dir):
    """Get CS2 toolchain version from steam.inf."""
    steam_inf = Path(cs2_dir) / "game" / "csgo" / "steam.inf"
    if steam_inf.exists():
        try:
            content = steam_inf.read_text(encoding="utf-8", errors="ignore")
            version_info = {}
            for line in content.split("\n"):
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    version_info[key] = value

            client_ver = version_info.get("ClientVersion", "Unknown")
            patch_ver = version_info.get("PatchVersion", "Unknown")
            version_date = version_info.get("VersionDate", "")
            version_time = version_info.get("VersionTime", "")

            return f"Client {client_ver}, Patch {patch_ver} ({version_date} {version_time})"
        except Exception as e:
            return f"Unknown (error: {str(e)[:50]})"
    return "Unknown (steam.inf not found)"


def generate_build_stats(content_dir, output_dir, models_folder, failures, success_count, failed_count, skipped_count, cs2_dir, build_times=None):
    """Generate BuildStats.md with compilation results.
    build_times: dict {model_name: {'time': str, 'duration': float}}
    """
    print("\n[7/7] Generating BuildStats.md...")

    output_path = Path(output_dir)
    stats_file = output_path / "BuildStats.md"

    toolchain_version = get_toolchain_version(cs2_dir)

    # Read model stats CSV if exists
    model_stats = []
    model_stats_csv = output_path / "model_stats.csv"
    if model_stats_csv.exists():
        try:
            import csv
            with open(model_stats_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('status') == 'Success':
                        model_stats.append(row)
            print(f"  Loaded model stats: {len(model_stats)} models")
        except Exception as e:
            print(f"  WARNING: Failed to read model stats CSV: {e}")

    # Collect all model directories and files
    models_dir = content_dir / models_folder / "models"
    model_entries = []

    # Build a dict of failed models: {model_name: error_reason}
    failed_dict = {}
    for key, value in failures.items():
        # Extract model name from path like "agents/models/upkk/curren_chan/curren_chan.vmdl"
        parts = key.replace("\\", "/").split("/")
        if len(parts) >= 2:
            model_name = parts[-1].replace(".vmdl", "")
            failed_dict[model_name] = value

    # Build set of successfully compiled models from output directory
    # Check if .vmdl_c file exists for each model
    compiled_models = set()
    compiled_model_dirs = set()  # Store (author, model_dir, model_name) tuples
    output_models_dir = output_path / models_folder / "models"
    if output_models_dir.exists():
        for author_dir in output_models_dir.iterdir():
            if not author_dir.is_dir():
                continue
            for model_dir in author_dir.iterdir():
                if not model_dir.is_dir():
                    continue
                # Check all .vmdl_c files in this directory
                vmdl_c_files = list(model_dir.glob("*.vmdl_c"))
                for vcf in vmdl_c_files:
                    # vcf is like "curren_chan.vmdl_c" or "curren_chan_nohitbox.vmdl_c"
                    model_name = vcf.stem.replace(".vmdl", "")  # Remove .vmdl_c -> .vmdl -> name
                    compiled_models.add(model_name)
                    compiled_model_dirs.add((author_dir.name, model_dir.name, model_name))

    if models_dir.exists():
        for author_folder in models_dir.iterdir():
            if not author_folder.is_dir():
                continue
            for model_folder in author_folder.iterdir():
                if not model_folder.is_dir():
                    continue

                vmdl_files = list(model_folder.glob("*.vmdl"))
                for vmdl in vmdl_files:
                    model_name = vmdl.stem

                    # Check compilation status
                    if model_name in failed_dict:
                        status = "FAIL"
                        reason = failed_dict[model_name].split("\n")[0][:100]
                    elif model_name in compiled_models:
                        status = "OK"
                        reason = "-"
                    else:
                        # Double-check: see if the compiled file exists in output
                        vmdl_c_in_output = output_models_dir / author_folder.name / model_folder.name / f"{model_name}.vmdl_c"
                        if vmdl_c_in_output.exists():
                            status = "OK"
                            reason = "-"
                        else:
                            status = "SKIP"
                            reason = "No compiled output"

                    # Get build time info
                    build_time_info = build_times.get(model_name, {'time': '-', 'duration': '-'})
                    build_time = build_time_info['time']
                    duration = build_time_info['duration']

                    # Path from agents/ onwards
                    model_path = f"agents/models/{author_folder.name}/{model_folder.name}/{vmdl.stem}"
                    if vmdl.name.endswith('.vmdl'):
                        display_file = f"{model_path}.vmdl"
                    else:
                        display_file = vmdl.name

                    model_entries.append({
                        "directory": f"agents/models/{author_folder.name}/{model_folder.name}",
                        "file": display_file,
                        "status": status,
                        "build_time": build_time,
                        "duration": f"{duration}s" if isinstance(duration, (int, float)) else '-',
                        "reason": reason
                    })

        # Also add failed models that might not be in model_entries yet
        for model_path, error in failures.items():
            # Check if already added
            if not any((me['file'].endswith('.vmdl') and model_path.endswith(me['file'].replace('.vmdl', ''))) for me in model_entries):
                # Extract directory and file from model_path
                # model_path like "agents/models/upkk/origami_v2/origami_v2.vmdl"
                parts = model_path.replace("\\", "/").split("/")
                if len(parts) >= 4:
                    directory = "/".join(parts[:4])  # agents/models/upkk/origami_v2
                    file = parts[-1]
                else:
                    directory = "unknown"
                    file = parts[-1] if parts else "unknown"

                model_name = file.replace(".vmdl", "")
                build_time_info = build_times.get(model_name, {'time': '-', 'duration': '-'})
                model_entries.append({
                    "directory": directory,
                    "file": file,
                    "status": "FAIL",
                    "build_time": build_time_info['time'],
                    "duration": f"{build_time_info['duration']}s" if isinstance(build_time_info['duration'], (int, float)) else '-',
                    "reason": error[:100]
                })

    # Generate markdown
    lines = []
    lines.append("# Build Stats")
    lines.append("")
    lines.append(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Toolchain Version:** {toolchain_version}")
    lines.append(f"**CS2 Directory:** {cs2_dir}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Success:** {success_count}")
    lines.append(f"- **Failed:** {failed_count}")
    lines.append(f"- **Skipped:** {skipped_count}")
    lines.append(f"- **Total:** {len(model_entries)}")
    lines.append("")
    lines.append("## Model Compilation Results")
    lines.append("")
    lines.append("| Directory | File | Status | Build Time | Duration | Failure Reason |")
    lines.append("|-----------|------|--------|-----------|----------|----------------|")
    lines.append("")
    
    for entry in sorted(model_entries, key=lambda x: (x["directory"], x["file"])):
        lines.append(f"| {entry['directory']} | {entry['file']} | {entry['status']} | {entry.get('build_time', '-')} | {entry.get('duration', '-')} | {entry['reason']} |")

    lines.append("")
    lines.append("## Failed Models Details")
    lines.append("")

    if failures:
        for model_path, error in failures.items():
            lines.append(f"### {model_path}")
            lines.append("```")
            lines.append(error[:500])
            lines.append("```")
            lines.append("")
    else:
        lines.append("No failures.")
        lines.append("")

    # Add model stats table if available
    if model_stats:
        lines.append("")
        lines.append("## Model Statistics (Vertex/Triangle Count)")
        lines.append("")
        lines.append("| Model | Meshes | Triangles | Vertices | Folder Size (MB) | Files |")
        lines.append("|-------|--------|-----------|----------|------------------|-------|")

        for stat in sorted(model_stats, key=lambda x: x.get('filename', '')):
            filename = stat.get('filename', '-')
            meshes = stat.get('meshes', 0)
            triangles = stat.get('triangles', 0)
            vertices = stat.get('vertices', 0)
            folder_size = stat.get('folder_size_mb', 0)
            file_count = stat.get('file_count', 0)

            lines.append(f"| {filename} | {meshes} | {triangles:,} | {vertices:,} | {folder_size} | {file_count} |")

        lines.append("")

    stats_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Generated: {stats_file}")
    return True


def main():
    args = parse_args()

    cs2_dir = Path(args.cs2_dir)
    source_dir = Path(args.source_dir)
    output_dir = Path(args.output_dir)
    models_folder = args.models_folder

    print("=" * 60)
    print("  Source 2 Model Compiler for CS2")
    print("=" * 60)
    print(f"  CS2:       {cs2_dir}")
    print(f"  Source:    {source_dir}")
    print(f"  Output:    {output_dir}")
    print(f"  Models:    {models_folder}")
    print()

    if not cs2_dir.exists():
        print(f"[ERROR] CS2 directory not found: {cs2_dir}")
        sys.exit(1)

    # Find compiler
    compiler = find_resourcecompiler(cs2_dir)
    if not compiler:
        sys.exit(1)
    print(f"  Compiler: {compiler}")

    content_dir = get_content_dir(cs2_dir)
    game_info_path = get_game_dir(cs2_dir)  # path to gameinfo.gi
    game_dir_cs2 = get_game_dir(cs2_dir)

    # Step 1: Copy to content
    if not copy_to_content(source_dir, content_dir, models_folder):
        sys.exit(1)

    # Step 2: Fix vmdl files
    if not fix_vmdl_files(content_dir, models_folder):
        sys.exit(1)

    # Step 3: Copy textures
    if not copy_textures_to_characters(content_dir, models_folder):
        sys.exit(1)

    # Step 4: Compile
    failures, success_count, failed_count, skipped_count, build_times = compile_models(compiler, content_dir, game_info_path, models_folder, cs2_dir, output_dir)

    # Step 5: Collect
    if not collect_compiled(content_dir, game_dir_cs2, output_dir, source_dir, models_folder, failures):
        print("\n[WARNING] No compiled files collected. Check errors above.")

    # Step 6: Generate model stats (vertex/triangle count)
    print("\n[6/7] Generating model stats...")
    try:
        subprocess.run(
            ["uv", "run", "python", "get_model_stats.py", "--model-dir", str(output_dir / models_folder / "models"),
             "--cli-path", str(Path(__file__).parent / "Source2Viewer-cli" / "Source2Viewer-CLI.exe")],
            cwd=Path(__file__).parent,
            check=True,
            timeout=300,
        )
    except Exception as e:
        print(f"  WARNING: Failed to generate model stats: {e}")

    # Step 7: Generate BuildStats.md
    generate_build_stats(content_dir, output_dir, models_folder, failures, success_count, failed_count, skipped_count, cs2_dir, build_times)

    print("\n" + "=" * 60)
    print("  Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
