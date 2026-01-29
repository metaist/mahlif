# CLI Reference

Mahlif provides a command-line interface for format conversion and plugin management.

```bash
mahlif <command> [options]
```

## Commands

| Command | Description |
|---------|-------------|
| [`convert`](#convert) | Convert between formats |
| [`stats`](#stats) | Show score statistics |
| [`sibelius`](#sibelius) | Sibelius plugin management |

---

## `convert`

Convert a Mahlif XML file to another format.

```bash
mahlif convert <input> <output> [options]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `input` | Source file (`.mahlif.xml`) |
| `output` | Destination file (`.ly`, `.plg`) |

### Options

| Option | Description |
|--------|-------------|
| `--dry-run` | Show what would be done without writing files |

### Supported Conversions

| From | To | Extension |
|------|-----|-----------|
| Mahlif XML | LilyPond | `.ly` |
| Mahlif XML | Sibelius Plugin | `.plg` |

### Examples

```bash
# Convert to LilyPond
mahlif convert score.mahlif.xml score.ly

# Convert to Sibelius import plugin
mahlif convert score.mahlif.xml import_score.plg

# Preview conversion
mahlif convert score.mahlif.xml score.ly --dry-run
```

See also: [LilyPond](lilypond.md), [Sibelius](sibelius.md)

---

## `stats`

Display statistics about a Mahlif XML score.

```bash
mahlif stats <file> [options]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `file` | Mahlif XML file to analyze |

### Options

| Option | Description |
|--------|-------------|
| `--json` | Output as JSON |
| `--verbose`, `-v` | Show per-staff breakdown |

### Example Output

```
Score: Symphony No. 5
Composer: Beethoven

Staves: 12
Bars: 502
Notes: 15,234
Chords: 2,891
Rests: 4,102
Dynamics: 347
Slurs: 892
Hairpins: 156
Text: 89
```

### JSON Output

```bash
mahlif stats score.mahlif.xml --json
```

```json
{
  "title": "Symphony No. 5",
  "composer": "Beethoven",
  "staves": 12,
  "bars": 502,
  "notes": 15234,
  ...
}
```

---

## `sibelius`

Sibelius plugin management commands.

```bash
mahlif sibelius <subcommand> [options]
```

### Subcommands

| Subcommand | Description |
|------------|-------------|
| [`build`](#sibelius-build) | Build plugins from source |
| [`check`](#sibelius-check) | Lint ManuScript files |
| [`list`](#sibelius-list) | List available plugins |
| [`show-plugin-dir`](#sibelius-show-plugin-dir) | Show plugin directory |

See [Sibelius](sibelius.md) for detailed documentation.

---

### `sibelius build`

Build ManuScript plugins from source.

```bash
mahlif sibelius build [plugins...] [options]
```

#### Arguments

| Argument | Description |
|----------|-------------|
| `plugins` | Plugin names or paths (optional, defaults to all) |

#### Options

| Option | Description |
|--------|-------------|
| `--install` | Install directly to Sibelius plugin directory |
| `--hardlink` | Create hardlinks in Sibelius directory (for development) |
| `--dry-run` | Show what would be done without writing files |
| `--quiet`, `-q` | Suppress output |

#### Examples

```bash
# Build all plugins to dist/
mahlif sibelius build

# Build and install
mahlif sibelius build --install

# Build specific plugin with hardlinks
mahlif sibelius build MahlifExport --hardlink

# Preview build
mahlif sibelius build --dry-run
```

---

### `sibelius check`

Lint ManuScript plugin files for errors and style issues.

```bash
mahlif sibelius check [files...] [options]
```

#### Arguments

| Argument | Description |
|----------|-------------|
| `files` | Files to check (optional, defaults to all source plugins) |

#### Options

| Option | Description |
|--------|-------------|
| `--fix` | Automatically fix trailing whitespace (W002) |
| `--dry-run` | Show what would be fixed without modifying files |
| `--quiet`, `-q` | Only show errors, not warnings |

#### Examples

```bash
# Check all plugins
mahlif sibelius check

# Check specific file
mahlif sibelius check path/to/plugin.plg

# Fix trailing whitespace
mahlif sibelius check --fix

# Preview fixes
mahlif sibelius check --fix --dry-run
```

See [Sibelius § ManuScript Linter](sibelius.md#manuscript-linter) for error codes.

---

### `sibelius list`

List available plugins in the package.

```bash
mahlif sibelius list
```

#### Example Output

```
Available plugins:
  MahlifExport
  MahlifImport
```

---

### `sibelius show-plugin-dir`

Show the Sibelius plugin directory for your platform.

```bash
mahlif sibelius show-plugin-dir
```

#### Example Output

```
/Users/username/Library/Application Support/Avid/Sibelius/Plugins
```

Returns exit code 1 if Sibelius plugin directory cannot be detected.
