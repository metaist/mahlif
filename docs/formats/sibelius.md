# Sibelius Export Mapping

This document maps Mahlif XML elements to Sibelius ManuScript API properties.
Properties are verified against the official ManuScript Language Guide (2024).

> [!NOTE]
> Properties marked with ❌ are not yet implemented in the export plugin.
> Properties marked with ⚠️ have partial support or caveats.

## Score Metadata

| Mahlif XML | Sibelius Property | Type | Notes |
|------------|-------------------|------|-------|
| `<work-title>` | `Score.Title` | string | read/write |
| `<composer>` | `Score.Composer` | string | read/write |
| `<lyricist>` | `Score.Lyricist` | string | read/write |
| `<arranger>` | `Score.Arranger` | string | read/write |
| `<copyright>` | `Score.Copyright` | string | read/write |
| `<publisher>` | `Score.Publisher` | string | read/write |
| `<source-file>` | `Score.FileName` | string | read only |
| `<source-format>` | `Sibelius.ProgramVersion` | int | Version × 1000 |
| ❌ `<opus>` | `Score.OpusNumber` | string | Not exported |
| ❌ `<dedication>` | `Score.Dedication` | string | Not exported |
| ❌ `<duration-ms>` | `Score.ScoreDuration` | int | Milliseconds, read only |

## Page Layout

Accessed via `Score.DocumentSetup` object. Units default to millimeters.

| Mahlif XML | Sibelius Property | Type | Notes |
|------------|-------------------|------|-------|
| `<page width="">` | `DocumentSetup.PageWidth` | float | In mm by default |
| `<page height="">` | `DocumentSetup.PageHeight` | float | In mm by default |
| `<staff-height>` | `DocumentSetup.StaffSize` | float | In mm |
| ❌ `<margins>` | `DocumentSetup.PageTopMargin` etc. | float | Not exported |
| ❌ `<orientation>` | `DocumentSetup.Orientation` | int | 0=portrait, 1=landscape |

## Staff Properties

| Mahlif XML | Sibelius Property | Type | Notes |
|------------|-------------------|------|-------|
| `<staff n="">` | `Staff.StaffNum` | int | 1-indexed |
| `instrument=""` | `Staff.InstrumentName` | string | Full name |
| `instrument-short=""` | `Staff.ShortInstrumentName` | string | Abbreviated |
| `clef=""` | `Staff.InitialClefStyleId` | string | e.g., "clef.treble" |
| `key-sig=""` | `Staff.InitialKeySignature` | KeySignature | Object, not int |
| ❌ `lines=""` | Via `InstrumentType` | int | Requires instrument lookup |
| ❌ `transposition=""` | Via `InstrumentType` | int | Semitones |

### Clef Style IDs

| Mahlif Value | Sibelius StyleId |
|--------------|------------------|
| `treble` | `clef.treble` or `clef.g` |
| `bass` | `clef.bass` or `clef.f` |
| `alto` | `clef.alto` or `clef.c` |
| `tenor` | `clef.tenor` |
| `treble-8vb` | `clef.treble.down.8` or `clef.g.down.8` |
| `treble-8va` | `clef.treble.up.8` or `clef.g.up.8` |
| `bass-8vb` | `clef.bass.down.8` |
| `bass-8va` | `clef.bass.up.8` |
| `percussion` | `clef.percussion` |

## Bar Properties

| Mahlif XML | Sibelius Property | Type | Notes |
|------------|-------------------|------|-------|
| `<bar n="">` | `Bar.BarNumber` | int | Internal bar number, 1-indexed |
| `length=""` | `Bar.Length` | int | In 1/256th quarter notes |
| `break=""` | Via objects in bar | string | Check for SystemBreak/PageBreak objects |

## NoteRest Properties

A `NoteRest` contains zero or more `Note` objects. Zero notes = rest.

| Mahlif XML | Sibelius Property | Type | Notes |
|------------|-------------------|------|-------|
| `pos=""` | `NoteRest.Position` | int | Position in bar (1/256th quarters) |
| `dur=""` | `NoteRest.Duration` | int | Duration (1/256th quarters) |
| `voice=""` | `NoteRest.VoiceNumber` | int | 1-4 |
| `hidden=""` | `NoteRest.Hidden` | bool | ⚠️ Accessed via BarObject |
| `dx=""` | `NoteRest.Dx` | int | Horizontal offset (1/32nd space) |
| `dy=""` | `NoteRest.Dy` | int | Vertical offset (1/32nd space) |
| `stem=""` | `NoteRest.StemFlipped` | bool | true = stem is flipped; no `Stemless` property exists |
| `beam=""` | `NoteRest.Beam` | int | 0=none, 1=start, 2=continue, 3=end |
| ❌ `grace=""` | `NoteRest.GraceNote` | bool | read only |
| ❌ `cue=""` | — | — | Not directly accessible |

