# Variable Tests

Tests for variable-related checks.

## Undefined Variable

Variables must be defined before use.

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        x = y + 1;
    }"
}
```

**Expected errors:**

- `MS-W020` - Variable 'y' may be undefined

## Variable Defined by Assignment

Variables are defined when assigned.

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        x = 1;
        y = x + 1;
    }"
}
```

**Expected errors:**
(none)

## Parameters Are Defined

Method parameters are considered defined.

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "(a, b) {
        x = a + b;
    }"
}
```

**Expected errors:**
(none)

## Built-in Globals

Built-in objects like `Sibelius` are always defined.

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        score = Sibelius.ActiveScore;
        arr = CreateSparseArray();
    }"
}
```

**Expected errors:**
(none)

## For Loop Variable

Loop variables are defined within the loop body.

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        for i = 1 to 10 {
            x = i;
        }
    }"
}
```

**Expected errors:**
(none)

## Plugin With No Variables

A plugin with only methods and no variable declarations.

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        Sibelius.MessageBox('Hello');
    }"
}
```

**Expected errors:**
(none)
