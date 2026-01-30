# Mahlif XML Schema

Version: 1.0-draft

## Overview

Mahlif XML is a universal interchange format for music notation. It is designed to:

1. Enable accurate bidirectional translation between notation formats (Sibelius, Finale, Dorico, LilyPond, MusicXML, etc.)
2. Capture all musical content (pitches, rhythms, articulations, dynamics, text)
3. Preserve layout adjustments (manual positioning, spacing, page breaks)
4. Support complex scores (multi-movement works, parts, ossia, cues)
5. Be human-readable and debuggable

## Units

| Unit           | Description                                                   |
| -------------- | ------------------------------------------------------------- |
| **tick**       | Duration unit. 256 ticks = quarter note (Sibelius convention) |
| **pitch**      | MIDI pitch number (60 = middle C)                             |
| **1/32 space** | Position offset unit. 32 units = 1 staff space                |

## Document Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mahlif version="1.0" generator="SibeliusPlugin/1.0">
  <meta>...</meta>
  <defaults>...</defaults>
  <parts>...</parts>
  <movements>
    <movement>
      <movement-meta>...</movement-meta>
      <layout>...</layout>
      <staves>...</staves>
      <system-staff>...</system-staff>
    </movement>
  </movements>
</mahlif>
```

For simple single-movement works, the structure can be flattened:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mahlif version="1.0" generator="SibeliusPlugin/1.0">
  <meta>...</meta>
  <layout>...</layout>
  <staves>...</staves>
  <system-staff>...</system-staff>
</mahlif>
```

---

## Element Reference

### `<mahlif>` (root)

| Attribute   | Type   | Required | Description                  |
| ----------- | ------ | -------- | ---------------------------- |
| `version`   | string | yes      | Schema version (e.g., "1.0") |
| `generator` | string | no       | Tool that created this file  |

---

### `<meta>`

Work-level metadata (applies to entire work across all movements).

```xml
<meta>
  <work-title>Symphony No. 5</work-title>
  <work-number>Op. 67</work-number>
  <movement-count>4</movement-count>
  <composer>Ludwig van Beethoven</composer>
  <lyricist></lyricist>
  <arranger></arranger>
  <editor></editor>
  <dedication>Dedicated to Prince Lobkowitz</dedication>
  <copyright>© 2024 Publisher</copyright>
  <publisher>Acme Music</publisher>
  <source-file>symphony5.sib</source-file>
  <source-format>Sibelius 24.6</source-format>
  <encoding-date>2024-01-15</encoding-date>
  <duration-ms>1920000</duration-ms>
</meta>
```

| Element          | Type   | Description                             |
| ---------------- | ------ | --------------------------------------- |
| `work-title`     | string | Title of the complete work              |
| `work-number`    | string | Opus, catalog number, etc.              |
| `movement-count` | int    | Number of movements                     |
| `composer`       | string | Composer name                           |
| `lyricist`       | string | Lyricist/librettist                     |
| `arranger`       | string | Arranger name                           |
| `editor`         | string | Editor (for scholarly editions)         |
| `dedication`     | string | Dedication text                         |
| `copyright`      | string | Copyright notice                        |
| `publisher`      | string | Publisher name                          |
| `source-file`    | string | Original filename                       |
| `source-format`  | string | Original format and version             |
| `encoding-date`  | string | Date of Mahlif encoding (ISO 8601)      |
| `duration-ms`    | int    | Total playback duration in milliseconds |

---

### `<defaults>`

Default values inherited by all movements.

```xml
<defaults>
  <page width="210" height="297" unit="mm"/>
  <margins top="12.7" bottom="12.7" left="12.7" right="12.7" unit="mm"/>
  <staff-height rastral="6">7</staff-height>
  <staff-spacing>10</staff-spacing>
  <system-spacing>15</system-spacing>
  <page-numbers position="bottom-center" first-page="1" show-first="false"/>
  <fonts>
    <music>Bravura</music>
    <text>Times New Roman</text>
    <lyrics>Times New Roman</lyrics>
  </fonts>
</defaults>
```

---

### `<parts>`

Part definitions for part extraction. References staves by number.

```xml
<parts>
  <part id="flute1" name="Flute 1" staves="1"/>
  <part id="flute2" name="Flute 2" staves="2"/>
  <part id="flutes" name="Flutes 1 & 2" staves="1,2"/>
  <part id="piano" name="Piano" staves="15,16"/>
  <part id="strings" name="Strings" staves="17,18,19,20,21"/>
</parts>
```

| Attribute | Type   | Description                   |
| --------- | ------ | ----------------------------- |
| `id`      | string | Unique identifier             |
| `name`    | string | Display name for part         |
| `staves`  | string | Comma-separated staff numbers |

---

### `<movements>`

Container for multi-movement works.

```xml
<movements>
  <movement n="1">...</movement>
  <movement n="2">...</movement>
  <movement n="3">...</movement>
</movements>
```

