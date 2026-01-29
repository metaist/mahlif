# ManuScript Language Data

This directory contains data about the ManuScript language for linting, 
code completion, and eventually an LSP server.

## Data Files

### `api.json` - Method Signatures
Extracted from the ManuScript Language PDF. Contains method names with
parameter counts (min/max).

```json
{
  "methods": {
    "AddNote": {"min_params": 3, "max_params": 5, "params": ["pos", "pitch", "dur", "tied?", "voice?"]}
  }
}
```

### `constants.json` - Global Constants (TODO)
Global constants defined by ManuScript. Reference: ManuScript Language Guide, 
Chapter 7 "Global Constants" (pages clxxxi-ccxvi).

Categories:
- **Truth Values**: `True` (1), `False` (0)
- **Measurements**: `Space` (32), `StaffHeight` (128)
- **Positions and Durations**: `Whole` (1024), `Quarter` (256), `Eighth` (128), etc.
- **Style Names**: `House`, `AllStyles`, etc.
- **Text Styles**: `"text.staff.expression"`, `"text.system.tempo"`, etc.
- **Line Styles**: Arpeggio, Slur, Hairpin styles
- **Clef Styles**: `"clef.treble"`, `"clef.bass"`, etc.
- **Instrument Types**: Various instrument type constants
- **SyllableTypes**: `MiddleOfWord`, `EndOfWord`, `StartOfWord`, `SingleSyllable`
- ... and many more

<!-- cspell:ignore clxxxi ccxvi -->

### `objects.json` - Object Types (TODO)
Object types with their methods and properties. This would enable:
- Property completion after `.`
- Method signature help
- Type checking

```json
{
  "objects": {
    "Bar": {
      "methods": ["AddNote", "AddText", "NthBar", ...],
      "properties": ["Length", "BarNumber", ...]
    },
    "Staff": {
      "methods": ["NthBar", ...],
      "properties": ["Instrument", "FullName", "ShortName", ...]
    }
  }
}
```

## Built-in Globals

Defined in `checker.py`:BUILTIN_GLOBALS`:
- `Sibelius` - Main application object
- `Self` - Current plugin context
- Built-in functions: `CreateSparseArray`, `Trace`, `Chr`, `Asc`, etc.
- Syllable constants: `MiddleOfWord`, `EndOfWord`, etc.

## Future: LSP Architecture

```
mahlif-lsp/
├── server.py           # LSP server implementation
├── completions.py      # Code completion
├── diagnostics.py      # Uses lint/ for diagnostics
├── hover.py           # Documentation on hover
├── signatures.py      # Method signature help
└── data/
    ├── api.json       # Method signatures
    ├── constants.json # Global constants
    └── objects.json   # Object types
```

## Data Extraction

The data is extracted from `_ignore_data/ManuScript Language.pdf` using:
- `api.py` - Extracts method signatures
- Future: Script to extract constants and object definitions

Run extraction:
```bash
pdftotext "ManuScript Language.pdf" - | python api.py > api.json
```
