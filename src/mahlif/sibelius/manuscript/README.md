# ManuScript Language Data

This directory contains data about the ManuScript language for linting,
code completion, and eventually an LSP server.

## Files

### `lang.json` - Language Definition

Comprehensive language data extracted from the ManuScript Language PDF:

- **objects**: Object types (Bar, Staff, Note, etc.) with methods and properties
- **constants**: Global constants (True, False, Quarter, Whole, MiddleOfWord, etc.)
- **builtin_functions**: Global functions (CreateSparseArray, Chr, Trace, etc.)

```json
{
  "objects": {
    "Bar": {
      "description": "A Bar contains BarObject objects.",
      "methods": {
        "AddNote": {
          "signatures": [{"params": ["pos", "pitch", "dur", ...], "min_params": 3, "max_params": 7}]
        }
      },
      "properties": ["BarNumber", "Length", ...]
    }
  },
  "constants": {
    "True": 1,
    "Quarter": 256,
    "MiddleOfWord": 0
  },
  "builtin_functions": {
    "CreateSparseArray": {"returns": "SparseArray", "params": []}
  }
}
```

### `extract.py` - Language Extractor

Extracts `lang.json` from the ManuScript Language PDF.

```bash
pdftotext "ManuScript Language.pdf" - | python extract.py > lang.json
```

When a new version of ManuScript is released, re-run this to regenerate.

## Other Files

- `checker.py` - Syntax/semantic checker for method bodies
- `tokenizer.py` - Lexer for method body content
- `ast.py` - AST node definitions
- `errors.py` - Error code definitions

## Future: LSP Architecture

The `lang.json` file provides everything needed for an LSP:

- **Completion**: Object methods/properties, constants, functions
- **Hover**: Descriptions, signatures
- **Diagnostics**: Undefined variables, wrong parameter counts
- **Signature help**: Method parameter info
