# ANSWERS.md

## How to run
```bash
python log_analyzer.py <logfile>
```
No external dependencies. Requires Python 3.8+.

## Stack choice: Why Python?

Python is ideal for rapid text parsing and reporting. Built‑in modules `re`, `json`, `datetime`, and `collections` handle everything without extra packages. The task’s core is heuristics and string manipulation, where Python’s simplicity lets you focus on edge cases rather than boilerplate.

A worse choice would be **C++** – verbose file I/O, manual memory management, and no built‑in regex would slow iteration. **Java** would add class overhead and a more complex build process, making it less agile for a one‑day exercise.

## One real edge case: Missing status code with response time directly after path

**File:** `log_analyzer.py`  
**Lines:** The block after `idx = 4` in `parse_line()` (approximately lines 75‑85).

The parser checks if the token after the path is a valid status code (digits or `-`). If it isn’t (e.g., raw response time `89ms`), the parser assumes the status code is missing and treats that token as the response time instead.

Without this handling, `"89ms"` would be forced into an integer status field, causing either a `ValueError` crash or silently corrupted statistics (e.g., counting 89 as a status code). This ensures we gracefully handle the variant: 2024/03/15 14:23:01 10.0.0.7 POST /api/login 89ms

## AI usage

- **ChatGPT (GPT‑4):** Asked “Give a regex to match ISO timestamps, slash timestamps, Apache timestamps, and epoch seconds.”  
  Output used as the `TIMESTAMP_PATTERNS` list. I added the epoch validation logic myself.  

- **GitHub Copilot (PyCharm):** Used for autocompleting `parse_response_time`. It generated a basic version handling only `ms`. I extended it to handle `s` and raw numbers.  

- **ChatGPT:** Asked “How to structure a CLI that prints summary report from logs?”  
  Received an outline. I adapted it to my data structure and added malformed line counting.  

**Change to AI output:**  
Copilot suggested `if parts[4].isdigit(): status = int(parts[4])` for status code extraction. I changed it to also accept `"-"` as a missing status placeholder and added the fallback that treats the token as response time when it’s not a status. This prevented a mis‑shift that would otherwise occur in lines without a status field.

---

## Honest gap

The response time parser assumes raw numbers under 10,000 are milliseconds; larger numbers are treated as seconds. This could misclassify an extremely slow request logged as `15000` (15 seconds in ms) if the unit is missing.  

With another day, I’d add a configurable threshold or a heuristic based on typical request ranges. Additionally, the report output is plain text; a JSON or HTML dashboard option would make it more useful for on‑call situations.



