# ManuScript Lint Test Examples

This directory contains example ManuScript code with expected lint errors.
Each `.md` file contains one or more test cases in the following format:

~~~markdown
## Test Name

Description of what this test checks.

```manuscript
{ code here }
```

**Expected errors:**
- `MS-E040` - Expected '(' after 'if'
- `MS-W002` - Trailing whitespace

**Reference:** ManuScript Language Guide, page xxii
~~~

The test runner (`test/test_lint_examples.py`) parses these files and:
1. Extracts the code from `manuscript` code blocks
2. Runs the linter on the code
3. Compares actual error codes against expected codes

## Adding New Tests

1. Create or edit a `.md` file in this directory
2. Add a `## Test Name` heading
3. Add a `manuscript` code block with the code to check
4. Add `**Expected errors:**` followed by a list of error codes
5. Optionally add `**Reference:**` to cite the ManuScript Language Guide

## Error Code Prefixes

- `MS-E0xx` - Syntax errors (structure, braces)
- `MS-E02x` - Method call errors (wrong arg count)
- `MS-E03x` - Tokenization errors (bad strings, chars)
- `MS-E04x` - Parse errors (control flow, expressions)
- `MS-W0xx` - Warnings (style, conventions)
