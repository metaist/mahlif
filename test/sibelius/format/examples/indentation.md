# Indentation Tests

## Basic Method Indentation

Methods should be indented one level inside the plugin.

**Input:**
```manuscript
{
Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
}
```

**Expected:**
```manuscript
{
    Initialize "() {
        AddToPluginsMenu('Test', 'Run');
    }"
}
```

## Nested Blocks

Each nested block adds one indentation level.

**Input:**
```manuscript
{
Initialize "() { if (x) { if (y) { z = 1; } } }"
}
```

**Expected:**
```manuscript
{
    Initialize "() {
        if (x) {
            if (y) {
                z = 1;
            }
        }
    }"
}
```

## For Loop Indentation

**Input:**
```manuscript
{
Run "() { for i = 1 to 10 { x = i; } }"
}
```

**Expected:**
```manuscript
{
    Run "() {
        for i = 1 to 10 {
            x = i;
        }
    }"
}
```

## While Loop Indentation

**Input:**
```manuscript
{
Run "() { while (x > 0) { x = x - 1; } }"
}
```

**Expected:**
```manuscript
{
    Run "() {
        while (x > 0) {
            x = x - 1;
        }
    }"
}
```

## Switch Statement Indentation

**Input:**
```manuscript
{
Run "() { switch (x) { case (1) { y = 1; } default { y = 0; } } }"
}
```

**Expected:**
```manuscript
{
    Run "() {
        switch (x) {
            case (1) {
                y = 1;
            }
            default {
                y = 0;
            }
        }
    }"
}
```