---

### `<movement>`

A single movement.

```xml
<movement n="1" attacca="false">
  <movement-meta>
    <title>Allegro con brio</title>
    <subtitle></subtitle>
    <tempo-marking>Allegro con brio</tempo-marking>
    <duration-ms>480000</duration-ms>
  </movement-meta>
  <layout>...</layout>
  <staves>...</staves>
  <system-staff>...</system-staff>
</movement>
```

| Attribute | Type | Description                                      |
| --------- | ---- | ------------------------------------------------ |
| `n`       | int  | Movement number (1-indexed)                      |
| `attacca` | bool | Proceeds directly to next movement without pause |

---

### `<movement-meta>`

Movement-level metadata.

```xml
<movement-meta>
  <title>Allegro con brio</title>
  <subtitle>Sonata form</subtitle>
  <tempo-marking>Allegro con brio ♩= 108</tempo-marking>
  <key>C minor</key>
  <time>2/4</time>
  <duration-ms>480000</duration-ms>
</movement-meta>
```

---

### `<layout>`

Score-level layout parameters.

```xml
<layout>
  <page width="210" height="297" unit="mm"/>
  <margins top="12.7" bottom="12.7" left="12.7" right="12.7" unit="mm"/>
  <staff-height rastral="6">7</staff-height>
  <staff-spacing default="10">
    <between staff="1" and="2" distance="8"/>
    <between staff="2" and="3" distance="12"/>
  </staff-spacing>
  <system-spacing>15</system-spacing>
</layout>
```

| Element          | Description                                                                   |
| ---------------- | ----------------------------------------------------------------------------- |
| `page`           | Page dimensions                                                               |
| `margins`        | Page margins                                                                  |
| `staff-height`   | Default staff height in mm. `rastral` attribute (0-8) is optional reference.  |
| `staff-spacing`  | Default space between staves. `<between>` overrides for specific staff pairs. |
| `system-spacing` | Default space between systems in mm                                           |

#### Rastral Sizes (Reference)

| Rastral | Height (mm) | Typical Use       |
| ------- | ----------- | ----------------- |
| 0       | 7.94        | Large scores      |
| 1       | 7.49        | —                 |
| 2       | 7.05        | —                 |
| 3       | 6.60        | Orchestral        |
| 4       | 6.20        | —                 |
| 5       | 5.80        | Chamber           |
| 6       | 5.50        | Piano             |
| 7       | 4.80        | Cue staves        |
| 8       | 3.70        | Ossia, small cues |

---

### `<staves>`

Container for all staves.

```xml
<staves count="24">
  <staff>...</staff>
  <staff>...</staff>
</staves>
```

---

### `<staff>`

A single staff (instrument line).

```xml
<staff n="1"
       instrument="Violin I"
       instrument-short="Vn. I"
       lines="5"
       clef="treble"
       key-sig="0"
       key-mode="major"
       transposition="0"
       voices="2"
       size="100"
       distance-above="12">
  <bar>...</bar>
  <bar>...</bar>
</staff>
```

| Attribute          | Type   | Required | Description                                            |
| ------------------ | ------ | -------- | ------------------------------------------------------ |
| `n`                | int    | yes      | Staff number (1-indexed)                               |
| `instrument`       | string | yes      | Full instrument name                                   |
| `instrument-short` | string | no       | Abbreviated name                                       |
| `lines`            | int    | no       | Number of staff lines (default: 5)                     |
| `clef`             | string | yes      | Initial clef (see Clef Values)                         |
| `key-sig`          | int    | yes      | Initial key signature (-7 to +7 sharps)                |
| `key-mode`         | string | no       | "major" or "minor"                                     |
| `transposition`    | int    | no       | Semitones of transposition (default: 0)                |
| `voices`           | int    | no       | Number of voices (default: 1)                          |
| `size`             | int    | no       | Staff size as percentage (100 = normal, 75 = cue size) |
| `distance-above`   | float  | no       | Distance from staff above in mm (overrides global)     |

---

### `<bar>`

A single measure/bar.

```xml
<bar n="1" length="1024" time-num="4" time-den="4">
  <!-- objects sorted by position -->
</bar>
```

| Attribute  | Type   | Required | Description                                |
| ---------- | ------ | -------- | ------------------------------------------ |
| `n`        | int    | yes      | Bar number                                 |
| `length`   | int    | yes      | Bar length in ticks                        |
| `time-num` | int    | no       | Time signature numerator (if changes here) |
| `time-den` | int    | no       | Time signature denominator                 |
| `key-sig`  | int    | no       | Key signature (if changes here)            |
| `break`    | string | no       | "system" or "page" if break occurs after   |

---

### `<note>` and `<rest>`

A note event or rest.

