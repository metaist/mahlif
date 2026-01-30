"""CLI for Sibelius-related commands.

Usage:
    mahlif sibelius install            # Install MahlifExport plugin to Sibelius
    mahlif sibelius install Cyrus      # Install specific plugin(s)
    mahlif sibelius build              # Build all plugins to dist/
    mahlif sibelius build --install    # Build all to Sibelius plugin directory
    mahlif sibelius check              # Lint ManuScript files
    mahlif sibelius list               # List available plugins
    mahlif sibelius show-plugin-dir    # Show Sibelius plugin directory

Or standalone:
    python -m mahlif.sibelius install
    python -m mahlif.sibelius build
    python -m mahlif.sibelius check
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _parse_codes(codes_str: str) -> set[str]:
    """Parse comma-separated rule codes into a set.

    Args:
        codes_str: Comma-separated codes like "W002,W003"

    Returns:
        Set of code strings
    """
    if not codes_str:
        return set()
    return {code.strip() for code in codes_str.split(",") if code.strip()}


def add_subparsers(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    name: str = "sibelius",
) -> None:
    """Add sibelius/manuscript subcommand to main CLI parser.

    Args:
        subparsers: Subparsers from main CLI
        name: Name of the subcommand ("sibelius" or "manuscript")
    """
    if name == "manuscript":
        help_text = "ManuScript language tools (alias for sibelius)"
        description = "Commands for ManuScript development (alias for sibelius)"
    else:
        help_text = "Sibelius plugin tools"
        description = "Commands for Sibelius plugin development and installation"

    parser = subparsers.add_parser(
        name,
        help=help_text,
        description=description,
    )
    _add_commands(parser)


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
        "--ignore",
        type=str,
        default="",
        help="Comma-separated list of rule codes to disable (e.g., W002,W003)",
    )
    check_parser.add_argument(
        "--fixable",
        type=str,
        default="",
        help="Comma-separated list of rule codes eligible for fix (default: all)",
    )
    check_parser.add_argument(
        "--unfixable",
        type=str,
        default="",
        help="Comma-separated list of rule codes ineligible for fix",
    )
    check_parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat all warnings as errors",
    )
    check_parser.add_argument(
        "--error",
        type=str,
        default="",
        help="Comma-separated list of warning codes to treat as errors (e.g., MS-W020)",
    )
    check_parser.add_argument(
        "files",
        type=Path,
        nargs="*",
        help="Files to check (default: all .plg in sibelius directory)",
    )

    # install (user-friendly shortcut for build --install)
    install_parser = subparsers.add_parser(
        "install",
        help="Install plugins to Sibelius",
        description="Build and install plugins to Sibelius plugin directory. "
        "By default, installs only MahlifExport. Specify plugin names to install others.",
    )
    install_parser.add_argument(
        "plugins",
        nargs="*",
        help="Plugin names to install (default: MahlifExport)",
    )
    install_parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Show what would be done without doing it",
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

    # format
    format_parser = subparsers.add_parser(
        "format",
        help="Format ManuScript files",
        description="Auto-format ManuScript plugin files",
    )
    format_parser.add_argument(
        "--check",
        action="store_true",
        help="Check if files are formatted (don't modify)",
    )
    format_parser.add_argument(
        "--diff",
        action="store_true",
        help="Show diff of what would change",
    )
    format_parser.add_argument(
        "files",
        type=Path,
        nargs="*",
        help="Files to format (default: all .plg in sibelius directory)",
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
        from mahlif.config import load_config
        from mahlif.sibelius.build import find_plugin_sources
        from mahlif.sibelius.manuscript.lint import fix_trailing_whitespace
        from mahlif.sibelius.manuscript.lint import lint
        from mahlif.sibelius.manuscript.lint import read_plugin

        # Load config file
        config = load_config()

        # Parse comma-separated code lists from CLI (overrides config)
        cli_ignore = _parse_codes(args.ignore)
        cli_fixable = _parse_codes(args.fixable)
        cli_unfixable = _parse_codes(args.unfixable)
        cli_error = _parse_codes(args.error)

        # Merge CLI flags with config (CLI takes precedence)
        ignore_codes = cli_ignore | config.sibelius.lint.ignore
        fixable_codes = cli_fixable | config.sibelius.lint.fixable
        unfixable_codes = cli_unfixable | config.sibelius.lint.unfixable
        error_codes = cli_error | config.sibelius.lint.error
        strict_mode = args.strict or config.sibelius.lint.strict

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

            # Filter out ignored errors
            if ignore_codes:
                errors = [e for e in errors if e.code not in ignore_codes]

            if args.fix:
                # Determine which codes are fixable
                # If --fixable is specified, only those codes are fixable
                # If --unfixable is specified, those codes are not fixable
                # Default: all fixable codes are fixable
                def is_fixable(code: str) -> bool:
                    if code in unfixable_codes:
                        return False
                    if fixable_codes:
                        return code in fixable_codes
                    return True

                # Check if there's trailing whitespace to fix
                content = read_plugin(path)
                lines = content.split("\n")
                has_trailing = any(line != line.rstrip() for line in lines)

                if has_trailing and is_fixable("MS-W002"):
                    if args.dry_run:
                        print(f"Would fix: {path} (trailing whitespace)")
                    else:
                        fix_trailing_whitespace(path)
                        print(f"✓ {path}: Fixed trailing whitespace")
                    # Filter out fixed W002 errors
                    errors = [e for e in errors if e.code != "MS-W002"]

            if not errors:
                if not args.fix:
                    print(f"✓ {path}: No issues found")
            else:
                # Count errors: MS-E* are always errors
                # Warnings (MS-W*) become errors if --strict or in --error list
                def is_error(code: str) -> bool:
                    if code.startswith("MS-E"):
                        return True
                    if strict_mode:
                        return True
                    if code in error_codes:
                        return True
                    return False

                error_count = sum(1 for e in errors if is_error(e.code))
                warning_count = len(errors) - error_count
                print(f"✗ {path}: {error_count} error(s), {warning_count} warning(s)")
                for error in errors:
                    print(f"  {error}")
                total_errors += error_count

        return min(total_errors, 127)

    elif args.sibelius_command == "install":
        from mahlif.sibelius.build import build_plugins

        # Default to MahlifExport if no plugins specified
        plugin_names = args.plugins if args.plugins else ["MahlifExport"]

        error_count, _ = build_plugins(
            plugin_names=plugin_names,
            install=True,
            dry_run=args.dry_run,
        )
        return error_count

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

    elif args.sibelius_command == "format":
        from mahlif.sibelius.build import find_plugin_sources
        from mahlif.sibelius.manuscript.format import format_file
        from mahlif.sibelius.manuscript.format import format_file_in_place

        # Filter empty paths
        files = [f for f in args.files if str(f) != "."]
        if not files:
            # Default to all plugins in sibelius directory
            source_dir = Path(__file__).parent
            files = find_plugin_sources(source_dir)

        unformatted_count = 0
        for path in files:
            if not path.exists():
                print(f"Error: {path} not found", file=sys.stderr)
                unformatted_count += 1
                continue

            original = path.read_text(encoding="utf-8")
            formatted = format_file(path)

            if original == formatted:
                if not args.check:
                    print(f"✓ {path}: Already formatted")
                continue

            if args.check:
                print(f"✗ {path}: Would reformat")
                unformatted_count += 1
            elif args.diff:
                import difflib

                diff = difflib.unified_diff(
                    original.splitlines(keepends=True),
                    formatted.splitlines(keepends=True),
                    fromfile=str(path),
                    tofile=str(path),
                )
                print("".join(diff))
                unformatted_count += 1
            else:
                format_file_in_place(path)
                print(f"✓ {path}: Reformatted")

        if args.check and unformatted_count > 0:
            print(f"\n{unformatted_count} file(s) would be reformatted")
            return 1

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
