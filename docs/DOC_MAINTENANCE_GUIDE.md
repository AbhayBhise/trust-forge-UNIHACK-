**Version:** 1.0
**Date:** 2026-08-18
**Owner:** All Contributors
**Status:** Active
**Last Updated:** 2026-08-18

# Doc Maintenance Guide

This file tells every team member (and their AI agents) how to keep docs accurate. **Every time you change code, update the corresponding doc in the same commit.**

---

## Rule: Code Changes → Doc Changes

| If you change... | You must also update... |
|-------------------|------------------------|
| `pipeline.py` (add/remove/rename step) | `ARCHITECTURE.md` pipeline steps table |
| `models.py` (add/remove/rename field) | `DATA_MODEL.md` field listings |
| `server.py` (add/remove/change route) | `API_CONTRACT.md` endpoint docs |
| `config_appliances.py` (add attribute) | `ARCHITECTURE.md` module descriptions |
| `frontend/app.js` (add/remove view) | `PROJECT_STATUS.md` frontend section |
| Any test file (add/remove test) | `QUALITY_ASSURANCE.md` test table, `PROJECT_STATUS.md` test files |
| Add new file to `files/` | `ARCHITECTURE.md` folder structure |
| Fix a bug that was in TECHNICAL_DEBT.md | Update that item to RESOLVED |
| Add new tech debt | Add entry to `TECHNICAL_DEBT.md` |

---

## How to Update Each Doc

### `docs/ARCHITECTURE.md`
- Keep pipeline steps table accurate (step number, function name, description)
- Keep folder structure listing complete (every `.py` file in `files/`)
- Keep module responsibilities accurate
- Update performance characteristics if throughput changes

### `docs/API_CONTRACT.md`
- Every endpoint must match `server.py` exactly — same route, same params, same response fields
- Never document params that don't exist in the function signature
- Never document response fields that aren't in the `return` statement
- If you add a route, document it here in the same PR

### `docs/DATA_MODEL.md`
- Every field must match `models.py` exactly — same name, same type, same default
- Don't fabricate fields that don't exist
- Don't use wrong types (e.g., `int` when code says `str`)
- If you add a field to a dataclass, add it here

### `docs/PROJECT_STATUS.md`
- Keep test file count accurate
- Update module status as things are completed
- Add new known gaps from user feedback or hackathon sessions

### `docs/QUALITY_ASSURANCE.md`
- Keep test suite table accurate (file name, type, count)
- Keep performance baselines up to date
- Don't contradict other docs (e.g., throughput numbers must match ARCHITECTURE.md)

### `docs/TECHNICAL_DEBT.md`
- Add new debt items as they're created
- Move items to RESOLVED when fixed
- Never delete resolved items — keep the history

### `docs/FINAL_REPORT.md`
- Keep pipeline steps accurate
- Keep folder structure complete
- Keep performance table consistent with other docs
- Update verified claims when new evidence is available

### `README.md`
- Keep demo instructions working (test them!)
- Keep feature list accurate
- Keep folder structure complete

---

## Verification Checklist (Before Every Push)

Run this mental checklist:
- [ ] Does every field in DATA_MODEL.md exist in models.py?
- [ ] Does every endpoint in API_CONTRACT.md exist in server.py?
- [ ] Does every pipeline step in ARCHITECTURE.md exist in pipeline.py?
- [ ] Are test counts in QUALITY_ASSURANCE.md accurate?
- [ ] Do performance numbers match across all docs?
- [ ] Is the folder structure in ARCHITECTURE.md complete?

---

## Common Mistakes to Avoid

1. **Don't document what you plan to build** — only document what exists in code
2. **Don't copy-paste between docs** without verifying — inconsistencies multiply
3. **Don't rename fields in code** without updating docs
4. **Don't add features** without documenting them
5. **Don't leave stale references** — if a file is deleted, remove mentions of it
