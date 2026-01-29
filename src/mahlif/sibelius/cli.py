"""CLI for Sibelius-related commands.

Usage:
    mahlif sibelius build              # Build all plugins to dist/
    mahlif sibelius build --install    # Build to Sibelius plugin directory
    mahlif sibelius check              # Lint ManuScript files
    mahlif sibelius show-plugin-dir    # Show Sibelius plugin directory

Or standalone:
    python -m mahlif.sibelius build
    python -m mahlif.sibelius check
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def add_subparsers(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Add sibelius subcommand to main CLI parser.

    Args:
        subparsers: Subparsers from main CLI
    """
    sibelius_parser = subparsers.add_parser(
        "sibelius",
        help="Sibelius plugin tools",
        description="Commands for Sibelius plugin development and installation",
    )
    _add_commands(sibelius_parser)


def _add_commands(parser: argparse.ArgumentParser) -> None:
    """Add subcommands to a sibelius parser.

    Args:
        parser: The sibelius parser to add commands to
    """
    subparsers = parser.add_subparsers(dest="sibelius_command", required=True)

    # build
    build_parser = subparsers.add_parser(
        "build",
        help="Build plugins (UTF-8 → UTF-16 BE)",
        description="Convert UTF-8 source .plg files to UTF-16 BE for Sibelius",
    )
    build_parser.add_argument(
        "plugins",
        nargs="*",
        help="Specific plugins to build (default: all)",
    )
    build_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output directory (default: dist/)",
    )
    build_parser.add_argument(
        "--install",
        action="store_true",
        help="Output directly to Sibelius plugin directory",
    )
    build_parser.add_argument(
        "--hardlink",
        action="store_true",
        help="Create hardlinks to Sibelius plugin directory",
    )
    build_parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Show what would be done without doing it",
    )
    build_parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress progress messages",
    )
    build_parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help="Source directory (default: mahlif/sibelius/)",
    )

    # check
    check_parser = subparsers.add_parser(
        "check",
        help="Lint ManuScript files",
        description="Check ManuScript .plg files for common issues",
    )
    check_parser.add_argument(
        "--fix",
        action="store_true",
        help="Auto-fix some issues (e.g., trailing whitespace)",
    )
    check_parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Show what would be fixed without fixing",
    )
    check_parser.add_argument(
        "files",
        type=Path,
        nargs="*",
        help="Files to check (default: all .plg in sibelius directory)",
    )

    # list
    subparsers.add_parser(
        "list",
        help="List available plugins",
        description="List plugins available to build",
    )

    # show-plugin-dir
    subparsers.add_parser(
        "show-plugin-dir",
        help="Show Sibelius plugin directory path",
        description="Print the OS-specific Sibelius plugin directory",
    )


def run_command(args: argparse.Namespace) -> int:
    """Run the appropriate sibelius subcommand.

    Args:
        args: Parsed arguments

    Returns:
        Exit code (0 for success)
    """
    if args.sibelius_command == "build":
        from mahlif.sibelius.build import build_plugins

        error_count, _ = build_plugins(
            source_dir=args.source,
            output_dir=args.output,
            plugin_names=args.plugins,
            install=args.install,
            hardlink=args.hardlink,
            dry_run=args.dry_run,
            verbose=not args.quiet,
        )
        return error_count

    elif args.sibelius_command == "check":
        from mahlif.sibelius.build import find_plugin_sources
        from mahlif.sibelius.lint import lint
        from mahlif.sibelius.lint import fix_trailing_whitespace
        from mahlif.sibelius.lint import read_plugin

        # Filter empty paths (Path('') becomes Path('.'))
        files = [f for f in args.files if str(f) != "."]
        if not files:
            # Default to all plugins in sibelius directory
            source_dir = Path(__file__).parent
            files = find_plugin_sources(source_dir)

        if not files:
            print("No .plg files found")
            return 0

        total_errors = 0
        for path in files:
            if not path.exists():
                print(f"Error: {path} not found")
                total_errors += 1
                continue

            errors = lint(path)

            if args.fix:
                # Check if there's trailing whitespace to fix
                content = read_plugin(path)
                lines = content.split("\n")
                has_trailing = any(line != line.rstrip() for line in lines)

                if has_trailing:
                    if args.dry_run:
                        print(f"Would fix: {path} (trailing whitespace)")
                    else:
                        fix_trailing_whitespace(path)
                        print(f"✓ {path}: Fixed trailing whitespace")

                # Filter out fixed W002 errors
                errors = [e for e in errors if e.code != "W002"]

            if not errors:
                if not args.fix:
                    print(f"✓ {path}: No issues found")
            else:
                error_count = sum(1 for e in errors if e.code.startswith("E"))
                warning_count = len(errors) - error_count
                print(f"✗ {path}: {error_count} error(s), {warning_count} warning(s)")
                for error in errors:
                    print(f"  {error}")
                total_errors += error_count

        return min(total_errors, 127)

    elif args.sibelius_command == "list":
        from mahlif.sibelius.build import find_plugin_sources

        source_dir = Path(__file__).parent
        plugins = find_plugin_sources(source_dir)

        if not plugins:
            print("No plugins found")
            return 0

        print("Available plugins:")
        for plg in plugins:
            print(f"  {plg.stem}")
        return 0

    elif args.sibelius_command == "show-plugin-dir":
        from mahlif.sibelius.build import get_sibelius_plugin_dir

        plugin_dir = get_sibelius_plugin_dir()
        if plugin_dir is None:
            print("Could not detect Sibelius plugin directory for this OS")
            return 1
        print(plugin_dir)
        return 0

    return 1  # pragma: no cover - unreachable with required=True


def main(args: list[str] | None = None) -> int:
    """Main entry point for standalone sibelius CLI.

    Args:
        args: Command line arguments (default: sys.argv[1:])

    Returns:
        Exit code (0 for success)
    """
    parser = argparse.ArgumentParser(
        prog="mahlif sibelius",
        description="Sibelius plugin tools",
    )
    _add_commands(parser)

    parsed = parser.parse_args(args)
    return run_command(parsed)


# no cover: start
if __name__ == "__main__":
    sys.exit(main())
# no cover: stop
