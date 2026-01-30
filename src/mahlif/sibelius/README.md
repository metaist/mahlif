# Mahlif Plugin for Sibelius

Bidirectional Sibelius ↔ Mahlif XML conversion.

- **Export**: Sibelius → Mahlif XML ✅
- **Import**: Mahlif XML → Sibelius 🚧 (in progress)

## Installation

### Via CLI (recommended)

```bash
mahlif install sibelius
```

### Manual Installation

1. Build the plugin (converts UTF-8 to UTF-16 BE):
   ```bash
   ./build.sh
   ```
2. Copy `dist/MahlifExport.plg` to your Sibelius plugins folder:
   - **Mac**: `~/Library/Application Support/Avid/Sibelius/Plugins/`
   - **Windows**: `%APPDATA%\Avid\Sibelius\Plugins\`
3. Restart Sibelius
4. The plugin appears in the **Plug-ins** menu

## Usage

1. Open a score in Sibelius
2. Go to **Plug-ins → Mahlif Export**
3. Choose a location to save the `.xml` file
4. Click **Save**

## What's Exported

### Fully Supported

- Notes, rests, chords (with pitches, durations, ties)
- Articulations (staccato, accent, fermata, etc.)
- Dynamics (f, p, mf, mp, etc.)
- Slurs, hairpins (crescendo/diminuendo)
- Clefs, key signatures, time signatures
- Tempo markings
- Rehearsal marks
- Text (expressions, technique, etc.)
- Lyrics (multiple verses)
- Tuplets
- Barlines (double, final, repeats, etc.)
- Ottava lines (8va, 8vb, 15va, 15vb)
- Position offsets (dx, dy)

### Partially Supported

- Grace notes (TODO)
- Trills (basic support)
- Arpeggios (basic support)
- Pedal markings (TODO)
- Chord symbols (TODO)
- Page/system breaks (exported, may need testing across Sibelius versions)
- Multi-movement works (detected via final barlines + movement title text)

### Not Yet Supported

- Fingerings
- Figured bass
- Guitar bend/slide
- Ossia staves
- Cue notes

## Requirements

- Sibelius 7 or later

## License

MIT License
