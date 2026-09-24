# AI Agent Logic Method — Specification

This folder defines the **method** that AI agents must follow when generating output for **Rewrite** and **Plan + Script** modes. All generated scripts must be converted to logic files (`md` + `json`) described here, so any AI agent can parse and execute without ambiguity.

## Core Principle
> **Never output raw code alone. Every script must be wrapped as executable logic.**

| File | Purpose | Consumer |
|------|---------|----------|
| `rewrite_spec.md` | How Rewrite mode works | AI agent prompt pipeline (`ollama_service.py: rewrite`) |
| `plan_spec.md` | How Plan mode works — Complete Detailed Plan + Script Logic | AI agent prompt pipeline (`ollama_service.py: plan`) |
| `workflow_template.json` | JSON schema for AI-executable workflow | Agent executor / parser |
| `logic_template.md` | Markdown workflow template | Human + AI agent readable steps |

## File Contract

### Logic Markdown (`logic.md`)
Human-readable but strictly structured workflow:
- `# Objective`
- `# Deliverables`
- `# Workflow Steps` (numbered, each with input/output/tool)
- `# File Tree`
- `# Execution Order`
- `# Code Blocks` (if needed, tied to steps)

### Logic JSON (`logic.json`)
Machine-parseable workflow definition validated against `workflow_template.json` schema.
Must contain:
```json
{
  "meta": { "objective": "", "version": "1.0" },
  "workflow": [ { "step": 1, "id": "setup", "action": "", "input": "", "output": "", "tool": "", "depends_on": [], "code_block": "" } ],
  "files": [ { "path": "", "purpose": "", "template": "" } ],
  "env": {},
  "acceptance_criteria": []
}
```

Any Ollama `plan` action will emit both formats consecutively.
