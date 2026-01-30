# CLI Reference

Mahlif provides a command-line interface for format conversion and plugin management.

```bash
mahlif <command> [options]
```

## Commands

| Command                 | Description                |
| ----------------------- | -------------------------- |
| [`convert`](#convert)   | Convert between formats    |
| [`stats`](#stats)       | Show score statistics      |
| [`encoding`](#encoding) | Convert file encoding      |
| [`sibelius`](#sibelius) | Sibelius plugin management |

---

## `convert`

Convert a Mahlif XML file to another format.

```bash
mahlif convert <input> <output> [options]
```

### Arguments

| Argument | Description                      |
| -------- | -------------------------------- |
| `input`  | Source file (`.mahlif.xml`)      |
| `output` | Destination file (`.ly`, `.plg`) |

### Options

| Option      | Description                                   |
| ----------- | --------------------------------------------- |
| `--dry-run` | Show what would be done without writing files |

### Supported Conversions

| From       | To              | Extension |
| ---------- | --------------- | --------- |
| Mahlif XML | LilyPond        | `.ly`     |
| Mahlif XML | Sibelius Plugin | `.plg`    |

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

## `encoding`

Convert a file between text encodings.

```bash
mahlif encoding <target> <file> [options]
```

### Arguments

| Argument | Description                                                                |
| -------- | -------------------------------------------------------------------------- |
| `target` | Target encoding (`utf8`, `utf16`, `utf16le`, `utf16be`, `latin1`, `ascii`) |
| `file`   | Input file                                                                 |

### Options

| Option           | Description                            |
| ---------------- | -------------------------------------- |
| `-o`, `--output` | Output file (default: overwrite input) |
| `-s`, `--source` | Source encoding (default: auto-detect) |

### Examples

```bash
# Convert UTF-16 file to UTF-8
mahlif encoding utf8 score.mahlif.xml

# Convert with explicit output file
mahlif encoding utf8 score.mahlif.xml -o score_utf8.mahlif.xml

# Convert with explicit source encoding
mahlif encoding utf8 score.mahlif.xml -s utf16le
```

---

## `stats`

Display statistics about a Mahlif XML score.

```bash
mahlif stats <file> [options]
```

### Arguments

| Argument | Description                |
| -------- | -------------------------- |
| `file`   | Mahlif XML file to analyze |

### Options

| Option            | Description              |
| ----------------- | ------------------------ |
| `--json`          | Output as JSON           |
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

| Subcommand                                     | Description                 |
| ---------------------------------------------- | --------------------------- |
| [`install`](#sibelius-install)                 | Install plugins to Sibelius |
| [`build`](#sibelius-build)                     | Build plugins from source   |
| [`check`](#sibelius-check)                     | Lint ManuScript files       |
| [`format`](#sibelius-format)                   | Format ManuScript files     |
| [`list`](#sibelius-list)                       | List available plugins      |
| [`show-plugin-dir`](#sibelius-show-plugin-dir) | Show plugin directory       |

See [Sibelius](sibelius.md) for detailed documentation.

---

### `sibelius install`

Install plugins to Sibelius plugin directory. By default, installs only the `MahlifExport` plugin.

```bash
mahlif sibelius install [plugins...] [options]
```

#### Arguments

| Argument  | Description                                     |
| --------- | ----------------------------------------------- |
| `plugins` | Plugin names to install (default: MahlifExport) |

#### Options

| Option      | Description                                |
| ----------- | ------------------------------------------ |
| `--dry-run` | Show what would be done without installing |

#### Examples

```bash
# Install MahlifExport plugin (default)
mahlif sibelius install

# Install a specific plugin
mahlif sibelius install Cyrus

# Install multiple plugins
mahlif sibelius install MahlifExport Cyrus

# Preview installation
mahlif sibelius install --dry-run
```

---

### `sibelius build`

Build ManuScript plugins from source.

```bash
mahlif sibelius build [plugins...] [options]
```

#### Arguments

| Argument  | Description                                       |
| --------- | ------------------------------------------------- |
| `plugins` | Plugin names or paths (optional, defaults to all) |

#### Options

| Option          | Description                                              |
| --------------- | -------------------------------------------------------- |
| `--install`     | Install directly to Sibelius plugin directory            |
| `--hardlink`    | Create hardlinks in Sibelius directory (for development) |
| `--dry-run`     | Show what would be done without writing files            |
| `--quiet`, `-q` | Suppress output                                          |

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

| Argument | Description                                               |
| -------- | --------------------------------------------------------- |
| `files`  | Files to check (optional, defaults to all source plugins) |

#### Options

| Option          | Description                                      |
| --------------- | ------------------------------------------------ |
| `--fix`         | Automatically fix trailing whitespace (MS-W002)  |
| `--dry-run`     | Show what would be fixed without modifying files |
| `--quiet`, `-q` | Only show errors, not warnings                   |

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

### `sibelius format`

Auto-format ManuScript plugin files.

```bash
mahlif sibelius format [files...] [options]
```

#### Arguments

| Argument | Description                                                |
| -------- | ---------------------------------------------------------- |
| `files`  | Files to format (optional, defaults to all source plugins) |

#### Options

| Option    | Description                                 |
| --------- | ------------------------------------------- |
| `--check` | Check if files are formatted (don't modify) |
| `--diff`  | Show diff of what would change              |

#### Examples

```bash
# Format all plugins
mahlif sibelius format

# Check formatting without modifying
mahlif sibelius format --check

# Show what would change
mahlif sibelius format --diff
```

See [Sibelius § ManuScript Formatter](sibelius.md#manuscript-formatter) for formatting rules.

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
