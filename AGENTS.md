# Project-Specific (mahlif)

**Goal**: Universal music notation interchange format (Mahlif XML) with bidirectional converters for Sibelius, Finale, Dorico, LilyPond, and MusicXML.

## Development Commands

| Command   | Purpose                                                                  |
| --------- | ------------------------------------------------------------------------ |
| `ds dev`  | **Must pass before every commit** — lint, type check, tests, spell check |
| `ds test` | Run tests only                                                           |
| `ds lint` | Run linters only                                                         |
| `ds docs` | Build documentation                                                      |

## Validation Rules

**`ds dev` is mandatory before commits.** Check the **full output**, not just the last few lines.

Common issues caught by `ds dev`:

- **cspell**: Unknown words → add to `.cspell.json`
- **ruff**: Python lint/format issues
- **ty/pyrefly/pyright/mypy**: Type errors
- **pytest**: Test failures

If `ds dev` fails, fix the issue before committing. Don't assume CI will catch it.

---

# General Principles (all projects)

## Preflight

Before starting any task:

1. Confirm you have the tools to do the work _and_ verify it succeeded
2. Identify the goal and immediate task; restate if conversation is long or after compaction
3. Check for relevant GitHub issues; add comments for significant progress
4. Clarify: **quick experiment** (user will check) or **deep dive** (use judgment)?

## Working Style

- Default to minimal changes; propose scope before larger refactors
- Don't delete files you didn't create (others may be working in same directory)
- Don't delete build artifacts needlessly; prefer idempotent approaches
- Follow existing patterns in the codebase
- Prefer editing existing files over creating new ones
- Don't add unnecessary comments or docstrings to unchanged code

## Communication

- Number items in summaries so user can reference specifics
- Present meaningful alternatives and wait—unless this is a deep dive
- If solving a different problem than started, stop and check in
- For long-running commands: `cmd 2>&1 | tee /tmp/build.log`
- If something hangs, investigate rather than waiting silently
- Notify when long-running tasks complete

## Shell Commands

| Instead of | Use  | Why                                   |
| ---------- | ---- | ------------------------------------- |
| `find`     | `fd` | Respects `.gitignore`, simpler syntax |
| `grep`     | `rg` | Faster, respects `.gitignore`         |
| `pip`      | `uv` | Faster, better dependency resolution  |

## Code Style

- Type hints with modern syntax (`Path | None` not `Optional[Path]`)
- Require 100% test coverage; task isn't complete without it
- `# pragma: no cover` only for trivial `if __name__ == "__main__"` or truly unreachable code
- Test observable behavior, not implementation details

## Workflow

1. Create an issue before implementing non-trivial changes
2. Add comments to issues when scope expands or for significant progress
3. Discuss structural/organizational changes before implementing
4. **Run validation commands and check full output** before committing
5. Commit frequently, but **do not push until asked**
6. Pushing to `main` triggers CI; batch commits to limit runs

## Commit Messages

Format: `prefix: description (#issue)`

| Prefix      | Use for                                    |
| ----------- | ------------------------------------------ |
| `add:`      | New features, files, capabilities          |
| `fix:`      | Bug fixes, corrections                     |
| `update:`   | Changes to existing functionality, docs    |
| `remove:`   | Deletions                                  |
| `refactor:` | Code restructuring without behavior change |

Rules:

- Lowercase titles, sentence fragments (no trailing period)
- Backticks for code: ``fix: bug in `keep_going` parsing``
- Reference issues: `(#123)` or `(closes #123)`
- Include `Co-Authored-By: {Model Name + Version} <noreply@anthropic.com>` in body

## GitHub Issues and Comments

- Same prefix convention as commits
- Lowercase titles; backticks for code references
- Add `aigen` label for AI-generated issues
- Start body: "Created by {Model Name + Version} during {context}..."
- Prefer flat hierarchy in markdown; use bolding appropriately

## Conventions

- Dates: ISO 8601 (`YYYY-MM-DD`)
- Prefer well-adopted standards where they exist
