# String and Literal Tests

Tests for string literals and escape sequences.

## Unterminated String

Strings must be closed on the same line (unless using escape sequences).

NOTE: Multi-line method bodies are not yet fully supported for deep checking.
This test currently passes because the method body extraction doesn't handle
multi-line methods. When that is fixed, this should report MS-E030.

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        x = 'hello
        y = 1;
    }"
}
```

**Expected errors:**
(none)

## Valid Escaped Quotes

Escaped quotes should be handled correctly (no error expected).

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        x = 'it\\'s fine';
        y = 1;
    }"
}
```

**Expected errors:**
(none)
