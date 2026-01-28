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
> Not recommended for production use. Expect bugs and incomplete features.

## Why?

Music notation software stores scores in proprietary formats that don't interoperate well. MusicXML exists but loses layout precision. Mahlif provides:

1. **Mahlif XML** — An intermediate format that preserves pixel-accurate layout (dx/dy offsets)
2. **Bidirectional converters** for Sibelius, Finale, Dorico, LilyPond, and MusicXML

Current focus: Sibelius → Mahlif XML → LilyPond → PDF

## Install

```bash
pip install mahlif
# or
uv add mahlif
```

## Usage

### Export from Sibelius

1. Copy `plugins/sibelius/MahlifExportFull.plg` to your Sibelius plugins folder:
   - **Mac**: `~/Library/Application Support/Avid/Sibelius/Plugins/Other/`
   - **Windows**: `%APPDATA%\Avid\Sibelius\Plugins\Other\`
2. Convert to UTF-16 BE (required by Sibelius):
   ```bash
   iconv -f UTF-8 -t UTF-16BE MahlifExportFull.plg > temp.plg
   printf '\xfe\xff' > MahlifExportFull.plg
   cat temp.plg >> MahlifExportFull.plg
   ```
3. Restart Sibelius
4. Home → Plug-ins → Other → Export to Mahlif XML (Full)
5. Save the `.xml` file

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

## License

[MIT License](https://github.com/metaist/mahlif/blob/main/LICENSE.md)
