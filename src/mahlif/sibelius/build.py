"""Build Sibelius plugins (UTF-8 → UTF-16 BE).

Python replacement for build.sh. Converts UTF-8 source .plg files to
UTF-16 BE with BOM, which is required by Sibelius.

Usage:
    mahlif sibelius build                     # Build all to dist/
    mahlif sibelius build MahlifExport        # Build specific plugin
    mahlif sibelius build --install           # Build to Sibelius plugin dir
    mahlif sibelius build --hardlink          # Build to dist/ + hardlink
    mahlif sibelius build --dry-run           # Show what would be done
"""

from __future__ import annotations

import sys
from pathlib import Path

from mahlif.encoding import encode_utf16be
from mahlif.sibelius.manuscript.lint import lint
from mahlif.sibelius.manuscript.lint import read_plugin


def get_sibelius_plugin_dir() -> Path | None:
    """Get the Sibelius plugin directory for the current OS.

    Returns:
        Path to plugin directory, or None if not detected

    Plugin paths:
        macOS: ~/Library/Application Support/Avid/Sibelius/Plugins/Other/
        Windows: %APPDATA%/Avid/Sibelius/Plugins/Other/
        Linux: Not officially supported by Sibelius
    """
    if sys.platform == "darwin":
        return Path.home() / "Library/Application Support/Avid/Sibelius/Plugins/Other"
    elif sys.platform == "win32":
        appdata = Path.home() / "AppData/Roaming"
        return appdata / "Avid/Sibelius/Plugins/Other"
    else:
        # Linux / other - no official Sibelius support
        return None


def convert_to_utf16be(content: str) -> bytes:
    """Convert string to UTF-16 BE with BOM.

    Args:
        content: Source content (UTF-8 string)

    Returns:
        UTF-16 BE encoded bytes with BOM prefix
    """
    # Strip trailing whitespace from each line
    lines = content.split("\n")
    cleaned = "\n".join(line.rstrip() for line in lines)
    return encode_utf16be(cleaned)


def find_plugin_sources(source_dir: Path) -> list[Path]:
    """Find all .plg files in source directory and subdirectories.

    Args:
        source_dir: Directory to search

    Returns:
        List of .plg file paths
    """
    plugins: list[Path] = []

    # Main directory
    for plg in source_dir.glob("*.plg"):
        plugins.append(plg)

    # Subdirectories (like cyrus/)
    for subdir in source_dir.iterdir():
        if subdir.is_dir() and not subdir.name.startswith("."):
            for plg in subdir.glob("*.plg"):
                plugins.append(plg)

    return sorted(plugins)


def resolve_plugins(
    source_dir: Path,
    args: list[str],
) -> tuple[list[Path], list[str]]:
    """Resolve plugin arguments to paths.

    Args can be:
    - Plugin names (e.g., "MahlifExport")
    - Paths (e.g., "./MahlifExport.plg", "../other/Custom.plg")

    Args:
        source_dir: Default source directory for name lookups
        args: Plugin names or paths

    Returns:
        Tuple of (resolved paths, unresolved names)
    """
    if not args:
        return find_plugin_sources(source_dir), []

    resolved: list[Path] = []
    unresolved: list[str] = []

    # Build lookup map for names
    available = {p.stem: p for p in find_plugin_sources(source_dir)}

    for arg in args:
        # Check if it looks like a path
        if "/" in arg or "\\" in arg or arg.endswith(".plg"):
            path = Path(arg)
            if path.exists():
                resolved.append(path)
            else:
                unresolved.append(arg)
        else:
            # Treat as name
            if arg in available:
                resolved.append(available[arg])
            else:
                unresolved.append(arg)

    return resolved, unresolved


