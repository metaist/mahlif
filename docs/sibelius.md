# Sibelius

Mahlif provides bidirectional support for Sibelius via ManuScript plugins.

| Direction         | Status         | Method        |
| ----------------- | -------------- | ------------- |
| Sibelius → Mahlif | ✅ Working     | Export plugin |
| Mahlif → Sibelius | 🚧 In Progress | Import plugin |

## Quick Start

### Install the Export Plugin

```bash
# Install plugins to Sibelius
mahlif sibelius install
```

**For developers:**

```bash
# Build plugins to dist/
mahlif sibelius build

# Or with hardlinks (edit source, reload in Sibelius)
mahlif sibelius build --hardlink
```

### Export from Sibelius

1. Open your score in Sibelius
2. Go to **Home → Plug-ins → Mahlif → Export to Mahlif XML**
3. Save the `.mahlif.xml` file

### Plugin Directory Locations

| Platform | Path                                                   |
| -------- | ------------------------------------------------------ |
| macOS    | `~/Library/Application Support/Avid/Sibelius/Plugins/` |
| Windows  | `%APPDATA%\Avid\Sibelius\Plugins\`                     |

To show your plugin directory:

```bash
mahlif sibelius show-plugin-dir
```

## CLI Commands

### `mahlif sibelius install`

Install plugins to Sibelius plugin directory. By default, installs only the `MahlifExport` plugin.

```bash
# Install MahlifExport plugin (default)
mahlif sibelius install

# Install a specific plugin
mahlif sibelius install Cyrus

# Install multiple plugins
mahlif sibelius install MahlifExport Cyrus

# Preview without installing
mahlif sibelius install --dry-run
```

### `mahlif sibelius build`

Build ManuScript plugins from source.

```bash
# Build all plugins to dist/
mahlif sibelius build

# Build specific plugins
mahlif sibelius build MahlifExport MahlifImport

# Build and install to Sibelius plugin directory
mahlif sibelius build --install

# Create hardlinks for development workflow
mahlif sibelius build --hardlink

# Preview without writing files
mahlif sibelius build --dry-run
```

The build process:

1. Lints each `.plg` file for errors
2. Converts UTF-8 source to UTF-16 BE with BOM (required by Sibelius)
3. Writes to output directory

### `mahlif sibelius check`

Lint ManuScript plugin files.

```bash
# Check specific files
mahlif sibelius check plugin.plg

# Check and fix trailing whitespace
mahlif sibelius check --fix plugin.plg

# Preview fixes without applying
mahlif sibelius check --fix --dry-run plugin.plg
```

### `mahlif sibelius list`

List available plugins in the package.

```bash
mahlif sibelius list
```

### `mahlif sibelius show-plugin-dir`

Show the Sibelius plugin directory for your platform.

```bash
mahlif sibelius show-plugin-dir
```

## ManuScript Linter

The linter catches common errors in ManuScript `.plg` files.

### Error Codes

Errors block the build:

| Code    | Description                                       |
| ------- | ------------------------------------------------- |
| MS-E001 | Unmatched closing brace                           |
| MS-E002 | Mismatched brace type (e.g., `{` closed with `]`) |
| MS-E003 | Unclosed brace at end of file                     |
| MS-E010 | Plugin must start with `{`                        |
| MS-E011 | Plugin must end with `}`                          |

### Warning Codes

Warnings are informational:

| Code    | Description                                     |
| ------- | ----------------------------------------------- |
| MS-W001 | Method name is a reserved word                  |
| MS-W002 | Trailing whitespace (auto-fixable with `--fix`) |
| MS-W003 | Line too long (>200 characters)                 |
| MS-W010 | Missing `Initialize` method                     |
| MS-W011 | `Initialize` should call `AddToPluginsMenu`     |

### Disabling Warnings

You can disable specific warnings using:

**CLI flags:**

```bash
mahlif sibelius check --ignore MS-W002,MS-W003 file.plg
```

**Inline comments:**

```manuscript
// noqa: MS-W002
someMethod "() { ... }"