### Duration Values

| Duration | Ticks (1/256th quarter) |
|----------|------------------------|
| Whole note | 1024 |
| Half note | 512 |
| Quarter note | 256 |
| Eighth note | 128 |
| 16th note | 64 |
| 32nd note | 32 |
| Dotted = base × 1.5 | e.g., dotted quarter = 384 |

## Note Properties

Individual notes within a NoteRest (chord).

| Mahlif XML | Sibelius Property | Type | Notes |
|------------|-------------------|------|-------|
| `pitch=""` | `Note.Pitch` | int | MIDI pitch, 60 = middle C |
| `written-pitch=""` | `Note.WrittenPitch` | int | For transposing instruments |
| `diatonic=""` | `Note.DiatonicPitch` | int | 35 = middle C, +7 per octave |
| `accidental=""` | `Note.Accidental` | int | See accidental constants |
| `tied=""` | `Note.Tied` | bool | Tied to next note |
| ❌ `notehead=""` | `Note.NoteStyle` | int | Notehead style index |
| ❌ `color=""` | `Note.Color` | int | 24-bit RGB |

### Accidental Values

| Mahlif Value | Sibelius Constant | Numeric |
|--------------|-------------------|---------|
| (none) | `Natural` | 0 |
| `#` | `Sharp` | 1 |
| `x` | `DoubleSharp` | 2 |
| `b` | `Flat` | -1 |
| `bb` | `DoubleFlat` | -2 |

## Articulations

Accessed via `NoteRest.GetArticulation(n)` where n is the articulation index.

| Mahlif Value | Sibelius Index | Constant |
|--------------|----------------|----------|
| `staccato` | 1 | `StaccatoArticulation` |
| `staccatissimo` | 2 | `StaccatissimoArticulation` |
| `wedge` | 3 | `WedgeArticulation` |
| `tenuto` | 4 | `TenutoArticulation` |
| `accent` | 5 | `AccentArticulation` |
| `marcato` | 6 | `MarcatoArticulation` |
| `harmonic` | 7 | — |
| `plus` | 8 | `PlusArticulation` |
| `up-bow` | 9 | `UpBowArticulation` |
| `down-bow` | 10 | `DownBowArticulation` |
| `long-fermata` | 12 | — |
| `fermata` | 13 | `FermataArticulation` |
| `short-fermata` | 14 | — |

## Clef Changes

| Mahlif XML | Sibelius Property | Type | Notes |
|------------|-------------------|------|-------|
| `<clef pos="">` | `Clef.Position` | int | Position in bar |
| `type=""` | `Clef.StyleId` | string | See clef styles above |
| `dx=""` | `Clef.Dx` | int | Horizontal offset |

## Key Signature

| Mahlif XML | Sibelius Property | Type | Notes |
|------------|-------------------|------|-------|
| `<key pos="">` | `KeySignature.Position` | int | Position in bar |
| `fifths=""` | `KeySignature.Sharps` | int | -7 to +7 |
| `mode=""` | `KeySignature.Major` | bool | true = major |

## Time Signature

| Mahlif XML | Sibelius Property | Type | Notes |
|------------|-------------------|------|-------|
| `<time pos="">` | `TimeSignature.Position` | int | Position in bar |
| `num=""` | `TimeSignature.Numerator` | int | Top number |
| `den=""` | `TimeSignature.Denominator` | int | Bottom number |

## Text Objects

Text objects are typed by their `StyleId`.

| Mahlif XML | Sibelius Property | Type | Notes |
|------------|-------------------|------|-------|
| `<text pos="">` | `Text.Position` | int | Position in bar |
| `style=""` | `Text.StyleId` | string | Text style identifier |
| (content) | `Text.Text` | string | The text content |
| `voice=""` | `Text.VoiceNumber` | int | 1-4 |
| `dx=""` | `Text.Dx` | int | Horizontal offset |
| `dy=""` | `Text.Dy` | int | Vertical offset |

### Dynamic Detection

Dynamics are detected by checking if the `StyleId` contains "dynamic" or "Dynamic".
Common dynamic styles include `text.staff.expression`.

| Mahlif XML | Detection Method |
|------------|------------------|
| `<dynamic>` | `StyleId` contains "dynamic" |

## Spanners (Lines)

### Slurs

| Mahlif XML | Sibelius Property | Type | Notes |
|------------|-------------------|------|-------|
| `<slur start-bar="">` | Current bar number | int | Bar containing slur start |
| `start-pos=""` | `Slur.Position` | int | Start position |
| `end-bar=""` | `Slur.EndBarNumber` | int | Bar containing slur end |
| `end-pos=""` | `Slur.EndPosition` | int | End position |
| `voice=""` | `Slur.VoiceNumber` | int | 1-4 |

