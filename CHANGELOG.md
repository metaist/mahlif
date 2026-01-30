# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog] and this project adheres to [Semantic Versioning].

Sections order is: `Fixed`, `Changed`, `Added`, `Deprecated`, `Removed`, `Security`.

[keep a changelog]: http://keepachangelog.com/en/1.1.0/
[semantic versioning]: http://semver.org/spec/v2.0.0.html

---

## [Unreleased]

[unreleased]: https://github.com/metaist/mahlif/compare/prod...main

These are changes that are on `main` that are not yet in `prod`.

**Fixed**

- [#1] UTF-16 encoding for Cyrillic/Unicode text preservation
- [#1] Barline type mapping in export plugin (use `BarlineType` string property)
- [#1] Generic instrument types prevent Sibelius from reordering staves
- [#1] Slur end positions normalized between import/export
- Parser validates root element (`<mahlif>` required)
- Tempo and rehearsal marks parsed from system staff
- Unmocked AppleScript calls prevented in test suite

[#1]: https://github.com/metaist/mahlif/issues/1
[#2]: https://github.com/metaist/mahlif/issues/2
[#3]: https://github.com/metaist/mahlif/issues/3
[#6]: https://github.com/metaist/mahlif/issues/6
[#10]: https://github.com/metaist/mahlif/issues/10

**Added**

- Mahlif XML schema for universal music notation interchange (`docs/schema.md`)
- [#1] **Sibelius Export Plugin** (`MahlifExport.plg`)
  - Notes, chords, rests with duration and voice
  - Dynamics and hairpins (crescendo/diminuendo)
  - Slurs with cross-bar support
  - Key signatures, time signatures, clef changes
  - Articulations (staccato, accent, fermata, etc.)
  - Lyrics with syllable types (hyphen, melisma)
  - Text annotations with style preservation
  - Tempo markings and rehearsal marks
  - Octava lines (8va, 8vb, 15ma, 15mb)
  - Pedal markings
  - Trills
  - Grace notes (acciaccatura, appoggiatura)
  - Special barlines (double, final, repeat)
  - Page/system breaks
  - Position offsets (dx/dy) for layout preservation
- [#1] **Sibelius Import** via generated ManuScript plugin
  - Python generates `.plg` from Mahlif XML
  - All export features supported in reverse
  - Generic instrument types to preserve staff order
  - Round-trip tested (export → import → export)
- [#6] **ManuScript Linter** for Sibelius plugins
  - Brace matching and syntax validation
  - Undefined variable detection (MS-W020)
  - Unused variable warnings (MS-W025)
  - Reserved word detection (MS-W001)
  - Potentially negative loop bounds (MS-W021)
  - Unescaped double quotes in strings (MS-E050)
  - Inline suppression comments (`// noqa: MS-W001`)
  - Config file support (`mahlif.toml`)
  - `--strict` and `--error` flags
- [#6] **ManuScript Formatter** for consistent code style
  - 4-space indentation
  - Trailing whitespace removal
  - Normalized blank lines around methods
- **Sibelius Automation** module for macOS
  - AppleScript-based UI control
  - Plugin reload without restart
  - Blank score creation
  - Modal detection and dismissal
  - State machine architecture
- [#3] **CLI Commands**
  - `mahlif convert` - Convert between formats
  - `mahlif sibelius build` - Build plugins with lint/format
  - `mahlif sibelius install` - Install plugins to Sibelius
  - `mahlif sibelius check` - Lint plugin files
  - `mahlif sibelius format` - Format plugin files
  - `mahlif sibelius list` - List available plugins
  - `mahlif manuscript` - Alias for `sibelius` subcommand
  - `mahlif stats` - Show score statistics
- Python parser for Mahlif XML files
- [#2] LilyPond converter (basic output)
- [#6] ManuScript language data (`lang.json`) with builtins and constants
- [#10] Cyrus plugin for IPA syllable fixing (experimental)
- Comprehensive test suite (820 tests, 100% coverage)
