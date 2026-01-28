# LilyPond Conversion Support

This document describes what Mahlif XML features are currently supported when converting to LilyPond format.

## Conversion Summary

The LilyPond converter (`mahlif.lilypond.to_lilypond()`) transforms a parsed Mahlif `Score` object into LilyPond source code.

### Export Statistics (from test score)

- **Staves**: 36 orchestral parts
- **Notes**: 15,466 individual notes
- **Chords**: 4,740 chord events
- **Dynamics**: 1,230 dynamic markings
- **Slurs**: 1,248 slur markings
- **Hairpins**: 333 crescendo/diminuendo markings
- **Key Changes**: 261 mid-piece key signature changes
- **Clef Changes**: 19 mid-piece clef changes

## Currently Supported ✅

### Score Structure

- [x] `\version` header (2.24.0)
- [x] `\header` block (title, composer, poet, arranger, copyright)
- [x] `\paper` block (custom page size)
- [x] `\score` with `<<` `>>` simultaneous music
- [x] `\new Staff` with name from instrument

### Notation Elements

| Feature | Status | Notes |
|---------|--------|-------|
| Single notes | ✅ | Pitch + duration |
| Chords | ✅ | `<c e g>4` syntax |
| Rests | ✅ | `r4`, `r2`, etc. |
| Hidden/spacer rests | ✅ | `s4` for invisible rests |
| Ties | ✅ | `~` appended to notes |
| Clef (initial) | ✅ | treble, bass, alto, tenor |
| Clef changes | ✅ | `\clef bass` mid-staff |
| Key signature (initial) | ✅ | `\key bes \major` |
| Key signature changes | ✅ | Key changes within bars |
| Time signature | ✅ | `\time 4/4` |
| Dynamics | ✅ | `\p`, `\f`, `\ff`, `\mf`, etc. |
| Hairpins (cresc) | ✅ | `\<` |
| Hairpins (dim) | ✅ | `\>` |
| Bar lines (single) | ✅ | `|` |
| Double bar | ✅ | `\bar "||"` |
| Final bar | ✅ | `\bar "|."` |
| Repeat start | ✅ | `\bar ".|:"` |
| Repeat end | ✅ | `\bar ":|."` |

### Articulations

| Articulation | Status | LilyPond |
|--------------|--------|----------|
| Staccato | ✅ | `-.` |
| Staccatissimo | ✅ | `-!` |
| Tenuto | ✅ | `--` |
| Accent | ✅ | `->` |
| Marcato | ✅ | `-^` |
| Fermata | ✅ | `\fermata` |
| Long fermata | ✅ | `\longfermata` |
| Short fermata | ✅ | `\shortfermata` |
| Up bow | ✅ | `\upbow` |
| Down bow | ✅ | `\downbow` |
| Harmonic | ✅ | `\flageolet` |
| Trill | ✅ | `\trill` |
| Arpeggio | ✅ | `\arpeggio` |

### Durations Supported

| Ticks | Duration | LilyPond |
|-------|----------|----------|
| 64 | 16th | `16` |
| 96 | dotted 16th | `16.` |
| 128 | 8th | `8` |
| 192 | dotted 8th | `8.` |
| 256 | quarter | `4` |
| 384 | dotted quarter | `4.` |
| 512 | half | `2` |
| 768 | dotted half | `2.` |
| 1024 | whole | `1` |
| 1536 | dotted whole | `1.` |
| 2048 | breve | `\breve` |

## Not Yet Implemented 🚧

### High Priority

- [ ] **Slurs**: `(` and `)` around slurred passages
- [ ] **Tuplets**: `\tuplet 3/2 { ... }` for triplets etc.
- [ ] **Multi-voice**: `<< { voice1 } \\ { voice2 } >>`
- [ ] **Lyrics**: `\lyricmode { ... }`
- [ ] **Grace notes**: `\grace`, `\acciaccatura`, `\appoggiatura`
- [ ] **Tremolo**: `\repeat tremolo`
- [ ] **Glissando/portamento**: `\glissando`
- [ ] **Ottava**: `\ottava #1`

### Medium Priority

- [ ] **Text annotations**: `^"text"` or `_"text"`
- [ ] **Rehearsal marks**: `\mark \default` or `\mark "A"`
- [ ] **Tempo markings**: `\tempo "Allegro" 4 = 120`
- [ ] **System/page breaks**: `\break`, `\pageBreak`
- [ ] **Staff groups**: `\new StaffGroup <<...>>`
- [ ] **Grand staff**: `\new PianoStaff <<...>>`
- [ ] **Transposing instruments**: `\transpose c bes`
- [ ] **Instrument changes**: Mid-staff instrument switches

### Layout/Positioning

- [ ] **dx/dy offsets**: Pixel-accurate positioning
- [ ] **Staff spacing**: `\override Staff.VerticalAxisGroup`
- [ ] **System margins**: `\paper { system-system-spacing }`
- [ ] **Note spacing**: `\override SpacingSpanner`

## Known Issues

1. **Empty bars**: Bars without content show as just `|` - should output whole-bar rests
2. **Long lines**: Each staff's content is on one line - should wrap for readability
3. **Enharmonic spelling**: Some notes may have unexpected accidentals (e.g., `des` vs `cis`)
4. **Missing time signatures**: Time signatures only output when they change

## Usage Example

```python
from mahlif.parser import parse
from mahlif.lilypond import to_lilypond

# Parse Mahlif XML
score = parse("score.mahlif.xml")

# Convert to LilyPond
lily_source = to_lilypond(score)

# Save to file
with open("score.ly", "w") as f:
    f.write(lily_source)
```

## Future Work

1. **Slur tracking**: Track slur start/end by position and voice
2. **Tuplet grouping**: Collect notes within tuplet spans
3. **Multi-movement scores**: Separate `\score` blocks per movement
4. **Part extraction**: Generate individual part files
5. **MIDI output**: `\midi { }` block for playback