x = 1;  // noqa: MS-W002

// mahlif: ignore MS-W002
someOtherMethod "() { ... }"

// mahlif: disable MS-W002
// ... code with trailing whitespace ...
// mahlif: enable MS-W002
```

**Config file (`mahlif.toml`):**

```toml
[sibelius.lint]
ignore = ["MS-W002", "MS-W003"]
```

## ManuScript Formatter

The formatter standardizes ManuScript code style.

```bash
# Format all plugins
mahlif sibelius format

# Check formatting
mahlif sibelius format --check

# Show diff
mahlif sibelius format --diff
```

### Formatting Rules

The formatter applies consistent style:

- **Indentation**: 4 spaces per level
- **Trailing whitespace**: Removed
- **Blank lines**: Normalized around methods
- **Braces**: Consistent placement

### Example

Before:

```manuscript
{
Initialize "() {
AddToPluginsMenu('Test','Run');
}"
Run "() {
x=1;
}"
}
```

After:

```manuscript
{
    Initialize "() {
        AddToPluginsMenu('Test', 'Run');
    }"

    Run "() {
        x = 1;
    }"
}
```

## Development Workflow

For plugin development, use hardlinks to avoid copying after each edit:

```bash
# Create hardlinks (one-time setup)
mahlif sibelius build --hardlink

# After editing source, rebuild
mahlif sibelius build

