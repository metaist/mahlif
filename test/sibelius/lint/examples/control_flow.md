# Control Flow Syntax Tests

Tests for `if`, `while`, `for`, and `switch` statement syntax.

## If Statement - Missing Parentheses

The `if` statement requires parentheses around the condition.

> The rule for if takes the form `if (condition) {statements}`.
> — ManuScript Language Guide, page xxii

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        if x = 1 {
            y = 2;
        }
    }"
}
```

**Expected errors:**
- `MS-E040` - Expected '(' after 'if'

## If Statement - Missing Braces

Braces are required even for single statements.

> As with while, the parentheses and braces are compulsory.
> — ManuScript Language Guide, page xxii

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        if (x = 1)
            y = 2;
    }"
}
```

**Expected errors:**
- `MS-E043` - Expected '{' after if

## While Statement - Missing Parentheses

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        while x < 5 {
            x = x + 1;
        }
    }"
}
```

**Expected errors:**
- `MS-E040` - Expected '(' after 'while'

## For Statement - Missing Equals

The `for` loop syntax is `for var = start to end { }`.

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        for i 1 to 5 {
            x = i;
        }
    }"
}
```

**Expected errors:**
- `MS-E040` - Expected '=' in for statement

## For Statement - Missing To

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        for i = 1 5 {
            x = i;
        }
    }"
}
```

**Expected errors:**
- `MS-E040` - Expected 'to' in for statement

## For Each - Missing In

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        for each note staff {
            x = note;
        }
    }"
}
```

**Expected errors:**
- `MS-E040` - Expected 'in' in for each statement

## Switch - Case Without Parentheses

The `case` clause requires parentheses: `case (value) { }`.

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        x = 1;
        switch (x) {
            case 1 {
                y = 1;
            }
        }
    }"
}
```

**Expected errors:**
- `MS-E040` - Expected '(' after 'case'
