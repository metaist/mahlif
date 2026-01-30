"""Main CLI for mahlif.

Usage:
    mahlif convert <src> <dest>     # Convert between formats
    mahlif stats <file>             # Show score statistics
    mahlif sibelius install         # Install Sibelius plugins
    mahlif sibelius build           # Build Sibelius plugins
    mahlif sibelius check           # Lint ManuScript files
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def detect_format(path: Path) -> str | None:
    """Detect format from file extension.

    Args:
        path: File path

    Returns:
        Format name or None if unknown

    Supported formats:
        .mahlif.xml, .mahlif -> mahlif
        .plg -> sibelius
        .ly -> lilypond
        .musicxml, .mxl -> musicxml
        .pdf -> pdf (via lilypond)
    """
    name = path.name.lower()

    if name.endswith(".mahlif.xml") or name.endswith(".mahlif"):
        return "mahlif"
    elif name.endswith(".plg"):
        return "sibelius"
    elif name.endswith(".ly"):
        return "lilypond"
    elif name.endswith(".musicxml") or name.endswith(".mxl"):
        return "musicxml"
    elif name.endswith(".pdf"):
        return "pdf"

    return None


def cmd_convert(args: argparse.Namespace) -> int:
    """Run convert command.

    Args:
        args: Parsed arguments

    Returns:
        Exit code (0 for success)
    """
    src = Path(args.src)
    dest = Path(args.dest)

    if not src.exists():
        print(f"Error: {src} not found")
        return 1

    src_format = args.from_format or detect_format(src)
    dest_format = args.to_format or detect_format(dest)

    if src_format is None:
        print(f"Error: Cannot detect format for {src}")
        print("Use --from to specify the source format")
        return 1

    if dest_format is None:
        print(f"Error: Cannot detect format for {dest}")
        print("Use --to to specify the destination format")
        return 1

    dry_run = getattr(args, "dry_run", False)

    # Currently supported conversions
    if src_format == "mahlif" and dest_format == "sibelius":
        from mahlif import parse
        from mahlif.sibelius.convert import generate_plugin
        from mahlif.sibelius.convert import write_plugin

        action = "Would convert" if dry_run else "Converting"
        print(f"{action} {src} → {dest}")

        if dry_run:
            return 0

        score = parse(src)
        title = score.meta.work_title or src.stem
        plugin_content = generate_plugin(score, title)
        write_plugin(dest, plugin_content)
        print(f"Generated {dest} ({dest.stat().st_size:,} bytes)")
        return 0

    elif src_format == "mahlif" and dest_format == "lilypond":
        from mahlif import parse
        from mahlif import to_lilypond

        action = "Would convert" if dry_run else "Converting"
        print(f"{action} {src} → {dest}")

        if dry_run:
            return 0

        score = parse(src)
        ly_content = to_lilypond(score)
        dest.write_text(ly_content, encoding="utf-8")
        print(f"Generated {dest} ({dest.stat().st_size:,} bytes)")
        return 0

    elif src_format == "mahlif" and dest_format == "pdf":
        import shutil
        import subprocess
        import tempfile

        from mahlif import parse
        from mahlif import to_lilypond

        # Check lilypond is available
        lilypond = shutil.which("lilypond")
        if lilypond is None:
            print("Error: LilyPond not found")
            print("Install LilyPond from https://lilypond.org/")
            return 1

        action = "Would convert" if dry_run else "Converting"
        print(f"{action} {src} → {dest} (via LilyPond)")

        if dry_run:
            return 0

        score = parse(src)
        ly_content = to_lilypond(score)

        with tempfile.TemporaryDirectory() as tmpdir:
            ly_path = Path(tmpdir) / "score.ly"
            ly_path.write_text(ly_content, encoding="utf-8")

            result = subprocess.run(
                [lilypond, "-o", str(Path(tmpdir) / "score"), str(ly_path)],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print("Error: LilyPond compilation failed")
                print(result.stderr)
                return 1

            pdf_path = Path(tmpdir) / "score.pdf"
            if not pdf_path.exists():
                print("Error: LilyPond did not produce PDF")
                return 1

            shutil.copy(pdf_path, dest)

        print(f"Generated {dest} ({dest.stat().st_size:,} bytes)")
        return 0

    else:
        print(f"Error: Conversion from {src_format} to {dest_format} not supported")
        print()
        print("Supported conversions:")
        print("  mahlif → sibelius (.plg)")
        print("  mahlif → lilypond (.ly)")
        print("  mahlif → pdf (via LilyPond)")
        return 1


def cmd_encoding(args: argparse.Namespace) -> int:
    """Convert file encoding.

    Args:
        args: Parsed arguments

    Returns:
        Exit code (0 for success)
    """
    from mahlif.encoding import convert_encoding

    src = Path(args.file)
    dest = Path(args.output) if args.output else src

    if not src.exists():
        print(f"Error: {src} not found")
        return 1

    try:
        result_path, src_enc, dest_enc = convert_encoding(
            src, args.target, dest, args.source
        )
        if src == dest:
            print(f"Converted {src} to {dest_enc} in place (was {src_enc})")
        else:
            print(f"Converted {src} → {result_path} ({src_enc} → {dest_enc})")
        return 0

    except ValueError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_stats(args: argparse.Namespace) -> int:
    """Run stats command.

    Args:
        args: Parsed arguments

    Returns:
        Exit code (0 for success)
    """
    from mahlif.stats import main as stats_main

    # Re-pack arguments for stats module
    stats_args = [str(args.file)]
    if args.json:
        stats_args.append("--json")
    if args.verbose:
        stats_args.append("--verbose")

    return stats_main(stats_args)


def main(args: list[str] | None = None) -> int:
    """Main entry point for mahlif CLI.

    Args:
        args: Command line arguments (default: sys.argv[1:])

    Returns:
        Exit code (0 for success)
    """
    parser = argparse.ArgumentParser(
        prog="mahlif",
        description="Universal music notation interchange format converter",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {_get_version()}",
    )

    subparsers = parser.add_subparsers(dest="command")

    # convert
    convert_parser = subparsers.add_parser(
        "convert",
        help="Convert between formats",
        description="Convert music notation files between formats",
    )
    convert_parser.add_argument("src", help="Source file")
    convert_parser.add_argument("dest", help="Destination file")
    convert_parser.add_argument(
        "--from",
        dest="from_format",
        choices=["mahlif", "musicxml"],
        help="Source format (default: detect from extension)",
    )
    convert_parser.add_argument(
        "--to",
        dest="to_format",
        choices=["sibelius", "lilypond", "musicxml", "pdf"],
        help="Destination format (default: detect from extension)",
    )
    convert_parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Show what would be done without doing it",
    )

    # stats
    stats_parser = subparsers.add_parser(
        "stats",
        help="Show score statistics",
        description="Display statistics for a Mahlif XML file",
    )
    stats_parser.add_argument("file", type=Path, help="Mahlif XML file")
    stats_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    stats_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show per-staff breakdown",
    )

    # encoding
    encoding_parser = subparsers.add_parser(
        "encoding",
        help="Convert file encoding",
        description="Convert text file between encodings (utf8, utf16, utf16le, utf16be, latin1, ascii)",
    )
    encoding_parser.add_argument(
        "target",
        choices=["utf8", "utf16", "utf16le", "utf16be", "latin1", "ascii"],
        help="Target encoding",
    )
    encoding_parser.add_argument("file", type=Path, help="Input file")
    encoding_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output file (default: overwrite input)",
    )
    encoding_parser.add_argument(
        "-s",
        "--source",
        type=str,
        default=None,
        help="Source encoding (default: auto-detect)",
    )

    # sibelius (subcommands via sibelius.cli)
    from mahlif.sibelius.cli import add_subparsers as add_sibelius_subparsers

    add_sibelius_subparsers(subparsers)

    # manuscript (alias for sibelius - language-focused vs host-focused)
    from mahlif.sibelius.cli import add_subparsers as add_manuscript_subparsers

    add_manuscript_subparsers(subparsers, name="manuscript")

    parsed = parser.parse_args(args)

    if parsed.command is None:
        parser.print_help()
        return 0

    if parsed.command == "convert":
        return cmd_convert(parsed)
    elif parsed.command == "stats":
        return cmd_stats(parsed)
    elif parsed.command == "encoding":
        return cmd_encoding(parsed)
    elif parsed.command in ("sibelius", "manuscript"):
        from mahlif.sibelius.cli import run_command

        return run_command(parsed)

    return 0  # pragma: no cover


def _get_version() -> str:
    """Get package version."""
    try:
        from mahlif import __version__

        return __version__
    except ImportError:  # pragma: no cover
        return "unknown"


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
