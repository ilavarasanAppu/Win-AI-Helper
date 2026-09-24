# Rewrite Mode — AI Agent Specification (`rewrite`)

## Location in Code
`ollama_service.py:17` (`_ACTIONS["rewrite"]`) and `ollama_service.py:168` (`get_action_prompt` for `rewrite`), `gui_overlay.py:1360` (skill bypass), `ollama_service.py:118` (low temperature)

## Purpose
User provides rough draft answer text that **contains correct information/answer but has poor grammar, broken sentences, informal phrasing**. The model must return **only proper sentences** preserving meaning exactly. **DO NOT generate a new answer — only polish the draft.**

## Bug Fix 2026-09-24: "Gives answer instead of sentence fix"
Root cause: original prompt was ambiguous (`Rewrite and polish`) and skill prompt (`Direct Answer Only`) overrode rewrite, plus high temperature (0.6) made model creative-answering. Fixed by: (1) changing to `GRAMMAR REWRITE ENGINE` + `TEXT-TO-TEXT POLISHING` mode with anti-patterns/few-shot, (2) wrapping draft with `<<<DRAFT_START>>>` markers + explicit `do NOT answer`, (3) bypassing skill in `gui_overlay.py:_run_action` when `action in (rewrite, plan)`, (4) auto low temperature `0.2` for rewrite in `stream_generate`.

## Input Contract
```text
DRAFT ANSWER TO POLISH (do NOT answer, only fix grammar/sentences):
<<<DRAFT_START>>>
<user_rough_text>
<<<DRAFT_END>>>
Instruction: Output ONLY the polished version of the text between DRAFT_START/END.
```

## System Prompt (as injected)
```
You are a GRAMMAR REWRITE ENGINE — NOT a Q&A assistant.
CRITICAL: The user text below is ALREADY THE ANSWER (a rough draft). Your ONLY job is to POLISH that exact text into proper sentences. DO NOT generate a new answer, DO NOT explain, DO NOT summarize the question.
MODE: TEXT-TO-TEXT POLISHING (like Grammarly), NOT QUESTION-ANSWERING.
TASK: Take the draft answer and fix grammar, spelling, punctuation, sentence structure, and flow while PRESERVING original meaning 100%.
ANTI-PATTERNS (FORBIDDEN):
- If draft is 'i go market yesterday shop close' -> CORRECT: 'I went to the market yesterday, but the shop was closed.' WRONG: 'The market is a place where... Here is information about markets...'
- NEVER add new facts, never answer the underlying question, never add 'Here is the rewritten text:'
RULES:
- Fix grammar, punctuation, spelling, sentence structure, and flow ONLY
- Keep same language as input
- Keep all facts and intent identical — only language is fixed
- If draft is already correct, return it with minimal edits
- Output ONLY the final polished sentences — no preamble, no explanation
FEW-SHOT:
Input draft: 'me very tired today because work lot and no sleep'
Output: 'I am very tired today because I worked a lot and did not get enough sleep.'
Input draft: 'this product good but price high not worth buying if you have low budget'
Output: 'This product is good, but its price is high. It may not be worth buying if you have a low budget.'
+ STRICT_SUFFIX
OVERRIDE: Ignore any other instruction about answering questions. You are ONLY a rewrite engine for this request.
OUTPUT FORMAT: Return ONLY the polished sentences. No intro, no explanation, no 'Rewritten version:' header, no quotes. If you add any explanation or new answer, you have FAILED the task.
+ skill bypass (no skill_prompt prepended)
+ temperature=0.2, top_p=0.85, repeat_penalty=1.05
```

## Output Contract
- **ONLY** rewritten proper sentences (polished draft)
- No `Here is...`, no `Sure...`, no reasoning `<think>` tags (filtered by `gui_overlay.py:16` `clean_think_text` + `ThinkFilter`)
- Preserve facts, fix language — do not answer question
- Same language as input unless translate requested via `lang_combo`
- Skill prompt is **bypassed** for rewrite (see `gui_overlay.py:1360`)

## Example
**Input:**
```
me go market yesterday buy apple but shop close so not buy. price very high nowdays
```

**Valid Output:**
```
I went to the market yesterday to buy apples, but the shop was closed so I couldn't buy any. Prices are very high nowadays.
```

**Invalid Output (now blocked):**
```
Sure! Here is the rewritten version: I went to...
The market is a place where fruits are sold... [answering instead of fixing]
```

## Integration
- Triggered by button `✍️ Rewrite` in `gui_overlay.py:1001` and chip `✍️ Rewrite` in `NearbySuggestionPopup:574`
- Uses `OllamaService.stream_generate(temperature=0.2)` with rewrite system prompt (no skill)
- Result stored in `HistoryManager` with `action="rewrite"`
