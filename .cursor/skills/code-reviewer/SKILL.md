---
name: code-reviewer
description: Review code and Home Assistant YAML for bugs, correctness, and maintainability. Use only when the user explicitly asks for a code review or names this skill (/code-reviewer).
disable-model-invocation: true
---

# Code Reviewer

Review local changes in this home-server repo. Do not fix findings unless the user asks.

## Scope

Default to uncommitted changes (`git diff` + `git diff --staged` + untracked files). If the user names a branch, PR, or file set, review that instead.

Skip generated and runtime noise:

- `homeassistant/.storage/`, logs, `*.db`, `.ha_run.lock`
- `printing/venv/`, `printing/downloads/`, `printing/output/`
- HACS / third-party under `homeassistant/custom_components/` unless the user changed it

## Output

Lead with a one-line verdict, then a table sorted by severity (highest first):

| Severity | Location | Finding |
| --- | --- | --- |
| Critical / Suggestion / Nice to have | `file:line` | Short issue and why it matters |

- **Critical**: Broken behavior, invalid HA config, secrets leak, data loss
- **Suggestion**: Likely bug, fragile pattern, missing error path
- **Nice to have**: Clarity, duplication, naming

If nothing is wrong, say so in one sentence. Do not invent issues.

## General checklist

- Logic matches the stated intent; edge cases (empty list, timeout, missing entity) are handled
- Names, IDs, and call sites stay in sync
- No secrets, tokens, or passwords in committed files
- Changes stay small; do not suggest unrelated refactors

## Home Assistant

This repo mounts `./homeassistant` as HA `/config`. Split files:

| Key | File |
| --- | --- |
| `automation` | `homeassistant/automations.yaml` |
| `script` | `homeassistant/scripts.yaml` |
| `rest_command` | `homeassistant/rest_commands.yaml` |
| `intent_script` | `homeassistant/intent_scripts.yaml` |
| Assist sentences | `homeassistant/custom_sentences/sv/*.yaml` |

When those files change, check:

1. **Wiring**: Intent names match `intent_scripts.yaml`. Scripts call existing `script.*` / `rest_command.*`. REST URLs and JSON payloads match the printing API.
2. **YAML / templates**: Valid YAML; Jinja `{{ }}` in the right fields; `tojson` for JSON payloads; `response_variable` used before it is read.
3. **Modern syntax**: Prefer `action:` over deprecated `service:`. Quote templates that would otherwise be parsed as YAML.
4. **Modes**: `single` vs `queued` vs `restart` fits the side effect (printing should not stampede).
5. **Entities**: `entity_id` values look real (todo, tts, media_player). Flag hardcoded IDs that the change just broke.
6. **Voice**: Custom sentences are Swedish (`language: "sv"`). Speech/TTS text should stay Swedish unless the user switched language.
7. **Secrets**: Real credentials belong in `homeassistant/secrets.yaml` via `!secret`. Never commit live passwords. `.gitignore` must keep covering secrets.
8. **Reload impact**: Note if the user must reload scripts, automations, or Assist — not just YAML-check.

Do not propose HA Cloud, Nabu Casa, or new integrations unless the change already needs them.