### Hairpins

Sibelius distinguishes `CrescendoLine` and `DiminuendoLine` as separate types.

| Mahlif XML | Sibelius Type | Notes |
|------------|---------------|-------|
| `<hairpin type="cresc">` | `CrescendoLine` | |
| `<hairpin type="dim">` | `DiminuendoLine` | |

Same properties as slurs: `Position`, `EndBarNumber`, `EndPosition`, `VoiceNumber`.

## Tuplets

| Mahlif XML | Sibelius Property | Type | Notes |
|------------|-------------------|------|-------|
| `<tuplet start-bar="">` | Current bar number | int | |
| `start-pos=""` | `Tuplet.Position` | int | |
| `num=""` | `Tuplet.Left` | int | Actual notes played |
| `den=""` | `Tuplet.Right` | int | In the time of |

## Barlines

Found as `SpecialBarline` objects in the system staff.

| Mahlif XML | Sibelius Property | Type | Notes |
|------------|-------------------|------|-------|
| `<barline pos="">` | `SpecialBarline.Position` | int | Usually 0 |
| `type=""` | `SpecialBarline.BarlineInternalType` | int | See below |

### Barline Types

| Mahlif Value | Sibelius Internal Type |
|--------------|----------------------|
| `single` | 0 |
| `double` | 1 |
| `final` | 2 |
| `repeat-end` | 3 |
| `repeat-start` | 4 |
| `repeat-both` | 5 |
| `dashed` | 6 |
| `invisible` | 7 |

## Lyrics

Found as `LyricItem` objects attached to notes.

| Mahlif XML | Sibelius Property | Type | Notes |
|------------|-------------------|------|-------|
| `<syl pos="">` | `LyricItem.Position` | int | Position in bar |
| (content) | `LyricItem.Text` | string | Syllable text |
| `hyphen=""` | `LyricItem.SyllableType` | int | See below |
| `melisma=""` | `LyricItem.SyllableType` | int | See below |

### Syllable Types

| SyllableType | Meaning | Mahlif |
|--------------|---------|--------|
| 0 | End of word | hyphen=false, melisma=false |
| 1 | Middle of word (hyphen follows) | hyphen=true |
| 2 | End of word with melisma | melisma=true |
| 3 | Middle of word with melisma | hyphen=true, melisma=true |

Verse number is extracted from `StyleId` (e.g., "verse1", "verse2").

## System Staff Objects

The system staff (`Score.SystemStaff`) contains score-wide objects.

### Tempo Markings

Detected by `StyleId` containing "tempo" or "Tempo".

| Mahlif XML | Sibelius Property | Type | Notes |
|------------|-------------------|------|-------|
| `<tempo pos="">` | `SystemTextItem.Position` | int | |
| `text=""` | `SystemTextItem.Text` | string | |
| `dx=""` | `SystemTextItem.Dx` | int | |
| `dy=""` | `SystemTextItem.Dy` | int | |
| ❌ `bpm=""` | — | — | Not directly accessible |

### Rehearsal Marks

Can be `RehearsalMark` objects or `SystemTextItem` with rehearsal style.

| Mahlif XML | Sibelius Property | Type | Notes |
|------------|-------------------|------|-------|
| `<rehearsal pos="">` | `RehearsalMark.Position` | int | |
| (content) | `RehearsalMark.MarkAsText` | string | Visible text (not `.Text`) |
| `n=""` | `RehearsalMark.Mark` | int | Internal number (0-indexed) |

## Position Offsets (dx/dy)

All `BarObject`-derived objects support position offsets:

| Property | Unit | Notes |
|----------|------|-------|
| `Dx` | 1/32nd of a staff space | Horizontal offset |
| `Dy` | 1/32nd of a staff space | Vertical offset |

A staff space is the distance between two adjacent staff lines (typically ~1.75mm for standard notation).

## Not Yet Supported

The following Sibelius features are not yet exported:

| Feature | Sibelius Object/Property | Priority |
|---------|-------------------------|----------|
| Chord symbols | `GuitarFrame` | Medium |
| Octava lines | `OctavaLine` | Medium |
| Pedal lines | `Line` (pedal style) | Low |
| Trills | `Trill` | Medium |
| Glissandi | `Line` (gliss style) | Low |
| Tremolo | `NoteRest.SingleTremolos`, `DoubleTremolos` | Medium |
| Cross-staff notes | `NoteRest.CrossStaff` | Low |
| Cue notes | — | Low |
| Ornaments | Various | Low |
| Fingering | `Text` (fingering style) | Low |
| Figured bass | `Text` (figured bass style) | Low |
| Multi-bar rests | `Score.ShowMultiRests` | Medium |
| Instrument changes | `InstrumentChange` | Medium |
