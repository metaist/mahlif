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
        x = Substring('hello', 1, 2;
    }"
}
```

**Expected errors:**
- `MS-E040` - Expected ')' to close function call

## Incomplete Binary Expression

Missing operand after operator.

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        x = 1 +;
    }"
}
```

**Expected errors:**
- `MS-E046` - Expected expression after operator

## Missing Property Name

Dot notation requires a property name.

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        obj = Sibelius;
        x = obj.;
    }"
}
```

**Expected errors:**
- `MS-E047` - Expected property name after '.'

## Unclosed Parenthesis

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        x = (1 + 2;
    }"
}
```

**Expected errors:**
- `MS-E040` - Expected ')'

## Unclosed Function Call

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        x = Sibelius.MessageBox('hello';
    }"
}
```

**Expected errors:**
- `MS-E040` - Expected ')' or ','

## Unclosed Array Index

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        arr = CreateSparseArray();
        x = arr[0;
    }"
}
```

**Expected errors:**
- `MS-E040` - Expected ']'

## Unexpected Closing Brace

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        x = 1;
        }
        y = 2;
    }"
}
```

**Expected errors:**
- `MS-E001` - Unexpected '}'

## Valid Chained Method Call

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        x = Sibelius.ActiveScore.NthStaff(1).FullInstrumentName;
    }"
}
```

**Expected errors:**
(none)

## Valid Complex Expression

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        a = 1;
        b = 2;
        c = 3;
        x = (a + b) * c;
    }"
}
```

**Expected errors:**
(none)

## Missing Operand After Multiplication

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        x = 2 *;
    }"
}
```

**Expected errors:**
- `MS-E046` - Expected expression after operator

## Missing Operand After Division

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        x = 10 /;
    }"
}
```

**Expected errors:**
- `MS-E046` - Expected expression after operator

## User Property Syntax Error

The `:` in user property syntax must be followed by a property name.

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        obj = Sibelius;
        x = obj._property:;
    }"
}
```

**Expected errors:**
- `MS-E047` - Expected property name after ':'

## Empty Expression in Call

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        Sibelius.MessageBox();
    }"
}
```

**Expected errors:**
(none)

## Valid User Property

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        obj = Sibelius.ActiveScore;
        x = obj._property:Name;
    }"
}
```

**Expected errors:**
(none)

## Trailing Comma in Function Call

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        Sibelius.MessageBox('hello',);
    }"
}
```

**Expected errors:**
(none)

## Empty Expression Where Expected

An expression is expected but none provided.

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() {
        if () {
            x = 1;
        }
    }"
}
```

**Expected errors:**
- `MS-E045` - Expected expression
