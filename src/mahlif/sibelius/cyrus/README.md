# Cyrus - IPA Syllabification Fixer for Sibelius

Cyrus is a Sibelius plugin that fixes IPA syllabification to match Cyrillic syllable boundaries in vocal scores. It was designed for Bärenreiter's Tchaikovsky Eugene Onegin edition with 3 lyric lines:

- **Verse 1**: Cyrillic text
- **Verse 2**: IPA transcription
- **Verse 3**: German translation (not processed)

## What It Does

The plugin compares Cyrillic and IPA syllable boundaries and moves IPA consonants from the start of one syllable to the end of the previous syllable to match the Cyrillic syllabification.

**Example**: `nɑ̟-ˈt͡ʃʲnoj` → `nɑ̟t͡ʃʲ-ˈnoj` (moves `t͡ʃʲ` to match Cyrillic `ноч-ной`)

## Building

```bash
uv run mahlif sibelius build --hardlink --source src/mahlif/sibelius/cyrus/ Cyrus
```

Then reload in Sibelius: File > Plug-ins > Edit Plug-ins > Unload/Reload

## Report Output

The plugin generates a report with:

- **CHNG**: Changes made (shows before/after IPA and Cyrillic)
- **UNRE**: Unresolved cases that need manual review
- **Stats**: Counts of changes, skipped, and unresolved

Location format: `p4 [B] Bar 8` = page 4, section B, bar 8

---

## Customization Guide

### EASY: Consonant Mappings (~lines 205-228)

Single Cyrillic consonant to IPA mapping:

```manuscript
if (c = 'п') { return 'p'; }
if (c = 'б') { return 'b'; }
if (c = 'т') { return 't'; }
if (c = 'щ') { return 'ʃ'; }  // Change this if different IPA is used
```

To edit: Find `MapSingleCyrillicConsonant` function, add/modify `if` statements.

### EASY: Special Cluster Overrides (~lines 189-191)

Multi-consonant clusters that map to a single IPA sound:

```manuscript
if (cyrOnset = 'сч' or cyrOnset = 'зч' or cyrOnset = 'жч') {
    return 'ʃ';
}
```

To add new clusters: Add `or cyrOnset = 'XX'` conditions in `MapCyrillicToIpa`.

### EASY: Vowel Lists (~lines 441-460)

**Cyrillic vowels** - used to find consonant onset:
```manuscript
GetCyrillicVowels "() {
return 'аеёиоуыэюяАЕЁИОУЫЭЮЯ';
}"
```

**IPA vowels** - used to find consonant onset:
```manuscript
GetIpaVowels "() {
return 'ɑʌɐeɛɪiouaæɨ';
}"
```

**Palatalizing vowels** - Cyrillic vowels that carry initial `j`:
```manuscript
GetPalatalizingVowels "() {
return 'яеёюЯЕЁЮ';
}"
```

To add a vowel: Just add the character to the string.

### EASY: Diacritics (~line 467)

Characters treated as modifiers attached to the previous consonant:

```manuscript
IsDiacritic "(c) {
diacritics = 'ʲːˑ̟̃';
return CharInString(c, diacritics);
}"
```

To add a diacritic: Add the character to the `diacritics` string.

### EASY: IPA Normalization (~lines 305-315)

Characters that should be treated as equivalent during matching:

```manuscript
if (c = 'ɫ') { result = result & 'l'; }  // dark L = light L
if (c = 'ɡ') { result = result & 'g'; }  // IPA g = ASCII g
```

To add equivalences: Add new `if` blocks in `NormalizeIpaForMatching`.

### MEDIUM: Skip Conditions (~line 221)

Conditions to skip processing (don't move consonants):

```manuscript
// Skip jotated vowels (j belongs to vowel, not consonant)
if (StartsWithPalatalizingVowel(cyrB) and IsJotatedVowelOnset(ipaBWork)) {
    return 'SKIP';
}
```

To add new skip conditions: Add `if (...) { return 'SKIP'; }` blocks in `ProcessSyllableBoundary` after the `OnsetMatches` check.

### HARD: Core Algorithm

These require understanding the full algorithm:

- **ExtractOneConsonantUnit**: Groups consonant + tie bar + diacritics as atomic unit
- **ExtractIpaOnset**: Extracts all consonant units before first vowel
- **CalculateUnitsToMove**: Finds how many units to move to match expected onset
- **ProcessSyllableBoundary**: Main logic flow

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

**Plugin doesn't appear in menu**: Check for syntax errors. Use `uv run mahlif sibelius check src/mahlif/sibelius/cyrus/Cyrus.plg`

**Runtime error**: Check the Sibelius trace window for the error location. Common issues:
- Accessing property that doesn't exist (e.g., `.Text` vs `.MarkAsText`)
- For loop with negative end value

**Progress bar stuck at 0**: This is a Sibelius UI quirk. The plugin is running; switch windows and back to see updates.

**Too many/few changes**: Check the vowel lists and consonant mappings match your transcription conventions.
