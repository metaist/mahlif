# Plugin Structure Tests

Tests for plugin-level structure issues like method definitions.

## Unescaped Double Quote in Method Body

Double quotes inside method bodies must be escaped since the body itself is wrapped in double quotes.

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    BuildLocation "(page) {
        // Build "p4 [B]" string
        beat = 1;
    }"
}
```

**Expected errors:**

- `MS-E050` - Unescaped double quote in method body
