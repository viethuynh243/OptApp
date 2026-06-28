# Plan 003: Sync README with the shipped v1.3.0 (version, features, structure)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 0ec2135..HEAD -- README.md core/version.py CHANGELOG.md`
> If any of those changed since this plan was written, compare the "Current
> state" excerpts against the live code before proceeding; on a mismatch,
> treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none (touches README only; coordinate with Plan 001 which also
  edits the README "Cài đặt" section — see Scope)
- **Category**: docs
- **Planned at**: commit `0ec2135`, 2026-06-20

## Why this matters

The README advertises **v1.1.0** while the code, `CHANGELOG.md`, and the window
title are all **v1.3.0**. Worse, the README's feature and structure sections
describe the pre-v1.3.0 app: they say constraints are "R3–R6" (v1.3.0 added
**R7 lateral force** and **R8 P–M interaction**), and the "Cấu trúc chính"
module list omits the entire `core/ext/` package (diameter sweep, cap-resize,
R7/R8 orchestration) plus `io_handlers/report_writer.py` and
`io_handlers/mcoc_writer_ext.py`. A new user reading the README cannot discover
the headline features of the version they're running. Stale docs that are
actively wrong are worse than missing ones.

## Current state

`core/version.py:7-9`:

```python
__version__ = "1.3.0"
RELEASE_DATE = "2026-06-18"
```

`CHANGELOG.md` top entry: `## [1.3.0] — 2026-06-18`.

`README.md:3` (stale version):

```
**Phiên bản: v1.1.0** (2026-06-16) · xem [CHANGELOG.md](CHANGELOG.md). Nguồn version: `core/version.py`.
```

`README.md:118-119` (stale constraint range — only R3–R6):

```
3. Mỗi phương án được **chấm bằng MCOC chính xác** (gọi `MCOC_Batch.exe`); ràng buộc R3–R6 và Pmax/Pmin/M đều từ MCOC.
```

`README.md:95-112` ("Cấu trúc chính của dự án") lists `core/*` and three
`io_handlers/*` modules but **omits**: the `core/ext/` package
(`pile_section.py`, `config_ext.py`, `blackbox_ext.py`, `nsga2_ext.py`,
`cap_resize.py`, `orchestrator.py`), `core/cap_suggest.py`,
`io_handlers/report_writer.py`, and `io_handlers/mcoc_writer_ext.py`.

Ground-truth feature descriptions to mirror (from `CHANGELOG.md` §[1.3.0]):
- Quét nhiều đường kính cọc (patch tiết diện thật vào file MCOC, chấm từng `d`).
- Chọn đường kính thắng theo hàm chi phí vật liệu (số cọc × diện tích tiết diện).
- Tự thu bệ (cap_resize) theo TCVN 10304:2014.
- Ràng buộc mở rộng **R7** (lực ngang `Hmax ≤ [H]`) và **R8** (tương tác P–M
  `N/[Po] + M/[M] ≤ 1.0`), bật ở luồng mở rộng.

The ADR vault confirms these are deliberate: `docs/vault/3-Quyết định (ADR)/`
contains ADR-005 (bật R7/R8 trong ext), ADR-006 (đường kính là biến tối ưu),
ADR-007 (đổi kích thước bệ theo TCVN). Match that vocabulary.

## Commands you will need

| Purpose         | Command                                  | Expected on success |
|-----------------|------------------------------------------|---------------------|
| Check version   | `grep -n "1.3.0" README.md`              | matches line 3      |
| Check no v1.1.0 | `grep -n "v1.1.0" README.md`             | no matches          |
| Check R7/R8     | `grep -n "R7\|R8\|R1–R8\|R1-R8" README.md` | at least one match |
| Check ext listed| `grep -n "core/ext" README.md`           | at least one match  |

## Scope

**In scope** (the only file you should modify):
- `README.md` — the version line (3), the constraint reference (118–119), the
  "Tính năng chính" section (~9–23), and the "Cấu trúc chính của dự án" list
  (~95–112).

**Out of scope** (do NOT touch):
- `README.md` "Cài đặt" section (lines ~24–33) — that is owned by **Plan 001**.
  If Plan 001 has already landed, leave its install text as-is. If both plans
  run, do this one's edits around that section without reverting it.
- `CHANGELOG.md`, `core/version.py` — they are already correct; do not "sync"
  them backward.
- Any source `.py` file or the `docs/` tree.

