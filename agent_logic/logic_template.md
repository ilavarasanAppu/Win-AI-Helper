# Workflow: <TITLE> — Logic Template (Markdown)

> Copy this template for every `plan` PART 2 `logic.md`. Fill all placeholders.

## Objective
<one-line restated objective>

## Deliverables
- `path/to/file` — purpose
- ...

## File Tree
```
project/
├── main.py          # Core logic
├── config.json      # Config / env
├── logic.md         # This workflow (human-readable)
└── logic.json       # Machine workflow (executable)
```

## Execution Order
```
setup → fetch → analyze → render → validate
```

## Steps

### Step 1: Setup Environment [P0]
- **ID:** `setup`
- **Action:** Create structure and install deps
- **Input:** objective
- **Output:** project folder + requirements
- **Tool:** `bash`
- **Depends on:** none
- **Validation:** Folder exists, pip succeeded
```bash
mkdir project && pip install -r requirements.txt
```

### Step 2: Core Implementation [P0]
- **ID:** `implement`
- **Action:** Implement main logic
- **Input:** spec from Plan Part 1
- **Output:** `main.py`
- **Tool:** `python`
- **Depends on:** `setup`
- **Validation:** File exists and runs without error
```python
# code for core logic
def main():
    pass
```

### Step 3: Test / Validate [P1]
- **ID:** `validate`
- **Action:** Run acceptance checks
- **Input:** output from Step 2
- **Output:** pass/fail
- **Tool:** `bash`
- **Depends on:** `implement`
```bash
python main.py --test
```

## Risks & Fallbacks
- Risk: API down → Fallback: cached data + retry with backoff

## Acceptance Criteria
- [ ] Workflow completes end-to-end
- [ ] Outputs match Deliverables
- [ ] No secrets in repo
