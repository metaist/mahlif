"""Parse Mahlif XML into data models."""

from __future__ import annotations

from pathlib import Path

from lxml import etree

from mahlif.models import (
    Bar,
    Barline,
    Clef,
    Dynamic,
    Grace,
    Hairpin,
    KeySignature,
    Layout,
    Lyrics,
    Meta,
    Movement,
    Note,
    NoteRest,
    Octava,
    Pedal,
    Position,
    Rehearsal,
    Score,
    Slur,
    Staff,
    Syllable,
    SystemStaff,
    Tempo,
    Text,
    TimeSignature,
    Trill,
    Tuplet,
)


def _get_text(elem: etree._Element, tag: str, default: str = "") -> str:
    """Get text content of a child element."""
    child = elem.find(tag)
    return child.text or default if child is not None else default


def _get_attr(elem: etree._Element, attr: str, default: str = "") -> str:
    """Get attribute value."""
    return elem.get(attr, default)


def _get_int(elem: etree._Element, attr: str, default: int = 0) -> int:
    """Get integer attribute."""
    val = elem.get(attr)
    return int(val) if val is not None else default


def _get_float(elem: etree._Element, attr: str, default: float = 0.0) -> float:
    """Get float attribute."""
    val = elem.get(attr)
    return float(val) if val is not None else default


def _get_bool(elem: etree._Element, attr: str, default: bool = False) -> bool:
    """Get boolean attribute."""
    val = elem.get(attr)
    if val is None:
        return default
    return val.lower() in ("true", "1", "yes")


def _parse_position(elem: etree._Element) -> Position:
    """Parse dx/dy offset."""
    return Position(
        dx=_get_float(elem, "dx"),
        dy=_get_float(elem, "dy"),
    )


def _parse_note(elem: etree._Element) -> Note:
    """Parse a note element (compact <n> format)."""
    return Note(
        pitch=_get_int(elem, "p"),
        diatonic=_get_int(elem, "d"),
        accidental=_get_attr(elem, "a"),
        tied=_get_bool(elem, "t"),
    )


def _parse_noterest(elem: etree._Element) -> NoteRest:
    """Parse a note, chord, or rest element."""
    tag = elem.tag
    notes: list[Note] = []
    articulations: list[str] = []

    match tag:
        case "chord":
            # Parse child notes
            for n_elem in elem.findall("n"):
                notes.append(_parse_note(n_elem))
        case "note":
            # Single note
            notes.append(
                Note(
                    pitch=_get_int(elem, "pitch"),
                    written_pitch=_get_int(elem, "written-pitch") or None,
                    diatonic=_get_int(elem, "diatonic"),
                    accidental=_get_attr(elem, "accidental"),
                    tied=_get_bool(elem, "tied"),
                )
            )
        case "rest":
            # Rest - no notes
            pass
        case _:  # pragma: no cover
            raise ValueError(f"Unknown noterest type: {tag!r}")

    # Parse articulations
    art_str = _get_attr(elem, "articulations")
    if art_str:
        articulations = art_str.split()

    stem = _get_attr(elem, "stem", "auto")
    beam = _get_attr(elem, "beam", "auto")

    # Type narrowing for literals
    stem_val: str = stem if stem in ("auto", "up", "down") else "auto"
    beam_val: str = (
        beam if beam in ("auto", "none", "start", "continue", "end") else "auto"
    )

    return NoteRest(
        pos=_get_int(elem, "pos"),
        dur=_get_int(elem, "dur"),
        voice=_get_int(elem, "voice", 1),
        hidden=_get_bool(elem, "hidden"),
        offset=_parse_position(elem),
        notes=notes,
        articulations=articulations,
        stem=stem_val,  # type: ignore[arg-type]
        beam=beam_val,  # type: ignore[arg-type]
    )


