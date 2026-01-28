# Tools

## ManuScript Linter

A linter for Sibelius ManuScript `.plg` plugin files.

### Usage

```bash
# Lint a plugin file
python src/mahlif/sibelius/lint.py MahlifExport.plg

# The build script runs the linter automatically
./src/mahlif/sibelius/build.sh
```

### Error Codes

#### Errors (block build)

| Code | Description |
|------|-------------|
| E001 | Unmatched closing brace |
| E002 | Mismatched brace type |
| E003 | Unclosed brace |
| E010 | Plugin must start with `{` |
| E011 | Plugin must end with `}` |

#### Warnings (informational)

| Code | Description |
|------|-------------|
| W001 | Method name is a reserved word |
| W002 | Trailing whitespace |
| W003 | Line too long (>200 chars) |
| W010 | Missing `Initialize` method |
| W011 | Initialize should call `AddToPluginsMenu` |

### Build Script

The build script (`build.sh`) performs these steps:

1. **Lint** - Runs the linter on all `.plg` files; fails on errors
2. **Clean** - Strips trailing whitespace
3. **Convert** - Converts UTF-8 source to UTF-16 BE with BOM (required by Sibelius)
4. **Output** - Writes to `dist/` directory

After building, copy the plugin to Sibelius:

```bash
cp dist/MahlifExport.plg ~/Library/Application\ Support/Avid/Sibelius/Plugins/Other/
```

Then reload in Sibelius: **File > Plug-ins > Edit Plug-ins > Unload/Reload**

!!! note "Symlinks don't work"
    Sibelius doesn't reliably follow symlinks for plugins. Use a direct copy.
