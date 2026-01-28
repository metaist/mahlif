# mahlif

Universal music notation interchange format with bidirectional converters.

**מַחֲלִיף** (machalif/mahlif) = Hebrew for "exchanger/converter"

> [!WARNING]
> **Experimental / Pre-release Software**
>
> This project is in early development. APIs may change without notice.
> Not recommended for production use. Expect bugs and incomplete features.

## Install

```bash
pip install mahlif
# or
uv add mahlif
```

## Quick Start

### Export from Sibelius

1. Copy `plugins/sibelius/MahlifExportFull.plg` to your Sibelius plugins folder
2. In Sibelius: Home → Plug-ins → Other → Export to Mahlif XML (Full)
3. Save the `.xml` file

### Convert to LilyPond

```bash
mahlif convert score.xml -o score.ly
mahlif render score.xml -o score.pdf
```

### Python API

```python
from mahlif import parse, to_lilypond

score = parse("score.xml")
lilypond_code = to_lilypond(score)
```

## Why?

Music notation software stores scores in proprietary formats that don't interoperate well. MusicXML exists but loses layout precision. Mahlif provides:

1. **Mahlif XML** — An intermediate format that preserves pixel-accurate layout (dx/dy offsets)
2. **Bidirectional converters** for Sibelius, Finale, Dorico, LilyPond, and MusicXML

Current focus: Sibelius → Mahlif XML → LilyPond → PDF