# Reload in Sibelius: File → Plug-ins → Edit Plug-ins → select plugin → Unload → Load
```

!!! note

    Sibelius doesn't follow symlinks reliably. Use hardlinks or direct copies.

---

## Property Mapping Reference

This section maps Mahlif XML elements to Sibelius ManuScript API properties.
Properties are verified against the official ManuScript Language Guide (2024).

!!! info "Legend"

    - ❌ Not yet implemented
    - ⚠️ Partial support or caveats

### Score Metadata

| Mahlif XML         | Sibelius Property         | Type   | Notes                   |
| ------------------ | ------------------------- | ------ | ----------------------- |
| `<work-title>`     | `Score.Title`             | string | read/write              |
| `<composer>`       | `Score.Composer`          | string | read/write              |
| `<lyricist>`       | `Score.Lyricist`          | string | read/write              |
| `<arranger>`       | `Score.Arranger`          | string | read/write              |
| `<copyright>`      | `Score.Copyright`         | string | read/write              |
| `<publisher>`      | `Score.Publisher`         | string | read/write              |
| `<source-file>`    | `Score.FileName`          | string | read only               |
| `<source-format>`  | `Sibelius.ProgramVersion` | int    | Version × 1000          |
| ❌ `<opus>`        | `Score.OpusNumber`        | string |                         |
| ❌ `<dedication>`  | `Score.Dedication`        | string |                         |
| ❌ `<duration-ms>` | `Score.ScoreDuration`     | int    | Milliseconds, read only |

### Page Layout

Accessed via `Score.DocumentSetup` object. Units default to millimeters.

| Mahlif XML         | Sibelius Property                  | Type  | Notes                   |
| ------------------ | ---------------------------------- | ----- | ----------------------- |
| `<page width="">`  | `DocumentSetup.PageWidth`          | float | mm                      |
| `<page height="">` | `DocumentSetup.PageHeight`         | float | mm                      |
| `<staff-height>`   | `DocumentSetup.StaffSize`          | float | mm                      |
| ❌ `<margins>`     | `DocumentSetup.PageTopMargin` etc. | float |                         |
| ❌ `<orientation>` | `DocumentSetup.Orientation`        | int   | 0=portrait, 1=landscape |

### Staff Properties

| Mahlif XML            | Sibelius Property           | Type         | Notes               |
| --------------------- | --------------------------- | ------------ | ------------------- |
| `<staff n="">`        | `Staff.StaffNum`            | int          | 1-indexed           |
| `instrument=""`       | `Staff.InstrumentName`      | string       | Full name           |
| `instrument-short=""` | `Staff.ShortInstrumentName` | string       | Abbreviated         |
| `clef=""`             | `Staff.InitialClefStyleId`  | string       | e.g., `clef.treble` |
| `key-sig=""`          | `Staff.InitialKeySignature` | KeySignature | Object              |
| ❌ `lines=""`         | Via `InstrumentType`        | int          |                     |
| ❌ `transposition=""` | Via `InstrumentType`        | int          | Semitones           |

#### Clef Style IDs

| Mahlif Value | Sibelius StyleId          |
| ------------ | ------------------------- |
| `treble`     | `clef.treble` or `clef.g` |
| `bass`       | `clef.bass` or `clef.f`   |
| `alto`       | `clef.alto` or `clef.c`   |
| `tenor`      | `clef.tenor`              |
| `treble-8vb` | `clef.treble.down.8`      |
| `treble-8va` | `clef.treble.up.8`        |
| `bass-8vb`   | `clef.bass.down.8`        |
| `bass-8va`   | `clef.bass.up.8`          |
| `percussion` | `clef.percussion`         |

### Bar Properties

| Mahlif XML   | Sibelius Property | Type   | Notes                    |
| ------------ | ----------------- | ------ | ------------------------ |
| `<bar n="">` | `Bar.BarNumber`   | int    | 1-indexed                |
| `length=""`  | `Bar.Length`      | int    | In 1/256th quarter notes |
| `break=""`   | Via bar objects   | string | SystemBreak/PageBreak    |

### NoteRest Properties

A `NoteRest` contains zero or more `Note` objects. Zero notes = rest.

| Mahlif XML  | Sibelius Property      | Type | Notes            |
| ----------- | ---------------------- | ---- | ---------------- |
| `pos=""`    | `NoteRest.Position`    | int  | 1/256th quarters |
| `dur=""`    | `NoteRest.Duration`    | int  | 1/256th quarters |
| `voice=""`  | `NoteRest.VoiceNumber` | int  | 1-4              |
| `hidden=""` | `NoteRest.Hidden`      | bool | ⚠️ Via BarObject |
| `dx=""`     | `NoteRest.Dx`          | int  | 1/32nd space     |
| `dy=""`     | `NoteRest.Dy`          | int  | 1/32nd space     |
| `stem=""`   | `NoteRest.StemFlipped` | bool |                  |
| `beam=""`   | `NoteRest.Beam`        | int  | 0-3              |
| ❌ `cue=""` | —                      | —    |                  |

#### Duration Values

| Duration | Ticks (1/256th quarter) |
| -------- | ----------------------- |
| Whole    | 1024                    |
| Half     | 512                     |
| Quarter  | 256                     |
| Eighth   | 128                     |
| 16th     | 64                      |
| 32nd     | 32                      |
| Dotted   | base × 1.5              |

### Note Properties

Individual notes within a chord.

| Mahlif XML         | Sibelius Property    | Type | Notes              |
| ------------------ | -------------------- | ---- | ------------------ |
| `pitch=""`         | `Note.Pitch`         | int  | MIDI, 60 = C4      |
| `written-pitch=""` | `Note.WrittenPitch`  | int  | Transposing        |
| `diatonic=""`      | `Note.DiatonicPitch` | int  | 35 = C4, +7/octave |
| `accidental=""`    | `Note.Accidental`    | int  | See below          |
| `tied=""`          | `Note.Tied`          | bool |                    |
| ❌ `notehead=""`   | `Note.NoteStyle`     | int  |                    |
| ❌ `color=""`      | `Note.Color`         | int  | 24-bit RGB         |

#### Accidental Values

| Mahlif | Sibelius      | Value |
| ------ | ------------- | ----- |
| (none) | `Natural`     | 0     |
| `#`    | `Sharp`       | 1     |
| `x`    | `DoubleSharp` | 2     |
| `b`    | `Flat`        | -1    |
| `bb`   | `DoubleFlat`  | -2    |

### Articulations

