# Structure Tests

## Empty Plugin

**Input:**
```manuscript
{
}
```

**Expected:**
```manuscript
{
}
```

## Empty Method Body

**Input:**
```manuscript
{
Run "() { }"
}
```

**Expected:**
```manuscript
{
    Run "() { }"
}
```

## Variable Definition

Variable definitions (non-method strings) are preserved.

**Input:**
```manuscript
{
MyVar "some value"
Initialize "() { }"
}
```

**Expected:**
```manuscript
{
    MyVar "some value"
    Initialize "() { }"
}
```

## Multiple Methods

**Input:**
```manuscript
{
Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
Run "() { x = 1; }"
}
```

**Expected:**
```manuscript
{
    Initialize "() {
        AddToPluginsMenu('Test', 'Run');
    }"
    Run "() {
        x = 1;
    }"
}
```

## Method With Parameters

**Input:**
```manuscript
{
DoSomething "(a, b, c) { x = a + b + c; }"
}
```

**Expected:**
```manuscript
{
    DoSomething "(a, b, c) {
        x = a + b + c;
    }"
}
```

## Comments Preserved

**Input:**
```manuscript
{
Run "() { // comment
x = 1; }"
}
```

**Expected:**
```manuscript
{
    Run "() {
        // comment
        x = 1;
    }"
}
```

## Multiple Statements

**Input:**
```manuscript
{
Run "() { x = 1; y = 2; z = 3; }"
}
```

**Expected:**
```manuscript
{
    Run "() {
        x = 1;
        y = 2;
        z = 3;
    }"
}
```

## Return Statement

**Input:**
```manuscript
{
GetValue "() { return 42; }"
}
```

**Expected:**
```manuscript
{
    GetValue "() {
        return 42;
    }"
}
```

## If-Else Statement

**Input:**
```manuscript
{
Run "() { if (x) { y = 1; } else { y = 2; } }"
}
```

**Expected:**
```manuscript
{
    Run "() {
        if (x) {
            y = 1;
        } else {
            y = 2;
        }
    }"
}
```

## For Each Statement

**Input:**
```manuscript
{
Run "() { for each item in list { x = item; } }"
}
```

**Expected:**
```manuscript
{
    Run "() {
        for each item in list {
            x = item;
        }
    }"
}
```

## Comment at Plugin Level

**Input:**
```manuscript
{
// This is a comment
Initialize "() { }"
}
```

**Expected:**
```manuscript
{
    // This is a comment
    Initialize "() { }"
}
```

## Blank Lines Between Members

**Input:**
```manuscript
{
Initialize "() { }"

Run "() { }"
}
```

**Expected:**
```manuscript
{
    Initialize "() { }"

    Run "() { }"
}
```
