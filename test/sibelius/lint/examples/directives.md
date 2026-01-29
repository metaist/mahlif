# Inline Directive Tests

Tests for inline lint suppression directives.

## noqa Comment

The `// noqa` comment suppresses errors on the same or next line.

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() { }" 
}
```

**Expected errors:**
- `MS-W002` - Trailing whitespace

NOTE: The line `Run "() { }" ` has trailing whitespace. Adding `// noqa: MS-W002` 
would suppress this error, but we can't test suppression in the example format
since we're testing what errors ARE reported.

## mahlif:ignore Comment

The `// mahlif: ignore MS-XXXX` comment works like noqa for specific codes.

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() { }"  // mahlif: ignore MS-W002
}
```

**Expected errors:**
(none)

## mahlif:disable/enable Region

The `// mahlif: disable` and `// mahlif: enable` comments create regions
where specific errors are suppressed.

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    // mahlif: disable MS-W002
    Run "() { }" 
    Other "() { }" 
    // mahlif: enable MS-W002
}
```

**Expected errors:**
(none)
