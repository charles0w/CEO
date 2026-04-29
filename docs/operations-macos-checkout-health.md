# macOS checkout health notes

Date: 2026-04-29

## Problem observed

The CEO repo lives under `~/Desktop`, which can be managed by iCloud/Optimize Mac Storage. During validation, macOS repeatedly converted tracked files and `.git` internals into `compressed,dataless` placeholders.

Symptoms seen:
- `git status` failed with `short read while indexing ...`
- `git` temporarily reported `not a git repository` after `.git/HEAD` and refs became dataless
- `npm install` failed with `EJSONPARSE` because `mobile/package.json` read as an empty file
- `npx tsc --noEmit` stalled while dependency files in `mobile/node_modules` were dataless

## Recovery that worked

A fresh clone outside Desktop had fully materialized files:

```bash
rm -rf /tmp/CEO-fresh
git clone https://github.com/charles0w/CEO.git /tmp/CEO-fresh
```

The Desktop checkout was repaired by restoring the already-pushed repository state from that clone and materializing tracked files by writing their bytes into the Desktop checkout.

After repair:
- `git status --short --branch` returned cleanly
- tracked files no longer reported `compressed,dataless`
- `npm ci --legacy-peer-deps --no-audit` succeeded
- full `npx tsc --noEmit --pretty false` completed successfully

## Practical recommendation

For long-running local development, keep the active repo outside iCloud-managed Desktop/Documents if possible, for example under `~/dev/CEO`. If keeping it on Desktop, expect to occasionally rehydrate files before running Git, npm, or TypeScript checks.
