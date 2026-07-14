"""List all .vmdl files under agents and write their relative paths to a text file."""

import argparse
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_SOURCE_DIR = BASE_DIR / "agents"
DEFAULT_OUTPUT_FILE = BASE_DIR / "vmdl_paths.txt"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write all .vmdl paths under agents to a text file."
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=DEFAULT_SOURCE_DIR,
        help=f"Directory to scan (default: {DEFAULT_SOURCE_DIR})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
        help=f"Output text file (default: {DEFAULT_OUTPUT_FILE})",
    )
    return parser.parse_args()


def list_vmdl_paths(source_dir: Path) -> list[str]:
    source_dir = source_dir.resolve()
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Source directory does not exist: {source_dir}")

    # Make every entry start with the source directory name, e.g.
    # agents/models/upkk/example/example.vmdl.
    relative_root = source_dir.parent
    return sorted(
        (path.relative_to(relative_root).as_posix() for path in source_dir.rglob("*.vmdl")),
        key=str.casefold,
    )


def main() -> int:
    args = parse_args()

    try:
        paths = list_vmdl_paths(args.source_dir)
    except FileNotFoundError as error:
        print(error)
        return 1

    output_file = args.output.resolve()
    output_file.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(paths)
    if content:
        content += "\n"
    output_file.write_text(content, encoding="utf-8")

    print(f"Wrote {len(paths)} .vmdl paths to {output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
