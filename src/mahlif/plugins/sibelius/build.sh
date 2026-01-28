#!/bin/bash
# Convert UTF-8 plugin sources to UTF-16 BE for Sibelius
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_DIR="$SCRIPT_DIR"
# Build to repo root dist/
BUILD_DIR="$SRC_DIR/../../../../dist"

mkdir -p "$BUILD_DIR"

for plg in "$SRC_DIR"/*.plg; do
    [ -f "$plg" ] || continue
    name=$(basename "$plg")
    echo "Converting $name..."
    printf '\xfe\xff' > "$BUILD_DIR/$name"
    iconv -f UTF-8 -t UTF-16BE "$plg" >> "$BUILD_DIR/$name"
done

echo "Done. Now reload in Sibelius: File > Plug-ins > Edit Plug-ins > Unload/Reload"
