# ManuScript Format Test Examples

This directory contains formatting examples as input/expected output pairs.

Each `.md` file contains test cases in the format:

````markdown
## Test Name

Description of what this test checks.

**Input:**

```manuscript
{ unformatted code }
```

**Expected:**

```manuscript
{ formatted code }
```
````

The test runner parses these files and verifies that formatting the input
produces the expected output.
