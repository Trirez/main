# Codebase Issue Triage: Proposed Tasks

## 1) Typo fix task
**Title:** Fix malformed local URL in README getting-started instructions.

- **Issue:** The README includes a broken URL example split across lines with a stray closing parenthesis, which reads as `http://127.0.0.1:5000` followed by `)` on the next line.
- **Why it matters:** This is a copy/paste friction point for first-time users and looks like a typo/formatting error in core setup docs.
- **Where:** `README.md`.
- **Proposed task:** Replace the broken URL example with a single correctly formatted URL line.
- **Acceptance criteria:**
  - URL appears as `http://127.0.0.1:5000` in one line.
  - No stray `)` remains in that sentence.

## 2) Bug fix task
**Title:** Fix drag-and-drop puzzle piece detection when dragging nested `<img>` elements.

- **Issue:** `handleDragStart` reads `e.target.dataset.id`, but drag events can originate from the nested `<img>` inside `.draggable-piece`, where `dataset.id` is missing. This can set `draggedPieceId` to `NaN` and break drop behavior.
- **Why it matters:** Intermittently broken drag interactions are a user-facing functional defect.
- **Where:** `static/js/app.js` in `handleDragStart`.
- **Proposed task:** Resolve the draggable piece id from the closest `.draggable-piece` ancestor (or use `e.currentTarget`) and guard against missing ids.
- **Acceptance criteria:**
  - Dragging works whether the user grabs the card container or the inner image.
  - `draggedPieceId` is always a valid integer for draggable pieces.

## 3) Comment/documentation discrepancy task
**Title:** Align `ImageCaptcha` module docs with actual 3x3 behavior.

- **Issue:** The module docstring says image captcha "Displays 3 images", but generation logic creates 9 images (3x3 grid) with 3 correct choices.
- **Why it matters:** Mismatched docs slow down maintenance and can mislead contributors.
- **Where:** `captcha_generators/image_captcha.py` module docstring vs `generate()` implementation.
- **Proposed task:** Update the docstring/comment text to describe 9 images in a 3x3 grid and 3 required selections.
- **Acceptance criteria:**
  - Module-level description matches runtime behavior.
  - No conflicting “3 images” phrasing remains.

## 4) Test improvement task
**Title:** Replace print-based smoke script with assertion-based automated tests.

- **Issue:** `test_captchas.py` is currently a script that prints values and “ALL TESTS PASSED!” regardless of strict assertions.
- **Why it matters:** CI cannot reliably detect regressions without assertions and a standard test runner.
- **Where:** `test_captchas.py`.
- **Proposed task:** Convert to `pytest` tests with deterministic assertions for response shape, lengths, and key invariants for each captcha generator.
- **Acceptance criteria:**
  - Tests fail on invalid output (missing keys, wrong lengths/types).
  - Tests run under `pytest` with non-zero exit code on failures.
  - At least one regression test added for drag puzzle position verification inputs.
