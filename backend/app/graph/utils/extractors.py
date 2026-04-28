"""
Regex extraction functions for reference materials.

Extracts activity descriptions, verbal cues, phoneme gestures,
and grade-specific standards from markdown reference files.
"""

import re


LETTER_TO_SOUNDS: dict[str, list[str]] = {
    "a": ["a", "\u0101"], "b": ["b"], "c": ["k"], "d": ["d"], "e": ["e", "\u0113"],
    "f": ["f"], "g": ["g"], "h": ["h"], "i": ["i", "\u012b"], "j": ["j"],
    "k": ["k"], "l": ["l"], "m": ["m"], "n": ["n"], "o": ["o", "\u014d"],
    "p": ["p"], "q": ["qu"], "r": ["r"], "s": ["s"], "t": ["t"],
    "u": ["u", "\u016b"], "v": ["v"], "w": ["w"], "x": ["x"], "y": ["y"],
    "z": ["z"],
}


def extract_activity(framework: str, slug: str) -> str:
    """Extract full description for one activity by slug from the framework."""
    pattern = rf"^### \[{re.escape(slug)}\] .+?\n(.*?)(?=^### \[|^## |\Z)"
    match = re.search(pattern, framework, re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def extract_verbal_cues(form_f: str, letter: str) -> str:
    """Extract verbal cues for a specific letter (upper + lower) from Form F."""
    pattern = rf"^[{re.escape(letter.upper())}{re.escape(letter.lower())}]\s*\u2013\s*.+$"
    return "\n".join(re.findall(pattern, form_f, re.MULTILINE))


def extract_gesture(form_g: str, letter: str) -> str:
    """Extract gesture row(s) for target letter's sound(s) from Form G."""
    sounds = LETTER_TO_SOUNDS.get(letter.lower(), [letter.lower()])
    rows = []
    for sound in sounds:
        escaped = re.escape(sound)
        row_pattern = rf"^\|[^|]*/{escaped}/[^|]*\|.+$"
        rows.extend(re.findall(row_pattern, form_g, re.MULTILINE))
    header = re.findall(r"^\| Phoneme.*$", form_g, re.MULTILINE)[:1]
    separator = re.findall(r"^\|---.*$", form_g, re.MULTILINE)[:1]
    return "\n".join(header + separator + rows)


def extract_grade_standards(standards: str, grade_header: str) -> str:
    """Extract grade-specific standards section."""
    pattern = rf"^##\s+{re.escape(grade_header)}\b.*?\n(.*?)(?=^##\s|\Z)"
    match = re.search(pattern, standards, re.MULTILINE | re.DOTALL)
    return match.group(0).strip() if match else ""


def extract_standard(standards_text: str, code: str) -> str:
    """Extract a single standard code + description from the reference file.

    Searches the whole file — codes are unique across grades
    (CLL* for PreK, K.F.* for K, 1.F.* for 1st).

    Returns "CODE — description" or "" if not found.
    """
    escaped = re.escape(code)
    pattern = rf"^\|\s*{escaped}\s*\|([^|]+)\|"
    match = re.search(pattern, standards_text, re.MULTILINE)
    return f"{code} — {match.group(1).strip()}" if match else ""


_CF_OPENER = re.compile(r"^>\s*\*\*Corrective Feedback:\*\*")
_CF_TURN_MARKERS = ("🗣️", "👉", "💬")


def extract_corrective_feedback_blocks(lesson_markdown: str) -> list[dict]:
    """Extract every Corrective Feedback blockquote block from a lesson.

    A block is a contiguous run of lines starting with `>` whose first line
    begins `> **Corrective Feedback:**`. The block ends at the first line
    that does not start with `>`.

    Returns a list of dicts: {"raw_text": str, "turn_count": int}, where
    turn_count is the number of speaker-marker lines (🗣️/👉/💬) in the block.
    Used by the corrective_feedback_scope eval to bound the LLM judge's input.
    """
    blocks: list[dict] = []
    lines = lesson_markdown.split("\n")
    i = 0
    while i < len(lines):
        if _CF_OPENER.match(lines[i]):
            start = i
            while i < len(lines) and lines[i].startswith(">"):
                i += 1
            block_lines = lines[start:i]
            turn_count = sum(
                1 for l in block_lines if any(m in l for m in _CF_TURN_MARKERS)
            )
            blocks.append({"raw_text": "\n".join(block_lines), "turn_count": turn_count})
        else:
            i += 1
    return blocks
