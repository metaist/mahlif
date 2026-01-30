# Spacing Tests

## Assignment Operator

Space around `=`.

**Input:**
```manuscript
{
Run "() { x=1; }"
}
```

**Expected:**
```manuscript
{
    Run "() {
        x = 1;
    }"
}
```

## Arithmetic Operators

Space around `+`, `-`, `*`, `/`.

**Input:**
```manuscript
{
Run "() { x=a+b*c-d/e; }"
}
```

**Expected:**
```manuscript
{
    Run "() {
        x = a + b * c - d / e;
    }"
}
```

## Comparison Operators

Space around `<`, `>`, `<=`, `>=`, `!=`.

**Input:**
```manuscript
{
Run "() { if (x<5) { y=1; } }"
}
```

**Expected:**
```manuscript
{
    Run "() {
        if (x < 5) {
            y = 1;
        }
    }"
}
```

## Logical Operators

Space around `and`, `or`.

**Input:**
```manuscript
{
Run "() { if (x and y or z) { a=1; } }"
}
```

**Expected:**
```manuscript
{
    Run "() {
        if (x and y or z) {
            a = 1;
        }
    }"
}
```

## Comma Spacing

Space after comma, not before.

**Input:**
```manuscript
{
Run "() { foo(a,b,c); }"
}
```

**Expected:**
```manuscript
{
    Run "() {
        foo(a, b, c);
    }"
}
```

## Keyword Spacing

Space after `if`, `while`, `for`, `switch`, `case`.

**Input:**
```manuscript
{
Run "() { if(x){ y=1; } }"
}
```

**Expected:**
```manuscript
{
    Run "() {
        if (x) {
            y = 1;
        }
    }"
}
```

## No Space Around Dot

Method calls have no space around `.`.

**Input:**
```manuscript
{
Run "() { Sibelius . MessageBox ( 'hi' ); }"
}
```

**Expected:**
```manuscript
{
    Run "() {
        Sibelius.MessageBox('hi');
    }"
}
```

## No Space Inside Parentheses

**Input:**
```manuscript
{
Run "() { foo( a, b ); }"
}
```

**Expected:**
```manuscript
{
    Run "() {
        foo(a, b);
    }"
}
```

## No Space Inside Brackets

**Input:**
```manuscript
{
Run "() { x = arr[ 0 ]; }"
}
```

**Expected:**
```manuscript
{
    Run "() {
        x = arr[0];
    }"
}
```