```xml
<note pos="0" dur="256" voice="1"
      pitch="67" written-pitch="67"
      diatonic="39" written-diatonic="39"
      accidental="" written-accidental=""
      tied="false"
      dx="0" dy="0"
      hidden="false"/>

<rest pos="256" dur="256" voice="1"
      hidden="false"
      dx="0" dy="0"/>
```

| Attribute            | Type   | Required  | Description                                       |
| -------------------- | ------ | --------- | ------------------------------------------------- |
| `pos`                | int    | yes       | Position in ticks from bar start                  |
| `dur`                | int    | yes       | Duration in ticks                                 |
| `voice`              | int    | no        | Voice number (default: 1)                         |
| `pitch`              | int    | note only | MIDI pitch (sounding)                             |
| `written-pitch`      | int    | no        | MIDI pitch (written, for transposing instruments) |
| `diatonic`           | int    | no        | Diatonic pitch (for correct spelling)             |
| `written-diatonic`   | int    | no        | Written diatonic pitch                            |
| `accidental`         | string | no        | Accidental: "", "b", "bb", "#", "x", etc.         |
| `written-accidental` | string | no        | Written accidental                                |
| `tied`               | bool   | no        | Tied to next note                                 |
| `hidden`             | bool   | no        | Hidden/invisible                                  |
| `dx`                 | int    | no        | Horizontal offset (1/32 spaces)                   |
| `dy`                 | int    | no        | Vertical offset (1/32 spaces)                     |
| `color`              | string | no        | Color (hex: "#FF0000" or name: "red")             |
| `size`               | int    | no        | Size as percentage (100 = normal, 60 = cue)       |
| `footnote-ref`       | string | no        | Reference to footnote id                          |

---

### `<chord>`

A chord (multiple simultaneous notes).

```xml
<chord pos="0" dur="256" voice="1"
       stem="auto" beam="continue"
       dx="0" dy="0">
  <n p="60" d="35" a=""/>
  <n p="64" d="37" a=""/>
  <n p="67" d="39" a=""/>
</chord>
```

| Attribute | Type   | Description                        |
| --------- | ------ | ---------------------------------- |
| `stem`    | string | "up", "down", or "auto"            |
| `beam`    | string | "none", "start", "continue", "end" |

Child `<n>` elements (compact note):

| Attribute | Meaning            |
| --------- | ------------------ |
| `p`       | pitch              |
| `d`       | diatonic           |
| `a`       | accidental         |
| `t`       | tied ("1" if true) |

---

### `<grace>`

Grace note(s) attached to following main note.

```xml
<grace pos="256" type="acciaccatura" slur="true">
  <n p="65" d="38" a="" dur="64"/>
  <n p="67" d="39" a="" dur="64"/>
</grace>
```

| Attribute | Type   | Description                                |
| --------- | ------ | ------------------------------------------ |
| `pos`     | int    | Position of main note these attach to      |
| `type`    | string | "grace", "acciaccatura", or "appoggiatura" |
| `slur`    | bool   | Slurred to main note                       |

---

### `<articulation>`

Articulation mark on a note/chord.

```xml
<articulation pos="0" voice="1" type="staccato"/>
<articulation pos="256" voice="1" type="accent"/>
```

| Type Values                                                |
| ---------------------------------------------------------- |
| `staccato`, `staccatissimo`, `tenuto`, `accent`, `marcato` |
| `fermata`, `short-fermata`, `long-fermata`                 |
| `up-bow`, `down-bow`, `harmonic`, `open`, `stopped`        |
| `trill`, `turn`, `mordent`, `prall`                        |

---

### `<dynamic>`

Dynamic marking.

```xml
<dynamic pos="0" voice="1" text="ff" dx="0" dy="0"/>
<dynamic pos="512" voice="1" text="p" dx="-10" dy="5"/>
```

| Attribute | Type   | Description                                                                           |
| --------- | ------ | ------------------------------------------------------------------------------------- |
| `text`    | string | Dynamic text: "ppp", "pp", "p", "mp", "mf", "f", "ff", "fff", "fp", "sf", "sfz", etc. |

---

### `<hairpin>`

Crescendo/diminuendo hairpin.

```xml
<hairpin type="cresc"
         start-bar="1" start-pos="0"
         end-bar="2" end-pos="512"
         voice="1"/>
```

| Attribute   | Type   | Description                |
| ----------- | ------ | -------------------------- |
| `type`      | string | "cresc" or "dim"           |
| `start-bar` | int    | Starting bar number        |
| `start-pos` | int    | Starting position in ticks |
| `end-bar`   | int    | Ending bar number          |
| `end-pos`   | int    | Ending position            |

---

### `<slur>`

Slur or phrasing slur.

```xml
<slur start-bar="1" start-pos="0"
      end-bar="1" end-pos="768"
      voice="1"
      phrasing="false"
      direction="auto"/>
```

| Attribute   | Type   | Description                     |
| ----------- | ------ | ------------------------------- |
| `phrasing`  | bool   | True for phrasing slur (dashed) |
| `direction` | string | "up", "down", or "auto"         |

