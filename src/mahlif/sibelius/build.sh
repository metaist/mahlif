#!/bin/bash
# Convert UTF-8 plugin sources to UTF-16 BE for Sibelius
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_DIR="$SCRIPT_DIR"
# Build to repo root dist/
BUILD_DIR="$SRC_DIR/../../../dist"

mkdir -p "$BUILD_DIR"

# Lint first
REPO_ROOT="$SRC_DIR/../../.."
echo "Linting plugins..."
lint_failed=0
for plg in "$SRC_DIR"/*.plg; do
    [ -f "$plg" ] || continue
    # Only fail on errors (E*), not warnings (W*)
    if ! uv run --project "$REPO_ROOT" python -m mahlif.sibelius.lint "$plg" 2>&1 | grep -q '\[E[0-9]'; then
        :
    else
        uv run --project "$REPO_ROOT" python -m mahlif.sibelius.lint "$plg"
        lint_failed=1
    fi
done

if [ $lint_failed -eq 1 ]; then
    echo "Lint errors found. Fix before building."
    exit 1
fi

# Build - main directory
for plg in "$SRC_DIR"/*.plg; do
    [ -f "$plg" ] || continue
    name=$(basename "$plg")
    echo "Converting $name..."
    # Strip trailing whitespace during conversion
    printf '\xfe\xff' > "$BUILD_DIR/$name"
    sed 's/[[:space:]]*$//' "$plg" | iconv -f UTF-8 -t UTF-16BE >> "$BUILD_DIR/$name"
done

# Build - subdirectories (like cyrus/)
for subdir in "$SRC_DIR"/*/; do
    [ -d "$subdir" ] || continue
    for plg in "$subdir"*.plg; do
        [ -f "$plg" ] || continue
        name=$(basename "$plg")
        echo "Converting $name (from $(basename "$subdir"))..."
        printf '\xfe\xff' > "$BUILD_DIR/$name"
        sed 's/[[:space:]]*$//' "$plg" | iconv -f UTF-8 -t UTF-16BE >> "$BUILD_DIR/$name"
    done
done

echo "Done. Now reload in Sibelius: File > Plug-ins > Edit Plug-ins > Unload/Reload"
