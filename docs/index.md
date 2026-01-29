# mahlif

Universal music notation interchange format with bidirectional converters.

**מַחֲלִיף** (machalif/mahlif) = Hebrew for "exchanger/converter"

> [!WARNING]
> **Experimental / Pre-release Software**
>
> This project is in early development. APIs may change without notice.

## Why Mahlif?

Music notation software stores scores in proprietary formats that don't interoperate well. MusicXML exists but loses layout precision. Mahlif provides:

1. **Mahlif XML** — An intermediate format preserving pixel-accurate layout (dx/dy offsets)
2. **Bidirectional converters** for notation software

## Install

```bash
pip install mahlif
# or
uv add mahlif
```

## Format Support

| Format | Import | Export | Notes |
|--------|--------|--------|-------|
| [Sibelius](sibelius.md) | ✅ Plugin | 🚧 Plugin | Export ~80% complete |
| [LilyPond](lilypond.md) | — | ✅ CLI | ~70% features |
| MusicXML | ❌ | ❌ | Planned |
| Finale | ❌ | ❌ | Planned |
| Dorico | ❌ | ❌ | Planned |

Current focus: **Sibelius → Mahlif XML → LilyPond → PDF**

## Quick Start

### Export from Sibelius

```bash
# Install the export plugin
mahlif sibelius build --install
```

Then in Sibelius: **Home → Plug-ins → Mahlif → Export to Mahlif XML**

### Convert to LilyPond

```bash
# Convert to LilyPond source
mahlif convert score.mahlif.xml score.ly

# Compile to PDF (requires LilyPond installed)
lilypond score.ly
```

### Python API

```python
from mahlif import parse
from mahlif.lilypond import to_lilypond

score = parse("score.mahlif.xml")
lily_source = to_lilypond(score)
```

## Documentation

- [CLI Reference](cli.md) — Command-line interface
- [Sibelius](sibelius.md) — Plugin installation, workflow, property mapping
- [LilyPond](lilypond.md) — Export features and limitations
- [Schema](schema.md) — Mahlif XML format specification

## Links

- [GitHub Repository](https://github.com/metaist/mahlif)
- [PyPI Package](https://pypi.org/project/mahlif/)
- [Issue Tracker](https://github.com/metaist/mahlif/issues)