| Mahlif Value    | Index | Constant                    |
| --------------- | ----- | --------------------------- |
| `staccato`      | 1     | `StaccatoArticulation`      |
| `staccatissimo` | 2     | `StaccatissimoArticulation` |
| `wedge`         | 3     | `WedgeArticulation`         |
| `tenuto`        | 4     | `TenutoArticulation`        |
| `accent`        | 5     | `AccentArticulation`        |
| `marcato`       | 6     | `MarcatoArticulation`       |
| `harmonic`      | 7     | —                           |
| `plus`          | 8     | `PlusArticulation`          |
| `up-bow`        | 9     | `UpBowArticulation`         |
| `down-bow`      | 10    | `DownBowArticulation`       |
| `long-fermata`  | 12    | —                           |
| `fermata`       | 13    | `FermataArticulation`       |
| `short-fermata` | 14    | —                           |

### Clef Changes

| Mahlif XML      | Sibelius Property | Type   |
| --------------- | ----------------- | ------ |
| `<clef pos="">` | `Clef.Position`   | int    |
| `type=""`       | `Clef.StyleId`    | string |
| `dx=""`         | `Clef.Dx`         | int    |

### Key Signature

| Mahlif XML     | Sibelius Property       | Type           |
| -------------- | ----------------------- | -------------- |
| `<key pos="">` | `KeySignature.Position` | int            |
| `fifths=""`    | `KeySignature.Sharps`   | int (-7 to +7) |
| `mode=""`      | `KeySignature.Major`    | bool           |

### Time Signature

| Mahlif XML      | Sibelius Property           | Type |
| --------------- | --------------------------- | ---- |
| `<time pos="">` | `TimeSignature.Position`    | int  |
| `num=""`        | `TimeSignature.Numerator`   | int  |
| `den=""`        | `TimeSignature.Denominator` | int  |

### Text Objects

| Mahlif XML       | Sibelius Property    | Type   |
| ---------------- | -------------------- | ------ |
| `<text pos="">`  | `Text.Position`      | int    |
| `style=""`       | `Text.StyleId`       | string |
| (content)        | `Text.Text`          | string |
| `voice=""`       | `Text.VoiceNumber`   | int    |
| `dx=""`, `dy=""` | `Text.Dx`, `Text.Dy` | int    |

Dynamics are detected when `StyleId` contains "dynamic".

### Slurs

| Mahlif XML            | Sibelius Property   | Type |
| --------------------- | ------------------- | ---- |
| `<slur start-bar="">` | Current bar         | int  |
| `start-pos=""`        | `Slur.Position`     | int  |
| `end-bar=""`          | `Slur.EndBarNumber` | int  |
| `end-pos=""`          | `Slur.EndPosition`  | int  |
| `voice=""`            | `Slur.VoiceNumber`  | int  |

### Hairpins

| Mahlif XML               | Sibelius Type    |
| ------------------------ | ---------------- |
| `<hairpin type="cresc">` | `CrescendoLine`  |
| `<hairpin type="dim">`   | `DiminuendoLine` |

### Tuplets

| Mahlif XML              | Sibelius Property | Type |
| ----------------------- | ----------------- | ---- |
| `<tuplet start-bar="">` | Current bar       | int  |
| `start-pos=""`          | `Tuplet.Position` | int  |
| `num=""`                | `Tuplet.Left`     | int  |
| `den=""`                | `Tuplet.Right`    | int  |

### Octava Lines

| Mahlif XML         | Sibelius Property         | Type   |
| ------------------ | ------------------------- | ------ |
| `<octava type="">` | `OctavaLine.StyleId`      | string |
| `start-bar=""`     | Current bar               | int    |
| `start-pos=""`     | `OctavaLine.Position`     | int    |
| `end-bar=""`       | `OctavaLine.EndBarNumber` | int    |
| `end-pos=""`       | `OctavaLine.EndPosition`  | int    |

Types: `8va`, `8vb`, `15va`, `15vb`

### Pedal Lines