def build_plugins(
    source_dir: Path | None = None,
    output_dir: Path | None = None,
    plugin_names: list[str] | None = None,
    install: bool = False,
    hardlink: bool = False,
    dry_run: bool = False,
    verbose: bool = True,
) -> tuple[int, list[Path]]:
    """Build plugins from source directory.

    Args:
        source_dir: Directory containing .plg sources (default: sibelius module dir)
        output_dir: Output directory (default: dist/, or Sibelius dir if install=True)
        plugin_names: Specific plugins to build (default: all)
        install: If True, output directly to Sibelius plugin directory
        hardlink: If True, create hardlinks to Sibelius plugin directory
        dry_run: If True, show what would be done without doing it
        verbose: Print progress messages

    Returns:
        Tuple of (error_count, list of built plugin paths)
    """
    if source_dir is None:
        source_dir = Path(__file__).parent

    # Determine output directory
    sibelius_dir: Path | None = None
    if install:
        sibelius_dir = get_sibelius_plugin_dir()
        if sibelius_dir is None:
            if verbose:
                print("Error: Could not detect Sibelius plugin directory")
                print("Your OS may not be supported, or Sibelius is not installed.")
            return 1, []
        if output_dir is None:
            output_dir = sibelius_dir
    elif output_dir is None:
        # Default to repo root dist/
        output_dir = source_dir.parent.parent.parent / "dist"

    assert output_dir is not None  # for type checker

    # Resolve plugins from args
    plugins, unresolved = resolve_plugins(source_dir, plugin_names or [])

    if unresolved:
        if verbose:
            print(f"Error: Could not find plugins: {', '.join(unresolved)}")
            available = find_plugin_sources(source_dir)
            if available:
                print(f"Available: {', '.join(p.stem for p in available)}")
        return 1, []

    if not plugins:
        if verbose:
            print(f"No .plg files found in {source_dir}")
        return 0, []

    if dry_run and verbose:
        print("Dry run - no changes will be made")
        print()

    # Format all plugins first
    if verbose:
        print("Formatting plugins...")
    for plg in plugins:
        if not dry_run:
            from mahlif.sibelius.manuscript.format import format_file_in_place

            changed = format_file_in_place(plg)
            if changed and verbose:
                print(f"  Formatted {plg.name}")

    # Lint all plugins
    if verbose:
        print("Linting plugins...")
    lint_failed = False
    for plg in plugins:
        errors = lint(plg)
        # Only fail on errors (E*), not warnings (W*)
        error_count = sum(1 for e in errors if e.code.startswith("MS-E"))
        warning_count = len(errors) - error_count
        if error_count > 0:
            if verbose:
                print(
                    f"✗ {plg.name}: {error_count} error(s), {warning_count} warning(s)"
                )
                for error in errors:
                    if error.code.startswith("MS-E"):
                        print(f"  {error}")
            lint_failed = True
        elif verbose:
            print(f"✓ {plg.name}: {error_count} error(s), {warning_count} warning(s)")

    if lint_failed:
        if verbose:
            print("Lint errors found. Fix before building.")
        return 1, []

    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)

    # Build plugins
    built: list[Path] = []
    for plg in plugins:
        output_path = output_dir / plg.name
        if verbose:
            print(f"Converting {plg.name} -> {output_path}")

        if not dry_run:
            content = read_plugin(plg)
            utf16_bytes = convert_to_utf16be(content)
            output_path.write_bytes(utf16_bytes)

        built.append(output_path)

    # Create hardlinks if requested (and not installing directly)
    if hardlink and not install:
        sibelius_dir = get_sibelius_plugin_dir()
        if sibelius_dir is None:
            if verbose:
                print("Warning: Could not detect Sibelius plugin directory")
                print("Hardlinks not created")
        else:
            if not dry_run:
                sibelius_dir.mkdir(parents=True, exist_ok=True)
            if verbose:
                print(f"Creating hardlinks in {sibelius_dir}...")

            for output_path in built:
                link_path = sibelius_dir / output_path.name
                if verbose:
                    print(f"  {output_path.name} -> {link_path}")
                if not dry_run:
                    if link_path.exists():
                        # Check if already hardlinked to the same inode
                        if link_path.stat().st_ino == output_path.stat().st_ino:
                            # Already a valid hardlink, nothing to do
                            continue
                        # Different file, need to replace
                        link_path.unlink()
                    link_path.hardlink_to(output_path)

    if verbose:
        action = "Would build" if dry_run else "Built"
        print(f"Done. {action} {len(built)} plugin(s) to {output_dir}")
        if sibelius_dir is not None and not dry_run:
            print("Reload in Sibelius: File > Plug-ins > Edit Plug-ins > Unload/Reload")

    return 0, built


def main(args: list[str] | None = None) -> int:
    """Main entry point for build command.

    Args:
        args: Command line arguments (default: sys.argv[1:])

    Returns:
        Exit code (0 for success)
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Build Sibelius plugins (UTF-8 → UTF-16 BE)"
    )
    parser.add_argument(
        "plugins",
        nargs="*",
        help="Specific plugins to build (default: all)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output directory (default: dist/)",
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help="Output directly to Sibelius plugin directory",
    )
    parser.add_argument(
        "--hardlink",
        action="store_true",
        help="Create hardlinks to Sibelius plugin directory",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Show what would be done without doing it",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress progress messages",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help="Source directory (default: mahlif/sibelius/)",
    )

    parsed = parser.parse_args(args)

    error_count, _ = build_plugins(
        source_dir=parsed.source,
        output_dir=parsed.output,
        plugin_names=parsed.plugins,
        install=parsed.install,
        hardlink=parsed.hardlink,
        dry_run=parsed.dry_run,
        verbose=not parsed.quiet,
    )

    return error_count


# no cover: start
if __name__ == "__main__":
    sys.exit(main())
# no cover: stop
