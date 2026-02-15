---
name: new-task
description: Structured approach for new development tasks. Creates feature branches, phased development plans, and checkpoint testing. Use when starting a new feature, implementing a spec, or beginning any substantial development work. Triggers on "new task", "new feature", "start development", "implement feature", or "create spec".
---

# New Task Skill

Guides structured development from scope to completion with phased checkpoints.

## Workflow

```
1. Scope & Spec → 2. Create Branch → 3. Development Plan → 4. Implement Phases → 5. Merge
```

## Step 1: Gather Scope & Spec

Ask the user for:

| Question | Purpose |
|----------|---------|
| What is the feature/task? | Define objective |
| What are the requirements? | Understand constraints |
| What's the expected outcome? | Define success criteria |
| Any dependencies? | Identify blockers |

Document answers before proceeding.

## Step 2: Create Feature Branch

```bash
git checkout -b feature/<task-name>
```

Naming conventions:
- `feature/<name>` - New features
- `fix/<name>` - Bug fixes
- `refactor/<name>` - Code restructuring

## Step 3: Create Development Plan

Create `DEVPLAN.md` in project root:

```markdown
# Development Plan: <Task Name>

## Objective
<What we're building and why>

## Requirements
- [ ] Requirement 1
- [ ] Requirement 2

## Phases

### Phase 1: <Name>
**Goal**: <What this phase accomplishes>

**Tasks**:
- [ ] Task 1
- [ ] Task 2

**Checkpoint**: <How to verify phase completion>

---

### Phase 2: <Name>
**Goal**: <What this phase accomplishes>

**Tasks**:
- [ ] Task 1
- [ ] Task 2

**Checkpoint**: <How to verify phase completion>

---

## Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2
```

## Step 4: Implement Phases

For each phase:

1. **Announce phase start** - State what you're implementing
2. **Implement tasks** - Complete all tasks in the phase
3. **Run checkpoint** - Execute verification steps
4. **Confirm with user** - Get approval before next phase

### Checkpoint Types

| Type | Example |
|------|---------|
| Build | `npm run build` passes |
| Test | `pytest` passes |
| Manual | User verifies UI looks correct |
| Runtime | Application runs without errors |

## Step 5: Complete & Merge

After all phases complete:

```bash
git add -A
git commit -m "feat(<scope>): <description>"
git checkout master
git merge feature/<task-name>
git branch -d feature/<task-name>
```

## Quick Reference

| Step | Action |
|------|--------|
| 1 | Ask: What? Requirements? Outcome? Dependencies? |
| 2 | `git checkout -b feature/<name>` |
| 3 | Create DEVPLAN.md with phases |
| 4 | Implement → Checkpoint → Confirm → Repeat |
| 5 | Commit, merge, delete branch |
