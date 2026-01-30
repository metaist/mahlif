"""Tests for extract_objects function."""

from __future__ import annotations

from mahlif.sibelius.manuscript.extract import extract_objects


def test_extract_objects_basic() -> None:
    """Test extracting objects from PDF text."""
    text = """
Bar
A Bar contains BarObject objects.

Methods
l

AddNote(pos,pitch,dur)
Adds a note.

l

Delete()
Deletes.

Variables
l

Length
The length.

l

BarNumber
The bar number.
"""
    objects = extract_objects(list(text.split("\n")))
    assert "Bar" in objects
    bar = objects["Bar"]
    assert "AddNote" in bar.methods
    assert "Delete" in bar.methods
    assert "Length" in bar.properties
    assert "BarNumber" in bar.properties


def test_extract_objects_multiple() -> None:
    """Test extracting multiple object types."""
    text = """
Staff
A Staff.

Methods
l

NthBar(n)
Gets bar.

Variables
l

Name
The name.

Note
A Note.

Methods
l

Delete()
Deletes.

Variables
l

Pitch
The pitch.
"""
    objects = extract_objects(list(text.split("\n")))
    assert "Staff" in objects
    assert "Note" in objects
    assert "NthBar" in objects["Staff"].methods
    assert "Delete" in objects["Note"].methods


def test_extract_objects_duplicate_object() -> None:
    """Test extracting an object defined in multiple places merges methods."""
    text = """
Barline
A Barline object.

Methods
l

Test1()
First method.

Variables
l

Aa
Property one.

Barline
More Barline docs.

Methods
l

Test2()
Second method.

Variables
l

Bb
Property two.
"""
    objects = extract_objects(list(text.split("\n")))
    assert "Barline" in objects
    barline = objects["Barline"]
    assert "Test1" in barline.methods
    assert "Test2" in barline.methods
    assert "Aa" in barline.properties
    assert "Bb" in barline.properties


def test_extract_objects_skip_object_reference_header() -> None:
    """Test that '4 Object Reference' line is skipped."""
    text = """
4 Object Reference

Bar
A Bar.

Methods
l

Test()
Test method.

Variables
l

Name
The name.
"""
    objects = extract_objects(list(text.split("\n")))
    assert "Bar" in objects
    assert "4" not in objects
    assert "4 Object Reference" not in objects


def test_extract_objects_with_4_object_reference() -> None:
    """Test that '4 Object Reference' line inside object is skipped."""
    text = """
Barline
A Barline.

Methods
l

4 Object Reference

Test()
Test method.

Variables
l

Name
The name.
"""
    objects = extract_objects(list(text.split("\n")))
    assert "Barline" in objects
    assert "4" not in objects["Barline"].methods
    assert "Test" in objects["Barline"].methods


def test_extract_objects_method_overload() -> None:
    """Test extracting overloaded methods (same name, different signatures)."""
    text = """
Barline
A Barline.

Methods
l

Test(a)
One param.

l

Test(a,b)
Two params.

Variables
l

Name
The name.
"""
    objects = extract_objects(list(text.split("\n")))
    assert "Barline" in objects
    barline = objects["Barline"]
    assert "Test" in barline.methods
    sigs = barline.methods["Test"]
    assert len(sigs) == 2


def test_extract_duplicate_method_name() -> None:
    """Test extraction handles duplicate method names (merges signatures)."""
    lines = [
        "Sibelius",
        "Description of Sibelius object",
        "Methods",
        "TestMethod()",
        "TestMethod(param1)",
        "Variables",
        "SomeProp",
        "",
        "Bar",
        "Description of Bar",
        "Methods",
        "OtherMethod()",
    ]
    objects = extract_objects(lines)

    assert "Sibelius" in objects
    assert "TestMethod" in objects["Sibelius"].methods
    assert len(objects["Sibelius"].methods["TestMethod"]) == 2


def test_extract_object_split_across_pages() -> None:
    """Test extraction handles object split across pages (same name twice)."""
    lines = [
        "Sibelius",
        "First description",
        "Methods",
        "FirstMethod()",
        "",
        "Bar",
        "Bar description",
        "Methods",
        "BarMethod()",
        "",
        "Sibelius",
        "Continued description",
        "Methods",
        "FirstMethod(x)",
        "SecondMethod()",
        "Variables",
        "ExtraProp",
    ]
    objects = extract_objects(lines)

    assert "Sibelius" in objects
    assert "FirstMethod" in objects["Sibelius"].methods
    assert len(objects["Sibelius"].methods["FirstMethod"]) == 2
    assert "SecondMethod" in objects["Sibelius"].methods
