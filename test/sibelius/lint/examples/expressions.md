# Expression Syntax Tests

Tests for expression parsing and operators.

## Empty Assignment

Assignment requires a value on the right side.

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        x = ;
    }"
}
```

**Expected errors:**
- `MS-E048` - Unexpected token ';'

## Incomplete Binary Expression

Binary operators require operands on both sides.

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        y = 1 + ;
    }"
}
```

**Expected errors:**
- `MS-E046` - Expected expression after operator

## Missing Semicolon

Statements must end with a semicolon.

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        x = 1
        y = 2;
    }"
}
```

**Expected errors:**
- `MS-E044` - Expected ';' after statement

## Missing Property Name

Property access requires a name after the dot.

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        x = obj.;
    }"
}
```

**Expected errors:**
- `MS-E047` - Expected property or method name after '.'

## Unclosed Parenthesis in Expression

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

## Unclosed Function Call

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        x = Foo(1, 2;
    }"
}
```

**Expected errors:**
- `MS-E040` - Expected ')' to close function call