def _parse_bar_elements(
    bar_elem: etree._Element,
) -> list[
    NoteRest
    | Clef
    | KeySignature
    | TimeSignature
    | Dynamic
    | Text
    | Slur
    | Hairpin
    | Tuplet
    | Barline
    | Octava
    | Pedal
    | Trill
    | Grace
    | Tempo
    | Rehearsal
]:
    """Parse all elements within a bar."""
    elements: list[
        NoteRest
        | Clef
        | KeySignature
        | TimeSignature
        | Dynamic
        | Text
        | Slur
        | Hairpin
        | Tuplet
        | Barline
        | Octava
        | Pedal
        | Trill
        | Grace
        | Tempo
        | Rehearsal
    ] = []

    for child in bar_elem:
        match child.tag:
            case "note" | "chord" | "rest":
                elements.append(_parse_noterest(child))

            case "clef":
                elements.append(
                    Clef(
                        pos=_get_int(child, "pos"),
                        type=_get_attr(child, "type", "treble"),
                        offset=_parse_position(child),
                    )
                )

            case "key":
                mode = _get_attr(child, "mode", "major")
                mode_val: str = mode if mode in ("major", "minor") else "major"
                elements.append(
                    KeySignature(
                        pos=_get_int(child, "pos"),
                        fifths=_get_int(child, "fifths"),
                        mode=mode_val,  # type: ignore[arg-type]
                    )
                )

            case "time":
                elements.append(
                    TimeSignature(
                        pos=_get_int(child, "pos"),
                        num=_get_int(child, "num"),
                        den=_get_int(child, "den"),
                    )
                )

            case "dynamic":
                elements.append(
                    Dynamic(
                        pos=_get_int(child, "pos"),
                        text=_get_attr(child, "text"),
                        voice=_get_int(child, "voice", 1),
                        offset=_parse_position(child),
                    )
                )

            case "text":
                elements.append(
                    Text(
                        pos=_get_int(child, "pos"),
                        text=child.text or "",
                        style=_get_attr(child, "style"),
                        voice=_get_int(child, "voice", 1),
                        offset=_parse_position(child),
                    )
                )

            case "tempo":
                elements.append(
                    Tempo(
                        pos=_get_int(child, "pos"),
                        text=_get_attr(child, "text") or "",
                        bpm=int(_get_float(child, "bpm"))
                        if _get_float(child, "bpm")
                        else None,
                        offset=_parse_position(child),
                    )
                )

            case "rehearsal":
                elements.append(
                    Rehearsal(
                        pos=_get_int(child, "pos"),
                        text=child.text or _get_attr(child, "text") or "",
                        type=_get_attr(child, "type") or "custom",  # type: ignore[arg-type]
                    )
                )

            case "slur":
                elements.append(
                    Slur(
                        start_bar=_get_int(child, "start-bar"),
                        start_pos=_get_int(child, "start-pos"),
                        end_bar=_get_int(child, "end-bar"),
                        end_pos=_get_int(child, "end-pos"),
                        voice=_get_int(child, "voice", 1),
                    )
                )

            case "hairpin":
                hp_type = _get_attr(child, "type", "cresc")
                hp_type_val: str = hp_type if hp_type in ("cresc", "dim") else "cresc"
                elements.append(
                    Hairpin(
                        type=hp_type_val,  # type: ignore[arg-type]
                        start_bar=_get_int(child, "start-bar"),
                        start_pos=_get_int(child, "start-pos"),
                        end_bar=_get_int(child, "end-bar"),
                        end_pos=_get_int(child, "end-pos"),
                        voice=_get_int(child, "voice", 1),
                    )
                )

            case "tuplet":
                elements.append(
                    Tuplet(
                        start_bar=_get_int(child, "start-bar"),
                        start_pos=_get_int(child, "start-pos"),
                        num=_get_int(child, "num"),
                        den=_get_int(child, "den"),
                    )
                )

            case "barline":
                elements.append(
                    Barline(
                        pos=_get_int(child, "pos"),
                        type=_get_attr(child, "type", "single"),
                    )
                )

            case "octava":
                elements.append(
                    Octava(
                        type=_get_attr(child, "type", "8va"),
                        start_bar=_get_int(child, "start-bar"),
                        start_pos=_get_int(child, "start-pos"),
                        end_bar=_get_int(child, "end-bar"),
                        end_pos=_get_int(child, "end-pos"),
                        voice=_get_int(child, "voice", 1),
                    )
                )

            case "pedal":
                elements.append(
                    Pedal(
                        type=_get_attr(child, "type", "sustain"),
                        start_bar=_get_int(child, "start-bar"),
                        start_pos=_get_int(child, "start-pos"),
                        end_bar=_get_int(child, "end-bar"),
                        end_pos=_get_int(child, "end-pos"),
                    )
                )

            case "trill":
                elements.append(
                    Trill(
                        start_bar=_get_int(child, "start-bar"),
                        start_pos=_get_int(child, "start-pos"),
                        end_bar=_get_int(child, "end-bar"),
                        end_pos=_get_int(child, "end-pos"),
                        voice=_get_int(child, "voice", 1),
                    )
                )

            case "grace":
                elements.append(
                    Grace(
                        pos=_get_int(child, "pos"),
                        type=_get_attr(child, "type", "grace"),
                        pitch=_get_int(child, "pitch"),
                        dur=_get_int(child, "dur"),
                        voice=_get_int(child, "voice", 1),
                    )
                )

            case _:  # pragma: no cover
                raise ValueError(f"Unknown bar element tag: {child.tag!r}")

    return elements


