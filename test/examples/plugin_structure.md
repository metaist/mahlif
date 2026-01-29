# Plugin Structure Tests

Tests for overall plugin file structure.

## Missing Opening Brace

A plugin file must start with `{`.

```manuscript
Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
Run "() { }"
}
```

**Expected errors:**
- `MS-E010` - Plugin must start with '{'
- `MS-E001` - Unmatched closing '}'

## Missing Closing Brace

A plugin file must end with `}`.

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() { }"
```

**Expected errors:**
- `MS-E003` - Unclosed '{'
- `MS-E011` - Plugin must end with '}'

## Missing Initialize Method

Every plugin should have an `Initialize` method.

```manuscript
{
    Run "() { }"
}
```

**Expected errors:**
- `MS-W010` - Missing 'Initialize' method

## Initialize Without AddToPluginsMenu

The `Initialize` method should call `AddToPluginsMenu` to add the plugin to the menu.

```manuscript
{
    Initialize "() { x = 1; }"
    Run "() { }"
}
```

**Expected errors:**
- `MS-W011` - Initialize should call 'AddToPluginsMenu'

## Valid Minimal Plugin

A minimal valid plugin (no errors expected).

```manuscript
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() { }"
}
```

**Expected errors:**
(none)
