# Brace Matching Tests

Tests for brace, bracket, and parenthesis matching.

## Mismatched Braces

Opening and closing braces must match in type.

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        arr = CreateSparseArray();
        arr[0] = 1;
        x = (arr[0];
    }"
}
```

**Expected errors:**
- `MS-E040` - Expected ')' after expression

## Unclosed Parenthesis

All opening parentheses must have matching closing parentheses.

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        x = (1 + 2;
    }"
}
```

**Expected errors:**
- `MS-E040` - Expected ')' after expression

## Balanced Braces

All braces properly matched (no errors expected).

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        if (x) {
            arr[0] = (1 + 2);
        }
    }"
}
```

**Expected errors:**
(none)