def _parse_bar(bar_elem: etree._Element) -> Bar:
    """Parse a bar element."""
    return Bar(
        n=_get_int(bar_elem, "n"),
        length=_get_int(bar_elem, "length", 1024),
        break_type=_get_attr(bar_elem, "break") or None,
        elements=_parse_bar_elements(bar_elem),
    )


def _parse_lyrics(staff_elem: etree._Element) -> list[Lyrics]:
    """Parse lyrics elements from a staff."""
    lyrics_list: list[Lyrics] = []

    for lyrics_elem in staff_elem.findall("lyrics"):
        syllables: list[Syllable] = []
        for syl_elem in lyrics_elem.findall("syl"):
            syllables.append(
                Syllable(
                    pos=_get_int(syl_elem, "pos"),
                    text=syl_elem.text or "",
                    bar=_get_int(syl_elem, "bar") or None,
                    hyphen=_get_bool(syl_elem, "hyphen"),
                    melisma=_get_bool(syl_elem, "melisma"),
                )
            )

        lyrics_list.append(
            Lyrics(
                voice=_get_int(lyrics_elem, "voice", 1),
                verse=_get_int(lyrics_elem, "verse", 1),
                syllables=syllables,
            )
        )

    return lyrics_list


def _parse_staff(staff_elem: etree._Element) -> Staff:
    """Parse a staff element."""
    bars = [_parse_bar(bar_elem) for bar_elem in staff_elem.findall("bar")]
    lyrics = _parse_lyrics(staff_elem)

    return Staff(
        n=_get_int(staff_elem, "n"),
        instrument=_get_attr(staff_elem, "instrument"),
        instrument_short=_get_attr(staff_elem, "instrument-short"),
        full_name=_get_attr(staff_elem, "full-name"),
        short_name=_get_attr(staff_elem, "short-name"),
        clef=_get_attr(staff_elem, "clef", "treble"),
        key_sig=_get_int(staff_elem, "key-sig"),
        lines=_get_int(staff_elem, "lines", 5),
        size=_get_int(staff_elem, "size", 100),
        bars=bars,
        lyrics=lyrics,
    )


def _parse_system_staff(ss_elem: etree._Element) -> SystemStaff:
    """Parse system staff element."""
    bars = [_parse_bar(bar_elem) for bar_elem in ss_elem.findall("bar")]
    return SystemStaff(bars=bars)


