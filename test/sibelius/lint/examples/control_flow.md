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

## While Statement - Missing Braces

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        x = 1;
        while (x < 5)
            x = x + 1;
    }"
}
```

**Expected errors:**
- `MS-E043` - Expected '{' after while

## For Statement - Missing Braces

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        for i = 1 to 5
            x = i;
    }"
}
```

**Expected errors:**
- `MS-E043` - Expected '{' after for

## For Each - Missing Braces

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        list = CreateSparseArray();
        for each item in list
            x = item;
    }"
}
```

**Expected errors:**
- `MS-E043` - Expected '{' after for each

## Switch - Case Without Braces

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        x = 1;
        switch (x) {
            case (1)
                y = 1;
        }
    }"
}
```

**Expected errors:**
- `MS-E043` - Expected '{' after case
- `MS-E042` - Cascading errors from missing brace

## Switch - Invalid Content

Content inside switch must be `case` or `default`.

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        x = 1;
        switch (x) {
            y = 1;
        }
    }"
}
```

**Expected errors:**
- `MS-E042` - Expected 'case' or 'default' in switch

## Valid If-Else Statement

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        x = 1;
        if (x = 1) {
            y = 1;
        } else {
            y = 2;
        }
    }"
}
```

**Expected errors:**
(none)

## Valid Nested Control Flow

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        for i = 1 to 10 {
            if (i > 5) {
                x = i;
            }
        }
    }"
}
```

**Expected errors:**
(none)

## If Statement - Missing Right Parenthesis

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        x = 1;
        if (x = 1 {
            y = 2;
        }
    }"
}
```

**Expected errors:**
- `MS-E040` - Expected ')'

## While Statement - Missing Right Parenthesis

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        x = 1;
        while (x < 5 {
            x = x + 1;
        }
    }"
}
```

**Expected errors:**
- `MS-E040` - Expected ')'

## Else If Statement

Valid else if chain.

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        x = 1;
        if (x = 1) {
            y = 1;
        } else if (x = 2) {
            y = 2;
        } else {
            y = 0;
        }
    }"
}
```

**Expected errors:**
(none)

## Standalone Block

Valid standalone block (braces without control flow).

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        x = 1;
        {
            y = 2;
        }
    }"
}
```

**Expected errors:**
(none)

## Empty Statement (Semicolon Only)

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        ;
        x = 1;
        ;
    }"
}
```

**Expected errors:**
(none)

## For Statement - Missing Loop Variable

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        for = 1 to 5 {
            x = i;
        }
    }"
}
```

**Expected errors:**
- `MS-E041` - Expected variable name after 'for'

## For Each - Missing Type or Variable After Each

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        for each in list {
            x = item;
        }
    }"
}
```

**Expected errors:**
- `MS-E041` - Expected type or variable

## Switch - Missing Left Parenthesis

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        x = 1;
        switch x {
            case (1) {
                y = 1;
            }
        }
    }"
}
```

**Expected errors:**
- `MS-E040` - Expected '('

## Switch - Missing Right Parenthesis

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        x = 1;
        switch (x {
            case (1) {
                y = 1;
            }
        }
    }"
}
```

**Expected errors:**
- `MS-E040` - Expected ')'

## For Each - Identifier Followed By Number

When an identifier follows `each`, the next token must be either another identifier (type) or `in`.

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        for each item 123 {
            x = item;
        }
    }"
}
```

**Expected errors:**
- `MS-E041` - Expected 'in'

## Switch Case - Missing Right Parenthesis

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        x = 1;
        switch (x) {
            case (1 {
                y = 1;
            }
        }
    }"
}
```

**Expected errors:**
- `MS-E040` - Expected ')'

## Switch With Comment Before Closing Brace

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        x = 1;
        switch (x) {
            case (1) { y = 1; }
            // comment before closing brace
        }
    }"
}
```

**Expected errors:**
(none)

## Switch Without Opening Brace

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        x = 1;
        switch (x)
            case (1) { y = 1; }
    }"
}
```

**Expected errors:**
- `MS-E040` - Expected '{'
- `MS-E048` - Cascading error from missing brace
- `MS-E001` - Cascading error

## For Loop With Potentially Negative End

When a for loop end value involves subtraction, it could become negative at runtime.

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "(arr) {
        for i = 0 to Length(arr) - 3 {
            x = i;
        }
    }"
}
```

**Expected errors:**
- `MS-W021` - For loop end could be negative
