from __future__ import annotations

import argparse
from pathlib import Path

from .conversion import convert


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert a texture folder to validated TX files")
    parser.add_argument("textures", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--ocio")
    parser.add_argument(
        "--output-space",
        help="Override OCIO's scene_linear role (normally leave this unset)",
    )
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--no-inspect", action="store_true")
    parser.add_argument(
        "--skip-png-jpeg-linearization", action="store_true",
        help=(
            "Advanced override: preserve recognized PNG/JPEG color-map values "
            "without converting them to OCIO scene-linear"
        ),
    )
    args = parser.parse_args(argv)
    manifest = convert(
        args.textures, args.output, args.ocio, args.output_space, args.force,
        not args.no_inspect, args.skip_png_jpeg_linearization,
    )
    print(manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