def _parse_layout(layout_elem: etree._Element) -> Layout:
    """Parse layout element."""
    page_elem = layout_elem.find("page")
    page_width = (
        _get_float(page_elem, "width", 210.0) if page_elem is not None else 210.0
    )
    page_height = (
        _get_float(page_elem, "height", 297.0) if page_elem is not None else 297.0
    )

    staff_height_elem = layout_elem.find("staff-height")
    staff_height = (
        float(staff_height_elem.text or 7.0) if staff_height_elem is not None else 7.0
    )

    return Layout(
        page_width=page_width,
        page_height=page_height,
        staff_height=staff_height,
    )


def _parse_meta(meta_elem: etree._Element) -> Meta:
    """Parse meta element."""
    return Meta(
        work_title=_get_text(meta_elem, "work-title"),
        composer=_get_text(meta_elem, "composer"),
        lyricist=_get_text(meta_elem, "lyricist"),
        arranger=_get_text(meta_elem, "arranger"),
        copyright=_get_text(meta_elem, "copyright"),
        publisher=_get_text(meta_elem, "publisher"),
        source_file=_get_text(meta_elem, "source-file"),
        source_format=_get_text(meta_elem, "source-format"),
        duration_ms=int(_get_text(meta_elem, "duration-ms") or 0),
    )


def _parse_movement(mov_elem: etree._Element) -> Movement:
    """Parse a movement element."""
    # Movement meta
    mov_meta = mov_elem.find("movement-meta")
    title = _get_text(mov_meta, "title") if mov_meta is not None else ""

    # Layout
    layout_elem = mov_elem.find("layout")
    layout = _parse_layout(layout_elem) if layout_elem is not None else Layout()

    # Staves
    staves_elem = mov_elem.find("staves")
    staves = (
        [_parse_staff(s) for s in staves_elem.findall("staff")]
        if staves_elem is not None
        else []
    )

    # System staff
    ss_elem = mov_elem.find("system-staff")
    system_staff = (
        _parse_system_staff(ss_elem) if ss_elem is not None else SystemStaff()
    )

    return Movement(
        n=_get_int(mov_elem, "n"),
        title=title,
        layout=layout,
        staves=staves,
        system_staff=system_staff,
    )


def parse(source: str | Path | bytes) -> Score:
    """Parse a Mahlif XML file into a Score object.

    Handles UTF-8 and UTF-16 encoded files automatically.

    Args:
        source: Path to XML file, XML string, or XML bytes

    Returns:
        Parsed Score object
    """
    if isinstance(source, bytes):
        # Raw bytes - lxml auto-detects encoding from BOM/declaration
        root = etree.fromstring(source)
    elif isinstance(source, Path) or (
        isinstance(source, str) and not source.strip().startswith("<")
    ):
        # It's a file path - read as bytes to let lxml handle encoding
        path = Path(source)
        with open(path, "rb") as f:
            content = f.read()
        root = etree.fromstring(content)
    else:
        # It's an XML string (assumed UTF-8)
        root = etree.fromstring(source.encode("utf-8"))

    # Validate root element
    if root.tag != "mahlif":
        raise ValueError(f"Invalid root element: {root.tag!r}. Expected 'mahlif'.")

    # Meta
    meta_elem = root.find("meta")
    meta = _parse_meta(meta_elem) if meta_elem is not None else Meta()

    # Check for multi-movement structure
    movements_elem = root.find("movements")
    if movements_elem is not None:
        # Multi-movement work
        movements = [_parse_movement(m) for m in movements_elem.findall("movement")]
        return Score(
            meta=meta,
            movements=movements,
        )

    # Single movement / flat structure
    layout_elem = root.find("layout")
    layout = _parse_layout(layout_elem) if layout_elem is not None else Layout()

    staves_elem = root.find("staves")
    staves = (
        [_parse_staff(s) for s in staves_elem.findall("staff")]
        if staves_elem is not None
        else []
    )

    ss_elem = root.find("system-staff")
    system_staff = (
        _parse_system_staff(ss_elem) if ss_elem is not None else SystemStaff()
    )

    return Score(
        meta=meta,
        layout=layout,
        staves=staves,
        system_staff=system_staff,
    )