## Git workflow

- Branch: `advisor/003-readme-sync`
- One commit, message e.g. `Cập nhật README theo v1.3.0 (R1–R8, gói ext, phiên bản)`.
- Do NOT push or open a PR unless instructed.

## Steps

### Step 1: Fix the version line

Edit `README.md:3` to read v1.3.0 and the matching date:

```
**Phiên bản: v1.3.0** (2026-06-18) · xem [CHANGELOG.md](CHANGELOG.md). Nguồn version: `core/version.py`.
```

**Verify**: `grep -n "v1.3.0" README.md` matches line 3 AND `grep -n "v1.1.0" README.md` returns nothing.

### Step 2: Add the v1.3.0 features to "Tính năng chính"

In the "## Tính năng chính" bullet list (~lines 9–23), add a short subsection or
bullets for the extended-optimization features, using the CHANGELOG vocabulary
from "Current state". Keep it concise (3–5 bullets), e.g.:

- **Tối ưu mở rộng (gói `core/ext/`)**: quét nhiều **đường kính cọc** (patch
  tiết diện thật vào file MCOC, chấm chính xác từng `d`), chọn đường kính thắng
  theo **chi phí vật liệu**, và **tự thu bệ** theo TCVN 10304:2014.
- **Ràng buộc R1–R8**: ngoài R3–R6, luồng mở rộng bật **R7** (lực ngang
  `Hmax ≤ [H]`) và **R8** (tương tác P–M `N/[Po] + M/[M] ≤ 1.0`).

**Verify**: `grep -n "đường kính\|R7\|R8" README.md` returns matches in the features area.

### Step 3: Fix the constraint range in the methodology summary

Update `README.md:118-119` so it no longer claims only R3–R6. Change "ràng buộc
R3–R6" to reflect that the extended flow covers R1–R8 (R7/R8 optional). Keep the
sentence otherwise intact.

**Verify**: `grep -n "R3–R6" README.md` — if any remain, confirm each remaining
mention is contextually correct (e.g. describing the base flow), otherwise update it.

### Step 4: Complete the "Cấu trúc chính của dự án" module list

Add the missing modules to the list (~lines 95–112), each with a one-line role:

- `core/ext/` — gói tối ưu mở rộng: `pile_section.py` (bảng/đặc trưng đường
  kính), `config_ext.py` (cấu hình R7/R8 + thu bệ), `blackbox_ext.py`
  (đánh giá có R7/R8), `nsga2_ext.py` (NSGA-II mở rộng), `cap_resize.py` (thu
  bệ theo TCVN), `orchestrator.py` (điều phối end-to-end).
- `core/cap_suggest.py` — đề xuất nới bệ tối thiểu khi bệ chật.
- `io_handlers/report_writer.py` — sinh báo cáo kỹ thuật MD/PDF.
- `io_handlers/mcoc_writer_ext.py` — patch tiết diện theo đường kính vào template MCOC.

**Verify**: `grep -n "core/ext\|report_writer\|mcoc_writer_ext\|cap_suggest" README.md` returns matches.

## Test plan

This is a docs-only change; there is no code test. Verification is the grep
checks in Done criteria. Optionally render the README in a Markdown viewer to
confirm the new bullets/list are well-formed (no broken nesting).

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `grep -n "v1.1.0" README.md` returns no matches
- [ ] `grep -n "v1.3.0" README.md` returns a match on the version line
- [ ] `grep -n "R7" README.md` and `grep -n "R8" README.md` each return a match
- [ ] `grep -n "core/ext" README.md` returns a match
- [ ] `grep -n "report_writer\|mcoc_writer_ext\|cap_suggest" README.md` returns matches
- [ ] `git status` shows only `README.md` modified
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- `core/version.py` no longer says `1.3.0` (a new release happened since this
  plan was written — use the actual current version instead and report it).
- The README sections don't match the "Current state" excerpts (README drifted;
  re-read before editing).
- Plan 001 has rewritten the "Cài đặt" section and your edits would conflict —
  keep Plan 001's install text and only edit the version/features/structure
  sections.

## Maintenance notes

- `core/version.py` is the single source of truth for the version; whoever cuts
  the next release should bump it and re-check that `README.md:3` and
  `CHANGELOG.md` agree.
- A reviewer should sanity-check the feature bullets against the current
  `CHANGELOG.md` top entry, not against this plan (the CHANGELOG is canonical).
