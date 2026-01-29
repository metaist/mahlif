# LilyPond

Mahlif converts to LilyPond format for high-quality PDF output.

| Direction | Status | Method |
|-----------|--------|--------|
| Mahlif → LilyPond | ✅ Working | CLI / Python API |
| LilyPond → Mahlif | ❌ Not planned | — |

## Quick Start

```bash
# Convert Mahlif XML to LilyPond
mahlif convert score.mahlif.xml score.ly

# Then compile with LilyPond
lilypond score.ly
```

### Python API

```python
from mahlif import parse
from mahlif.lilypond import to_lilypond

score = parse("score.mahlif.xml")
lily_source = to_lilypond(score)

with open("score.ly", "w") as f:
    f.write(lily_source)
```

## Feature Support

### Score Structure

| Feature | Status | LilyPond Output |
|---------|--------|-----------------|
| Version header | ✅ | `\version "2.24.0"` |
| Title/composer | ✅ | `\header { title = "..." }` |
| Page size | ✅ | `\paper { paper-width = ... }` |
| Staff names | ✅ | `\new Staff = "Violin"` |

### Notes and Rests

| Feature | Status | LilyPond Output |
|---------|--------|-----------------|
| Single notes | ✅ | `c'4` |
| Chords | ✅ | `<c' e' g'>4` |
| Rests | ✅ | `r4` |
| Hidden rests | ✅ | `s4` (spacer) |
| Ties | ✅ | `c'4~` |

### Durations

| Ticks | Duration | LilyPond |
|-------|----------|----------|
| 2048 | Breve | `\breve` |
| 1536 | Dotted whole | `1.` |
| 1024 | Whole | `1` |
| 768 | Dotted half | `2.` |
| 512 | Half | `2` |
| 384 | Dotted quarter | `4.` |
| 256 | Quarter | `4` |
| 192 | Dotted eighth | `8.` |
| 128 | Eighth | `8` |
| 96 | Dotted 16th | `16.` |
| 64 | 16th | `16` |
| 32 | 32nd | `32` |

### Clefs and Signatures

| Feature | Status | LilyPond Output |
|---------|--------|-----------------|
| Initial clef | ✅ | `\clef treble` |
| Clef changes | ✅ | `\clef bass` |
| Key signature | ✅ | `\key bes \major` |
| Key changes | ✅ | Mid-bar key changes |
| Time signature | ✅ | `\time 4/4` |

### Dynamics and Expression

| Feature | Status | LilyPond Output |
|---------|--------|-----------------|
| Dynamics | ✅ | `\p`, `\f`, `\ff`, `\mf`, etc. |
| Crescendo hairpin | ✅ | `\<` |
| Diminuendo hairpin | ✅ | `\>` |

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

### Barlines

| Type | Status | LilyPond |
|------|--------|----------|
| Single | ✅ | `|` |
| Double | ✅ | `\bar "||"` |
| Final | ✅ | `\bar "|."` |
| Repeat start | ✅ | `\bar ".|:"` |
| Repeat end | ✅ | `\bar ":|."` |

## Not Yet Implemented

### High Priority

| Feature | LilyPond | Notes |
|---------|----------|-------|
| Slurs | `( )` | Need start/end tracking |
| Tuplets | `\tuplet 3/2 { }` | Need grouping logic |
| Multi-voice | `<< { } \\ { } >>` | Need voice separation |
| Lyrics | `\lyricmode { }` | Need syllable alignment |
| Grace notes | `\grace`, `\acciaccatura` | |

### Medium Priority

| Feature | LilyPond | Notes |
|---------|----------|-------|
| Text annotations | `^"text"` | |
| Rehearsal marks | `\mark "A"` | |
| Tempo markings | `\tempo 4 = 120` | |
| System breaks | `\break` | |
| Staff groups | `\new StaffGroup` | |
| Grand staff | `\new PianoStaff` | |
| Transposition | `\transpose c bes` | |

### Layout/Positioning

| Feature | Notes |
|---------|-------|
| dx/dy offsets | Pixel-accurate positioning |
| Staff spacing | `\override VerticalAxisGroup` |
| Note spacing | `\override SpacingSpanner` |

## Known Limitations

1. **Empty bars** show as `|` instead of whole-bar rests
2. **Long lines** — each staff is one line (no wrapping)
3. **Enharmonic spelling** may differ from original
4. **Time signatures** only appear when they change

## Export Statistics

From a test orchestral score:

| Metric | Count |
|--------|-------|
| Staves | 36 |
| Notes | 15,466 |
| Chords | 4,740 |
| Dynamics | 1,230 |
| Slurs | 1,248 |
| Hairpins | 333 |
| Key changes | 261 |
| Clef changes | 19 |
