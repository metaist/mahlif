# mahlif: Universal Music Notation Interchange Format

<p align="center">
  <a href="https://github.com/metaist/mahlif/actions/workflows/ci.yaml"><img alt="Build" src="https://img.shields.io/github/actions/workflow/status/metaist/mahlif/.github/workflows/ci.yaml?branch=main&logo=github"/></a>
  <a href="https://pypi.org/project/mahlif"><img alt="PyPI" src="https://img.shields.io/pypi/v/mahlif.svg?color=blue" /></a>
  <a href="https://pypi.org/project/mahlif"><img alt="Supported Python Versions" src="https://img.shields.io/pypi/pyversions/mahlif" /></a>
</p>

**מַחֲלִיף** (machalif/mahlif) = Hebrew for "exchanger/converter"

> [!WARNING]
> **Experimental / Pre-release Software**
>
> This project is in early development. APIs may change without notice.

## Why Mahlif?

Music notation software stores scores in proprietary formats that don't interoperate well. MusicXML exists but loses layout precision. Mahlif provides:

1. **Mahlif XML** — An intermediate format preserving pixel-accurate layout (dx/dy offsets)
2. **Bidirectional converters** for notation software

<!--[[[cog
# Format support matrix is maintained in docs/index.md
# Run: cog -r README.md
import cog
cog.outl("## Format Support")
cog.outl("")
cog.outl("| Format | Import | Export | Notes |")
cog.outl("|--------|--------|--------|-------|")
cog.outl("| Sibelius | ✅ Plugin | 🚧 Plugin | Export ~80% complete |")
cog.outl("| LilyPond | — | ✅ CLI | ~70% features |")
cog.outl("| MusicXML | ❌ | ❌ | Planned |")
cog.outl("| Finale | ❌ | ❌ | Planned |")
cog.outl("| Dorico | ❌ | ❌ | Planned |")
]]]-->

## Format Support

| Format   | Import    | Export    | Notes                |
| -------- | --------- | --------- | -------------------- |
| Sibelius | ✅ Plugin | 🚧 Plugin | Export ~80% complete |
| LilyPond | —         | ✅ CLI    | ~70% features        |
| MusicXML | ❌        | ❌        | Planned              |
| Finale   | ❌        | ❌        | Planned              |
| Dorico   | ❌        | ❌        | Planned              |

<!--[[[end]]]-->

Current focus: **Sibelius → Mahlif XML → LilyPond → PDF**

## Install

```bash
pip install mahlif
# or
uv add mahlif
```

## Quick Start

### Export from Sibelius

```bash
# Install the export plugin
mahlif sibelius install
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

See the [full documentation](docs/index.md) for:

- [CLI Reference](docs/cli.md) — All commands and options
- [Sibelius](docs/sibelius.md) — Plugin installation, linter, property mapping
- [LilyPond](docs/lilypond.md) — Export features and limitations
- [Schema](docs/schema.md) — Mahlif XML format specification

## License

[MIT License](LICENSE.md)