| Mahlif XML        | Sibelius Property        | Type |
| ----------------- | ------------------------ | ---- |
| `<pedal type="">` | `PedalLine`              | —    |
| `start-bar=""`    | Current bar              | int  |
| `start-pos=""`    | `PedalLine.Position`     | int  |
| `end-bar=""`      | `PedalLine.EndBarNumber` | int  |
| `end-pos=""`      | `PedalLine.EndPosition`  | int  |

Types: `sustain`

### Trills

| Mahlif XML             | Sibelius Property    | Type |
| ---------------------- | -------------------- | ---- |
| `<trill start-bar="">` | Current bar          | int  |
| `start-pos=""`         | `Trill.Position`     | int  |
| `end-bar=""`           | `Trill.EndBarNumber` | int  |
| `end-pos=""`           | `Trill.EndPosition`  | int  |

### Grace Notes

| Mahlif XML       | Sibelius Property                            | Type   |
| ---------------- | -------------------------------------------- | ------ |
| `<grace pos="">` | `GraceNote.Position`                         | int    |
| `type=""`        | `GraceNote.IsAcciaccatura`, `IsAppoggiatura` | string |
| `pitch=""`       | `GraceNote.Pitch`                            | int    |
| `dur=""`         | `GraceNote.Duration`                         | int    |

Types: `grace`, `acciaccatura`, `appoggiatura`

### Barlines

| Mahlif Value   | Sibelius Type |
| -------------- | ------------- |
| `single`       | 0             |
| `double`       | 1             |
| `final`        | 2             |
| `repeat-end`   | 3             |
| `repeat-start` | 4             |
| `repeat-both`  | 5             |
| `dashed`       | 6             |
| `invisible`    | 7             |

### Lyrics

| Mahlif XML     | Sibelius Property        | Type   |
| -------------- | ------------------------ | ------ |
| `<syl pos="">` | `LyricItem.Position`     | int    |
| (content)      | `LyricItem.Text`         | string |
| `hyphen=""`    | `LyricItem.SyllableType` | int    |
| `melisma=""`   | `LyricItem.SyllableType` | int    |

#### Syllable Types

| Type | Meaning                 |
| ---- | ----------------------- |
| 0    | End of word             |
| 1    | Middle (hyphen follows) |
| 2    | End with melisma        |
| 3    | Middle with melisma     |

### System Staff Objects

#### Tempo Markings

| Mahlif XML       | Sibelius Property         | Type   |
| ---------------- | ------------------------- | ------ |
| `<tempo pos="">` | `SystemTextItem.Position` | int    |
| `text=""`        | `SystemTextItem.Text`     | string |
| ❌ `bpm=""`      | —                         | —      |

#### Rehearsal Marks

| Mahlif XML           | Sibelius Property          | Type   |
| -------------------- | -------------------------- | ------ |
| `<rehearsal pos="">` | `RehearsalMark.Position`   | int    |
| (content)            | `RehearsalMark.MarkAsText` | string |
| `n=""`               | `RehearsalMark.Mark`       | int    |

### Position Offsets

All `BarObject`-derived objects support:

| Property | Unit                            |
| -------- | ------------------------------- |
| `Dx`     | 1/32nd staff space (horizontal) |
| `Dy`     | 1/32nd staff space (vertical)   |

### Supported Spanners/Lines

The export plugin handles these line types:

| Feature      | Mahlif Element                                   |
| ------------ | ------------------------------------------------ |
| Octava lines | `<octava type="8va/8vb/15va/15vb">`              |
| Pedal lines  | `<pedal type="sustain">`                         |
| Trills       | `<trill>`                                        |
| Grace notes  | `<grace type="grace/acciaccatura/appoggiatura">` |

### Not Yet Supported

| Feature            | Priority |
| ------------------ | -------- |
| Chord symbols      | Medium   |
| Glissandi          | Low      |
| Tremolo            | Medium   |
| Cross-staff notes  | Low      |
| Cue notes          | Low      |
| Ornaments          | Low      |
| Fingering          | Low      |
| Multi-bar rests    | Medium   |
| Instrument changes | Medium   |
