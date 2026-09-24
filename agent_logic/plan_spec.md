# Plan Mode — Complete Detailed Plan + Script Logic Specification (`plan`)

## Location in Code
`ollama_service.py:26` (`_ACTIONS["plan"]`) and `ollama_service.py:151` (`get_action_prompt` for `plan`)

## Purpose
User provides any objective/context. Model must return **TWO mandatory parts**:
1. **Complete Detailed Plan** (Markdown, thorough — not vague)
2. **Script Logic as AI-Agent Understandable Method** (both `logic.md` + `logic.json`)

This ensures even non-technical agents can execute the plan.

## Input Contract
```text
Objective/Context to plan:
"""
<user_objective>
"""

Generate the Complete Detailed Plan + Script Logic (md + json) now.
```

## System Prompt (as injected)
```
You are an expert planner and solution architect. ... (see ollama_service.py:_ACTIONS["plan"])
+ STRICT_SUFFIX
+ OUTPUT FORMAT (MANDATORY):
# PART 1: COMPLETE DETAILED PLAN
## 1. Objective & Scope
## 2. Deliverables
## 3. Step-by-Step Plan (Phased, with P0/P1/P2)
## 4. Milestones & Timeline
## 5. Resources & Dependencies
## 6. Risks & Mitigations
## 7. Acceptance Criteria

# PART 2: SCRIPT LOGIC - AI Agent Method
## logic.md (Workflow in Markdown)
```markdown
[workflow steps + file tree + execution order]
```
## logic.json (Executable Workflow)
```json
{ "workflow": [...], "files": [...], "env": {} }
```
```

## Output Contract — PART 1: Complete Detailed Plan

### Required Sections (all must appear)
| Section | Content |
|---------|---------|
| **1. Objective & Scope** | Restate objective, in-scope / out-of-scope, assumptions |
| **2. Deliverables** | Concrete outputs, file names, artifacts |
| **3. Step-by-Step Plan** | Phases (e.g., Phase 1: Setup, Phase 2: Core). Each step: `What / Why / How / Owner / Output` + Priority `P0` (critical) `P1` (important) `P2` (nice-to-have) |
| **4. Milestones & Timeline** | Dates or relative timeline (e.g., Day 1, Week 1), exit criteria per milestone |
| **5. Resources & Dependencies** | Tools, APIs, models, env vars, external services |
| **6. Risks & Mitigations** | At least 2-3 risks with mitigation and fallback |
| **7. Acceptance Criteria** | Definition of Done, measurable checks |

No vague bullet like "Do research" — must be actionable.

## Output Contract — PART 2: Script Logic (AI-Agent Method)

### Why `md` + `json`?
- **md**: Human-readable workflow + pseudocode + file tree + execution order
- **json**: Machine-parseable workflow that an AI agent can load and execute step-by-step

### Rules
- **NEVER** output raw standalone code without wrapping it as logic steps
- Code (if needed) appears **inside** logic structure: as fenced code in `logic.md` and as `code_block` field in `logic.json` `workflow` entries
- If no code is needed, still emit `logic.json` with workflow steps the agent can follow manually
- JSON must be valid (no trailing commas, double quotes)
- Markdown must use headings exactly as template

### logic.md Template
```markdown
# Workflow: <title>
## File Tree
```
project/
  main.py
  config.json
```
## Execution Order
1. setup -> 2. core -> 3. test -> 4. deploy
## Steps
### Step 1: Setup Environment [P0]
- Input: ...
- Output: ...
- Tool: bash / python / ollama
- Action: ...
```python
# code for step 1
```
```

### logic.json Schema
See `agent_logic/workflow_template.json`. Minimal valid example:
```json
{
  "meta": { "objective": "Build XYZ", "version": "1.0" },
  "workflow": [
    { "step": 1, "id": "setup", "action": "Create project structure", "input": "objective", "output": "folder structure", "tool": "bash", "depends_on": [], "code_block": "mkdir project" },
    { "step": 2, "id": "implement", "action": "Implement core logic", "input": "spec", "output": "main.py", "tool": "python", "depends_on": ["setup"], "code_block": "print('hello')" }
  ],
  "files": [
    { "path": "main.py", "purpose": "Main entry", "template": "python" }
  ],
  "env": { "python_version": "3.10" },
  "acceptance_criteria": ["Workflow completes without error", "Output matches spec"]
}
```

## Example (Truncated)
**Input:** `Build a Python script to scrape NSE stock price`

**Valid Output (excerpt):**
```markdown
# PART 1: COMPLETE DETAILED PLAN
## 1. Objective & Scope
Objective: Scrape NSE stock price for given symbol...
Scope: Intraday price only...

# PART 2: SCRIPT LOGIC - AI Agent Method
## logic.md
...
## logic.json
```json
{ "meta": {...}, "workflow": [...] }
```
```

## Integration
- Triggered by button `📋 Plan` in `gui_overlay.py:1003`
- Uses `OllamaService.stream_generate()` with plan system prompt
- Result is streamed to `output_view` and stored in history as `action="plan"`
- Both md and json are preserved in history so agents can retrieve

## Validation Checklist for Model Output
- [ ] PART 1 has all 7 sections
- [ ] Each step has P0/P1/P2 and owner/output
- [ ] PART 2 has `logic.md` code fence and `logic.json` code fence
- [ ] logic.json is valid JSON and matches `workflow_template.json` schema
- [ ] No raw code outside logic structure

