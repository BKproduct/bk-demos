# Skill: Continuous Learning

> **What it does:** After any complex AI session, one command makes the AI extract reusable patterns, save them as structured files, and apply them automatically in future sessions. Your agent gets smarter every day.

---

## How to Install

1. Create a folder in your project: `.cursor/skills/continuous-learning/learned/`
2. Save this file as `.cursor/skills/continuous-learning/SKILL.md`
3. That's it — the skill is live.

**Trigger phrases:**
- `"save what you learned"`
- `"remember this pattern"`
- `"extract a skill from this session"`
- `"continuous learning"`

Also triggers **automatically** at the end of complex multi-step sessions where a novel workflow, workaround, or debugging technique emerged.

---

## What It Does

Scans the current session for patterns worth remembering. Saves them as `.md` files your agent reads automatically in future sessions.

### Pattern categories it looks for:

| Category | What it captures |
|---|---|
| `error_resolution` | How a specific error was diagnosed and fixed |
| `user_corrections` | Cases where you corrected the agent's approach |
| `workarounds` | Non-obvious solutions to library/framework quirks |
| `debugging_techniques` | Effective step-by-step debug sequences |
| `project_specific` | Your conventions, folder structures, naming patterns |

### What it does NOT extract:
- One-time typo fixes
- Simple factual lookups
- External API issues outside your control

---

## Workflow

### Step 1 — Scan
Agent reviews the session and drafts patterns in this format:

```
Name: <short-slug>
Category: <error_resolution / user_corrections / workarounds / debugging_techniques / project_specific>
Problem: <one sentence — what situation triggers this>
Solution: <concise steps or code snippet>
Example: <concrete instance from this session>
```

### Step 2 — Confirm
Agent presents drafts and asks:
> "I found [N] pattern(s) worth saving. Save all / select / skip?"

### Step 3 — Save
Approved patterns written to:
```
<YOUR_SKILLS_DIR>/continuous-learning/learned/YYYY-MM-DD-<slug>.md
```

File template:
```markdown
---
name: <slug>
category: <category>
learned_date: <YYYY-MM-DD>
session_context: <one-line description of the session>
---

## Problem
<When does this situation arise?>

## Solution
<Steps or code snippet>

## Example (from session)
<Concrete instance>
```

### Step 4 — Index
Appends a row to `learned/INDEX.md`:
```
| YYYY-MM-DD | <slug> | <category> | <one-line summary> |
```
Creates the file with a header row if it doesn't exist.

---

## Applying Learned Patterns in Future Sessions

At the start of a session, if a task resembles a previously learned pattern, the agent reads the relevant file from `learned/` and applies it. It checks `INDEX.md` first for a fast scan.

**No configuration needed.** The agent finds the files automatically if the folder structure is in place.

---

## Setup Checklist

- [ ] Folder created: `<YOUR_SKILLS_DIR>/continuous-learning/learned/`
- [ ] This file saved as `SKILL.md` in `<YOUR_SKILLS_DIR>/continuous-learning/`
- [ ] (Optional) Add trigger phrases to your `CLAUDE.md` or `cursor rules`

---

## Why This Works

Most AI coding assistants repeat the same mistakes across sessions because they have no persistent memory of what went wrong. This skill gives your agent a structured, searchable memory of hard-won lessons — without any external service, database, or API.

**Cost:** Zero. Pure local markdown files.
**Payoff:** Compounds. Every session makes the next one faster.
