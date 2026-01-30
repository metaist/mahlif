# Cyrus - IPA Syllabification Fixer for Sibelius

Cyrus is a Sibelius plugin that fixes IPA syllabification to match Cyrillic syllable boundaries in vocal scores. It was designed for Bärenreiter's Tchaikovsky Eugene Onegin edition with 3 lyric lines:

- **Verse 1**: Cyrillic text
- **Verse 2**: IPA transcription
- **Verse 3**: German translation (not processed)

## What It Does

The plugin compares Cyrillic and IPA syllable boundaries and moves IPA consonants from the start of one syllable to the end of the previous syllable to match the Cyrillic syllabification.

**Example**: `nɑ̟-ˈt͡ʃʲnoj` → `nɑ̟t͡ʃʲ-ˈnoj` (moves `t͡ʃʲ` to match Cyrillic `ноч-ной`)

---

## Installation

First, [install Mahlif](https://docs.metaist.com/mahlif/#install) if you haven't already.

Then install the Cyrus plugin:

```bash
uv run mahlif sibelius install Cyrus
```

Reload in Sibelius: **File > Plug-ins > Edit Plug-ins** > select Cyrus > **Unload** then **Load**

## Usage

1. Open your score in Sibelius
2. Run **Plug-ins > Other > Cyrus**
3. The plugin will process all staves with lyrics
4. Save the report when prompted
5. Review the report for any unresolved cases

### Converting Report Encoding

Sibelius saves files as UTF-16. To convert to UTF-8 for easier viewing:

```bash
uv run mahlif encoding utf8 cyrus_report.txt
```

This converts the file in place. Use `-o output.txt` to save to a different file.

---

## Report Format

The report shows:

- **CHNG**: Changes made (before → after IPA with Cyrillic comparison)
- **UNRE**: Unresolved cases that need manual review

Location format: `p4 [B] Bar 8, Beat 1` = page 4, section B, bar 8, beat 1

Example:

```
CHNG p4 [B] Bar 8, Beat 1, Tatyana: nɑ̟-ˈt͡ʃʲnoj -> nɑ̟t͡ʃʲ-ˈnoj (cyr: ноч-ной)
UNRE p10 [B] Bar 36, Beat 1, Onegin: jɛ-ˈvo (cyr: е-го, expected: g)
```

---

## Building from Source

For development:

```bash
uv run mahlif sibelius build --hardlink --source src/mahlif/sibelius/cyrus/ Cyrus
```

Then reload in Sibelius: **File > Plug-ins > Edit Plug-ins** > Unload/Reload

---

## Customization Guide

### EASY: Consonant Mappings

Single Cyrillic consonant to IPA mapping in `MapSingleCyrillicConsonant`:

```manuscript
if (c = 'щ') { return 'ʃ'; }  // Change this if different IPA is used
```

### EASY: Special Cluster Overrides

Multi-consonant clusters that map to a single IPA sound in `MapCyrillicToIpa`:

```manuscript
if (cyrOnset = 'сч' or cyrOnset = 'зч' or cyrOnset = 'жч') {
    return 'ʃ';
}
```

### EASY: Vowel Lists

**Cyrillic vowels** in `GetCyrillicVowels`:

```manuscript
return 'аеёиоуыэюяАЕЁИОУЫЭЮЯ';
```

**IPA vowels** in `GetIpaVowels`:

```manuscript
return 'ɑʌɐeɛɪiouaæɨ';
```

**Palatalizing vowels** in `GetPalatalizingVowels`:

```manuscript
return 'яеёюЯЕЁЮ';
```

### EASY: Diacritics

Characters treated as modifiers in `IsDiacritic`:

```manuscript
diacritics = 'ʲːˑ̟̃';
```

### EASY: IPA Normalization

Character equivalences in `NormalizeIpaForMatching`:

```manuscript
if (c = 'ɫ') { result = result & 'l'; }  // dark L = light L
if (c = 'ɡ') { result = result & 'g'; }  // IPA g = ASCII g
```

### MEDIUM: Skip Conditions

Add conditions in `ProcessSyllableBoundary` after the `OnsetMatches` check:

```manuscript
if (StartsWithPalatalizingVowel(cyrB) and IsJotatedVowelOnset(ipaBWork)) {
    return 'SKIP';
}
```

### HARD: Core Algorithm

These require understanding the full algorithm:

- `ExtractOneConsonantUnit`: Groups consonant + tie bar + diacritics as atomic unit
- `ExtractIpaOnset`: Extracts all consonant units before first vowel
- `CalculateUnitsToMove`: Finds how many units to move to match expected onset
- `ProcessSyllableBoundary`: Main logic flow

---

## Key Design Decisions

1. **Stress marker `ˈ` stays at syllable start** - never moved
2. **Affricates with tie bar (`t͡ʃ`, `t͡s`) are atomic** - not split
3. **Diacritics attach to previous consonant** - moved together
4. **Palatalizing vowels (я, е, ё, ю) keep their `j`** - when word-initial or after vowel
5. **г→в sound changes are flagged as UNRE** - legitimate transcription, can't auto-fix

## Lyric Style IDs

The plugin looks for these Sibelius style IDs:

- Verse 1 (Cyrillic): `text.staff.space.hypen.lyrics.verse1`
- Verse 2 (IPA): `text.staff.space.hypen.lyrics.verse2`

---

## Troubleshooting

**Plugin doesn't appear in menu**: Check for syntax errors:

```bash
uv run mahlif sibelius check src/mahlif/sibelius/cyrus/Cyrus.plg
```

**Progress bar stuck at 0**: This is a Sibelius UI quirk. The plugin is running; switch windows and back to see updates.

**Too many/few changes**: Check the vowel lists and consonant mappings match your transcription conventions.

**Report has strange characters**: Convert encoding:

```bash
uv run mahlif encoding utf8 cyrus_report.txt
```