---

### `<tie>`

Explicit tie (when not expressible via note `tied` attribute).

```xml
<tie start-bar="1" start-pos="768"
     end-bar="2" end-pos="0"
     pitch="67" voice="1"/>
```

---

### `<clef>`

Clef change.

```xml
<clef pos="0" type="bass" dx="0"/>
```

| Clef `type` Values                                  |
| --------------------------------------------------- |
| `treble`, `treble-8vb`, `treble-8va`, `treble-15va` |
| `bass`, `bass-8vb`, `bass-8va`                      |
| `alto`, `tenor`                                     |
| `percussion`, `tab`                                 |

---

### `<key>`

Key signature change.

```xml
<key pos="0" fifths="-3" mode="minor"/>
```

| Attribute | Type   | Description        |
| --------- | ------ | ------------------ |
| `fifths`  | int    | -7 (Cb) to +7 (C#) |
| `mode`    | string | "major" or "minor" |

---

### `<time>`

Time signature change.

```xml
<time pos="0" num="6" den="8"/>
<time pos="0" num="3+2" den="8" display="compound"/>
```

---

### `<text>`

Text annotation.

```xml
<text pos="0" voice="1"
      style="expression"
      placement="above"
      font="Times New Roman"
      size="12"
      bold="false"
      italic="true"
      dx="0" dy="10">dolce</text>
```

| Attribute   | Type   | Description                                           |
| ----------- | ------ | ----------------------------------------------------- |
| `style`     | string | "tempo", "expression", "technique", "rehearsal", etc. |
| `placement` | string | "above" or "below"                                    |
| `font`      | string | Font family name                                      |
| `size`      | float  | Font size in points                                   |
| `bold`      | bool   | Bold text                                             |
| `italic`    | bool   | Italic text                                           |

For mixed formatting within a single text element:

```xml
<text pos="0" style="expression" placement="above">
  <span italic="true">dolce</span> <span bold="true">espressivo</span>
</text>
```

#### `<span>` (child of `<text>`)

| Attribute     | Type   | Description                                  |
| ------------- | ------ | -------------------------------------------- |
| `font`        | string | Font family (inherits from parent if absent) |
| `size`        | float  | Font size (inherits from parent if absent)   |
| `bold`        | bool   | Bold                                         |
| `italic`      | bool   | Italic                                       |
| `underline`   | bool   | Underlined                                   |
| `superscript` | bool   | Superscript                                  |
| `subscript`   | bool   | Subscript                                    |

---

### `<lyrics>`

Lyrics container for a voice/verse combination.

```xml
<lyrics voice="1" verse="1" placement="below">
  <syl pos="0">Hel</syl>
  <syl pos="256" hyphen="true">lo</syl>
  <syl pos="512">world</syl>
  <syl pos="768" melisma="true">now</syl>
</lyrics>
```

| Attribute   | Type   | Required | Description                           |
| ----------- | ------ | -------- | ------------------------------------- |
| `voice`     | int    | yes      | Voice number lyrics attach to         |
| `verse`     | int    | yes      | Verse number (1, 2, 3...)             |
| `placement` | string | no       | "above" or "below" (default: "below") |

#### `<syl>` (syllable)

| Attribute | Type | Required | Description                                      |
| --------- | ---- | -------- | ------------------------------------------------ |
| `pos`     | int  | yes      | Position in ticks (aligns with note)             |
| `hyphen`  | bool | no       | Hyphen follows (word continues)                  |
| `melisma` | bool | no       | Extender line follows (held over multiple notes) |
| `elision` | bool | no       | Elided with next syllable (sung on same note)    |

The text content of `<syl>` is the syllable text.

**Example with multiple verses:**

```xml
<lyrics voice="1" verse="1">
  <syl pos="0">A</syl>
  <syl pos="256" hyphen="true">ma</syl>
  <syl pos="512">zing</syl>
</lyrics>
<lyrics voice="1" verse="2">
  <syl pos="0">'Twas</syl>
  <syl pos="256">grace</syl>
  <syl pos="512">that</syl>
</lyrics>
```

---

### `<tempo>`

Tempo marking.

```xml
<tempo pos="0" bpm="120" beat="4" text="Allegro"/>
<tempo pos="0" bpm="60" beat="4" text="Adagio" parenthetical="true"/>
```

| Attribute       | Type   | Description                         |
| --------------- | ------ | ----------------------------------- |
| `bpm`           | int    | Beats per minute                    |
| `beat`          | int    | Beat unit (4 = quarter, 8 = eighth) |
| `text`          | string | Tempo text (optional)               |
| `parenthetical` | bool   | Metronome mark in parentheses       |

---

### `<rehearsal>`

Rehearsal mark (letter, number, or custom).

```xml
<rehearsal pos="0" type="letter">A</rehearsal>
<rehearsal pos="0" type="number">1</rehearsal>
<rehearsal pos="0" type="bar-number"/>
<rehearsal pos="0" type="custom" enclosure="rectangle">Coda</rehearsal>
```

| Attribute   | Type   | Description                                     |
| ----------- | ------ | ----------------------------------------------- |
| `type`      | string | "letter", "number", "bar-number", "custom"      |
| `enclosure` | string | "rectangle", "square", "oval", "circle", "none" |

Text content is the mark itself (ignored for `bar-number` type).

---

### `<break>`

System or page break.

```xml
<break pos="1024" type="system"/>
<break pos="1024" type="page"/>
```

| Attribute | Type   | Description                |
| --------- | ------ | -------------------------- |
| `type`    | string | "system" or "page"         |
| `pos`     | int    | Position (usually bar end) |

Note: Breaks can also be indicated via `break` attribute on `<bar>`.

---

### `<page-text>`

Text anchored to page position (headers, footers, page numbers, footnotes).

```xml
<page-text position="header-center" page="first">
  Symphony No. 5
</page-text>
<page-text position="footer-right" page="all" type="page-number"/>
<page-text position="footer-left" page="2">
  <footnote marker="*">Manuscript source shows variant reading.</footnote>
</page-text>
```

| Attribute  | Type   | Description                                               |
| ---------- | ------ | --------------------------------------------------------- |
| `position` | string | See position values below                                 |
| `page`     | string | "all", "first", "odd", "even", or specific page number    |
| `type`     | string | "text", "page-number", "copyright", "footnote" (optional) |

**Position values:**

- `header-left`, `header-center`, `header-right`
- `footer-left`, `footer-center`, `footer-right`

---

### `<footnote>`

Footnote (typically in footer, with reference marker in score).

```xml
<footnote id="fn1" marker="*">
  Original manuscript has B-flat here; this edition follows the first printing.
</footnote>
```

The marker can be referenced elsewhere:

```xml
<note pos="256" dur="256" pitch="70" footnote-ref="fn1"/>
```

Or via text:

```xml
<text pos="256" style="footnote-marker">*</text>
```

---

### `<barline>`

Special barline.

```xml
<barline pos="1024" type="double"/>
```

| Type Values                                                                                     |
| ----------------------------------------------------------------------------------------------- |
| `single`, `double`, `final`, `repeat-start`, `repeat-end`, `repeat-both`, `dashed`, `invisible` |

---

### `<octava>`

Ottava line (8va, 8vb, etc.).

```xml
<octava type="8va"
        start-bar="1" start-pos="0"
        end-bar="2" end-pos="512"/>
```

| Type Values                  |
| ---------------------------- |
| `8va`, `8vb`, `15va`, `15vb` |

---

### `<tuplet>`

Tuplet grouping.

```xml
<tuplet start-bar="1" start-pos="0"
        num="3" den="2" actual="3" normal="2"
        bracket="true" number="true"/>
```

| Attribute | Type | Description                               |
| --------- | ---- | ----------------------------------------- |
| `num`     | int  | Display numerator (e.g., 3 for triplet)   |
| `den`     | int  | Display denominator (e.g., 2 for triplet) |
| `actual`  | int  | Actual notes in group                     |
| `normal`  | int  | Normal notes it replaces                  |
| `bracket` | bool | Show bracket                              |
| `number`  | bool | Show number                               |

---

### `<tremolo>`

Tremolo marking.

```xml
<tremolo pos="0" voice="1" strokes="3" type="single"/>
```

| Attribute | Type   | Description                                      |
| --------- | ------ | ------------------------------------------------ |
| `strokes` | int    | Number of tremolo strokes (1-4)                  |
| `type`    | string | "single" (on one note) or "double" (between two) |

---

### `<pedal>`

Piano pedal marking.

```xml
<pedal type="sustain" start-bar="1" start-pos="0" end-bar="2" end-pos="512"/>
<pedal type="sostenuto" start-bar="1" start-pos="0" end-bar="1" end-pos="1024"/>
<pedal type="una-corda" start-bar="1" start-pos="0" end-bar="4" end-pos="0"/>
```

| Attribute   | Type   | Description                                   |
| ----------- | ------ | --------------------------------------------- |
| `type`      | string | "sustain", "sostenuto", "una-corda"           |
| `start-bar` | int    | Starting bar number                           |
| `start-pos` | int    | Starting position in ticks                    |
| `end-bar`   | int    | Ending bar number                             |
| `end-pos`   | int    | Ending position                               |
| `line`      | bool   | Show as line (true) or Ped/\* symbols (false) |

---

### `<fingering>`

Fingering indication.

```xml
<fingering pos="0" voice="1" finger="3"/>
<fingering pos="0" voice="1" finger="1-2" substitution="true"/>
```

| Attribute      | Type   | Description                                                           |
| -------------- | ------ | --------------------------------------------------------------------- |
| `finger`       | string | Finger number(s): "1", "2", "3", "4", "5", or combinations like "1-2" |
| `substitution` | bool   | Finger substitution (change without re-attack)                        |
| `placement`    | string | "above", "below", "left", "right" (default: auto)                     |

---

### `<string-indication>`

String number for bowed strings or guitar.

```xml
<string-indication pos="0" voice="1" string="2"/>
```

| Attribute | Type | Description                 |
| --------- | ---- | --------------------------- |
| `string`  | int  | String number (1 = highest) |

---

### `<chord-symbol>`

Jazz/pop chord symbol.

```xml
<chord-symbol pos="0" root="C" kind="major-seventh" bass="E"/>
<chord-symbol pos="512" root="F" kind="minor" bass=""/>
<chord-symbol pos="0" root="G" kind="dominant" alterations="b9 #11"/>
```

| Attribute     | Type   | Description                                               |
| ------------- | ------ | --------------------------------------------------------- |
| `root`        | string | Root pitch: "C", "C#", "Db", etc.                         |
| `kind`        | string | Chord type (see below)                                    |
| `bass`        | string | Bass note if different from root (slash chord)            |
| `alterations` | string | Space-separated: "b5", "#5", "b9", "#9", "#11", "b13"     |
| `text`        | string | Override display text (e.g., "Cmaj7" for custom spelling) |

**Kind values:** `major`, `minor`, `augmented`, `diminished`, `dominant`, `major-seventh`, `minor-seventh`, `diminished-seventh`, `augmented-seventh`, `half-diminished`, `major-minor`, `major-sixth`, `minor-sixth`, `dominant-ninth`, `major-ninth`, `minor-ninth`, `dominant-11th`, `major-11th`, `minor-11th`, `dominant-13th`, `major-13th`, `minor-13th`, `suspended-second`, `suspended-fourth`, `power`, `other`

---

### `<figured-bass>`

Baroque figured bass notation.

```xml
<figured-bass pos="0" voice="1">
  <figure>6</figure>
  <figure>4</figure>
</figured-bass>

<figured-bass pos="256" voice="1">
  <figure prefix="#">4</figure>
  <figure suffix="+">2</figure>
</figured-bass>
```

| Child element | Attributes                   | Description                                                                                 |
| ------------- | ---------------------------- | ------------------------------------------------------------------------------------------- |
| `<figure>`    | `prefix`, `suffix`, `extend` | Single figure; prefix/suffix for accidentals (#, b, ♮); extend="true" for continuation line |

---

### `<harmonic>`

Harmonic indication (natural or artificial).

```xml
<harmonic pos="0" voice="1" type="natural"/>
<harmonic pos="0" voice="1" type="artificial" base-pitch="48" sounding-pitch="72"/>
```

| Attribute        | Type   | Description                           |
| ---------------- | ------ | ------------------------------------- |
| `type`           | string | "natural" or "artificial"             |
| `base-pitch`     | int    | Stopped pitch for artificial harmonic |
| `touch-pitch`    | int    | Touch pitch for artificial harmonic   |
| `sounding-pitch` | int    | Resulting sounding pitch              |

---

### `<bend>`

Guitar bend.

```xml
<bend pos="0" voice="1" amount="1" release="true"/>
<bend pos="0" voice="1" amount="0.5" pre-bend="true"/>
```

| Attribute  | Type  | Description                                                                  |
| ---------- | ----- | ---------------------------------------------------------------------------- |
| `amount`   | float | Bend amount in semitones (0.5 = quarter tone, 1 = half step, 2 = whole step) |
| `pre-bend` | bool  | Bend before attack                                                           |
| `release`  | bool  | Release bend back to original pitch                                          |

---

### `<slide>`

Slide/glissando between notes.

```xml
<slide start-bar="1" start-pos="0" end-bar="1" end-pos="256" type="shift"/>
<slide start-bar="1" start-pos="0" end-bar="1" end-pos="256" type="legato"/>
```

| Attribute | Type   | Description                                                                                                 |
| --------- | ------ | ----------------------------------------------------------------------------------------------------------- |
| `type`    | string | "shift" (position shift), "legato" (hammer/pull), "glissando" (discrete pitches), "portamento" (continuous) |

---

### `<breath>`

Breath mark.

```xml
<breath pos="512" voice="1" type="comma"/>
<breath pos="512" voice="1" type="tick"/>
```

| Attribute | Type   | Description                         |
| --------- | ------ | ----------------------------------- |
| `type`    | string | "comma", "tick", "upbow", "salzedo" |

---

### `<caesura>`

Caesura (railroad tracks).

```xml
<caesura pos="1024" type="normal"/>
<caesura pos="1024" type="thick"/>
```

| Attribute | Type   | Description                          |
| --------- | ------ | ------------------------------------ |
| `type`    | string | "normal", "thick", "short", "curved" |

---

### `<cue>`

Cue notes (from another instrument).

```xml
<cue start-bar="5" start-pos="0" end-bar="6" end-pos="512"
     source-staff="1" source-instrument="Flute 1"
     voice="1">
  <!-- cue notes inherit from source or can be explicit -->
</cue>
```

| Attribute           | Type   | Description                    |
| ------------------- | ------ | ------------------------------ |
| `source-staff`      | int    | Staff number to cue from       |
| `source-instrument` | string | Instrument name (for labeling) |
| `voice`             | int    | Voice in destination staff     |
| `size`              | int    | Size percentage (default: 60)  |

---

### `<ossia>`

Ossia passage (alternative version on separate staff).

```xml
<ossia start-bar="12" start-pos="0" end-bar="13" end-pos="0"
       parent-staff="3" position="above">
  <bar n="12">
    <note pos="0" dur="256" pitch="72" diatonic="42"/>
    <!-- ... -->
  </bar>
</ossia>
```

| Attribute      | Type   | Description                     |
| -------------- | ------ | ------------------------------- |
| `parent-staff` | int    | Staff this ossia relates to     |
| `position`     | string | "above" or "below" parent staff |
| `start-bar`    | int    | Starting bar                    |
| `end-bar`      | int    | Ending bar                      |

---

### `<ending>`

Repeat ending (volta bracket).

```xml
<ending start-bar="8" start-pos="0" end-bar="9" end-pos="1024"
        numbers="1" type="start"/>
<ending start-bar="10" start-pos="0" end-bar="11" end-pos="1024"
        numbers="2,3" type="discontinue"/>
```

| Attribute | Type   | Description                                                                   |
| --------- | ------ | ----------------------------------------------------------------------------- |
| `numbers` | string | Comma-separated ending numbers: "1", "2", "1,2"                               |
| `type`    | string | "start" (with downward jog), "stop" (with jog), "discontinue" (no ending jog) |

---

### `<segno>`

Segno sign.

```xml
<segno pos="0" id="segno1"/>
```

---

### `<coda>`

Coda sign.

```xml
<coda pos="0" id="coda1"/>
```

---

### `<jump>`

Navigation instruction (D.C., D.S., etc.).

```xml
<jump pos="1024" type="da-capo"/>
<jump pos="1024" type="dal-segno" target="segno1"/>
<jump pos="1024" type="to-coda" target="coda1"/>
<jump pos="1024" type="da-capo-al-coda" target="coda1"/>
<jump pos="1024" type="dal-segno-al-fine" target="segno1"/>
```

| Attribute | Type   | Description                 |
| --------- | ------ | --------------------------- |
| `type`    | string | See values below            |
| `target`  | string | ID of segno/coda to jump to |

**Type values:** `da-capo`, `dal-segno`, `da-capo-al-fine`, `da-capo-al-coda`, `dal-segno-al-fine`, `dal-segno-al-coda`, `to-coda`, `fine`

---

### `<fine>`

Fine (end point for D.C./D.S. al Fine).

```xml
<fine pos="1024"/>
```

---

### `<multimeasure-rest>`

Consolidated multi-measure rest.

```xml
<multimeasure-rest start-bar="5" count="12"/>
```

| Attribute   | Type | Description       |
| ----------- | ---- | ----------------- |
| `start-bar` | int  | First bar of rest |
| `count`     | int  | Number of bars    |

---

### `<system-staff>`

System-level objects (tempos, rehearsal marks, system text).

```xml
<system-staff>
  <bar n="1">
    <tempo pos="0" bpm="120" beat="4" text="Allegro vivace"/>
    <text pos="0" style="rehearsal">A</text>
  </bar>
</system-staff>
```

---

## Complete Example

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mahlif version="1.0" generator="MahlifPlugin/1.0">
  <meta>
    <title>Simple Example</title>
    <composer>Test Composer</composer>
  </meta>

  <layout>
    <page width="210" height="297" unit="mm"/>
    <margins top="12.7" bottom="12.7" left="12.7" right="12.7" unit="mm"/>
    <staff-height rastral="6">7</staff-height>
    <staff-spacing default="10">
      <between staff="1" and="2" distance="8"/>
    </staff-spacing>
    <system-spacing>15</system-spacing>
  </layout>

  <staves count="2">
    <staff n="1" instrument="Voice" clef="treble" key-sig="0" size="100">
      <bar n="1" length="1024" time-num="4" time-den="4">
        <note pos="0" dur="256" voice="1" pitch="67" diatonic="39"/>
        <note pos="256" dur="256" voice="1" pitch="69" diatonic="40"/>
        <note pos="512" dur="512" voice="1" pitch="71" diatonic="41"/>
        <dynamic pos="0" voice="1" text="mp"/>
        <slur start-bar="1" start-pos="0" end-bar="1" end-pos="768" voice="1"/>
      </bar>

      <bar n="2" length="1024">
        <note pos="0" dur="512" voice="1" pitch="72" diatonic="42"/>
        <rest pos="512" dur="512" voice="1"/>
        <hairpin type="dim" start-bar="2" start-pos="0" end-bar="2" end-pos="512"/>
      </bar>

      <lyrics voice="1" verse="1">
        <syl pos="0">Hel</syl>
        <syl pos="256" hyphen="true">lo</syl>
        <syl pos="512" melisma="true">world</syl>
        <syl pos="1024">now</syl>
      </lyrics>
    </staff>

    <staff n="2" instrument="Piano" clef="treble" key-sig="0" size="100" distance-above="8">
      <bar n="1" length="1024" time-num="4" time-den="4">
        <chord pos="0" dur="256" voice="1">
          <n p="60" d="35" a=""/>
          <n p="64" d="37" a=""/>
          <n p="67" d="39" a=""/>
        </chord>
        <chord pos="256" dur="256" voice="1">
          <n p="60" d="35" a=""/>
          <n p="65" d="38" a=""/>
          <n p="69" d="40" a=""/>
        </chord>
        <chord pos="512" dur="512" voice="1">
          <n p="59" d="34" a=""/>
          <n p="62" d="36" a=""/>
          <n p="67" d="39" a=""/>
        </chord>
        <dynamic pos="0" voice="1" text="mp"/>
      </bar>

      <bar n="2" length="1024">
        <chord pos="0" dur="512" voice="1">
          <n p="60" d="35" a=""/>
          <n p="64" d="37" a=""/>
          <n p="67" d="39" a=""/>
        </chord>
        <rest pos="512" dur="512" voice="1"/>
      </bar>
    </staff>
  </staves>

  <system-staff>
    <bar n="1">
      <tempo pos="0" bpm="96" beat="4" text="Andante"/>
      <text pos="0" style="expression" placement="above" italic="true">con espressione</text>
    </bar>
  </system-staff>
</mahlif>
```

---

## Design Rationale

1. **Flat structure within bars** — All objects at bar level, sorted by position. Easier to process than deeply nested.

2. **Spanners reference endpoints** — Slurs, hairpins, etc. store start/end positions explicitly rather than wrapping content.

3. **Compact note format in chords** — `<n p="60" d="35" a=""/>` reduces verbosity for chords.

4. **Separate system-staff** — Global items (tempo, rehearsal marks) kept separate from instrument staves.

5. **Layout offsets preserved** — `dx`/`dy` on notes and text enable faithful reproduction of manual adjustments.

6. **Human-readable** — Clear attribute names, indentation-friendly structure.

7. **Multi-movement support** — Full works with movements, attacca, movement-level metadata.

8. **Round-trip fidelity** — Designed so Sibelius → Mahlif → Sibelius (or any pair) loses minimal information.

---

## Format Compatibility Notes

### Sibelius

- Full support for all ManuScript-accessible properties
- dx/dy offsets map directly
- Rehearsal marks, page-aligned text supported

### Finale

- Similar object model; most elements map directly
- Smart Shapes → spanners
- Expressions → text with styles

### Dorico

- Flow = Movement
- Players/Layouts = Parts
- Most notation elements have direct equivalents

### LilyPond

- Most elements have direct `\command` equivalents
- dx/dy → `\override ... #'extra-offset`
- Layout → `\paper`, `\layout` blocks

### MusicXML

- Mahlif is more layout-aware than MusicXML
- MusicXML `<direction>` → Mahlif `<text>`, `<dynamic>`, `<tempo>`
- Mahlif spanners more explicit than MusicXML nesting

---

## Future Extensions

These elements may be added based on demand. Most notation software handles these via workarounds or plugins.

### Playback

- `<sound>` — MIDI/playback overrides (velocity, channel, instrument change)
- `<swing>` — Swing/shuffle playback ratio

### Editorial

- `<editorial>` — Editorial additions (brackets, dashed slurs, small type)
- `<variant>` — Alternative readings from different manuscript sources
- `<comment>` — Non-printing annotations/comments for collaboration

### Advanced Layout

- `<frame>` — Text frames (title pages, program notes, arbitrary positioned text)
- `<graphic>` — Embedded images/SVG
- `<spacer>` — Explicit vertical/horizontal spacing adjustments

### Specialized Notation

- `<accordion>` — Accordion register symbols
- `<harp-pedal>` — Harp pedal diagrams
- `<scordatura>` — Alternate tuning notation
- `<mensural>` — Medieval/Renaissance notation
- `<neume>` — Gregorian chant notation
- `<tablature>` — Full tab support (currently only `<string-indication>`)
- `<bowing>` — Detailed bowing patterns (hooked, ricochet, etc.)
- `<brass-techniques>` — Mutes, stopped horn, flutter tongue
- `<percussion-unpitched>` — Full unpitched percussion with instrument maps
