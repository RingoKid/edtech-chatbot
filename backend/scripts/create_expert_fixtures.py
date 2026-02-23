"""
Create eval fixtures from expert-written example lesson plans.

These are human-authored ground truth lessons (not AI-generated).
Used to calibrate LLM judge evals — expert lessons should score ~100%.

Source files:
  - FORM C: PreK letter Z lesson
  - Further example lesson plans: 3 letter B lesson variations

Usage:
    docker compose exec backend python scripts/create_expert_fixtures.py
"""

import json
import os
import re
import subprocess
from datetime import datetime, timezone

PROMPT_DIR = "prompt/Handwriting & Spelling (Transcription) AI Codes"
RESOURCES_DIR = "resources/expert-feedback"
FIXTURES_DIR = "tests/fixtures/handwriting_expert"

FORM_C_PATH = os.path.join(PROMPT_DIR, "FORM C_ Example Handwriting & Spelling Lesson for Output .md")
FURTHER_PATH = os.path.join(RESOURCES_DIR, "example-lesson-plans-high-low.md")


def get_git_sha() -> str:
    sha = os.environ.get("GIT_SHA")
    if sha:
        return sha
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True
        ).strip()
    except Exception:
        return "unknown"


def split_further_lessons(text: str) -> list[str]:
    """Split the 'Further example lesson plans' file into 3 separate lessons.

    Each lesson starts with a bare 'Standards' line (the new structure includes
    Standards and Objectives sections before the scripted lesson sections).
    """
    pattern = r"(?m)(?=^Standards$)"
    parts = re.split(pattern, text)
    lessons = [p.strip() for p in parts if p.strip()]
    return lessons


def save_fixture(fixture_id: str, params: dict, lesson_output: str, git_sha: str):
    fixture_data = {
        "fixture_id": fixture_id,
        "params": params,
        "lesson_output": lesson_output,
        "source": "expert",
        "source_file": None,  # filled below
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator_model": "human-expert",
        "generator_git_sha": git_sha,
    }
    path = os.path.join(FIXTURES_DIR, f"{fixture_id}.json")
    with open(path, "w") as f:
        json.dump(fixture_data, f, indent=2, ensure_ascii=False)
    print(f"  OK   {fixture_id} ({len(lesson_output):,} chars)")
    return fixture_data


def main():
    os.makedirs(FIXTURES_DIR, exist_ok=True)
    git_sha = get_git_sha()

    print("Creating expert fixtures...")
    print(f"Output dir: {FIXTURES_DIR}/")
    print()

    # --- Fixture 1: Form C — PreK letter Z ---
    with open(FORM_C_PATH) as f:
        form_c_raw = f.read()

    # Strip the Form C header/input metadata — keep only the lesson output
    # The lesson starts at "**Handwriting & Spelling Lesson **"
    marker = "**Handwriting & Spelling Lesson **"
    idx = form_c_raw.find(marker)
    if idx == -1:
        # Try without trailing space
        marker = "**Handwriting & Spelling Lesson**"
        idx = form_c_raw.find(marker)
    form_c_lesson = form_c_raw[idx:].strip() if idx != -1 else form_c_raw.strip()

    fixture = save_fixture(
        fixture_id="expert_prek_letter_z_onlevel",
        params={"grade": "PreK", "letter": "Z", "student_level": "on-level"},
        lesson_output=form_c_lesson,
        git_sha=git_sha,
    )
    fixture["source_file"] = "FORM C_ Example Handwriting & Spelling Lesson for Output .md"

    path = os.path.join(FIXTURES_DIR, "expert_prek_letter_z_onlevel.json")
    with open(path, "w") as f:
        json.dump(fixture, f, indent=2, ensure_ascii=False)

    # --- Fixtures 2-4: Further example lesson plans (3 letter B lessons) ---
    with open(FURTHER_PATH) as f:
        further_raw = f.read()

    lessons = split_further_lessons(further_raw)
    if len(lessons) != 3:
        print(f"  WARNING: Expected 3 lessons, found {len(lessons)}")

    # Lesson 1: /b/ beginning + ending, full CVC spelling (on-level)
    # Lesson 2: /b/ beginning + ending, CVC with pre-filled vowel (more scaffolded)
    # Lesson 3: /b/ vs /p/ contrast with stretch-and-chop (struggling — most support)
    further_fixtures = [
        {
            "id": "expert_k_letter_b_onlevel",
            "params": {"grade": "K", "letter": "B", "student_level": "on-level"},
            "source_note": "Further Lesson 1: /b/ beginning+ending, full CVC spelling",
        },
        {
            "id": "expert_k_letter_b_scaffolded",
            "params": {"grade": "K", "letter": "B", "student_level": "on-level"},
            "source_note": "Further Lesson 2: /b/ beginning+ending, CVC with pre-filled vowel",
        },
        {
            "id": "expert_k_letter_b_contrast",
            "params": {"grade": "K", "letter": "B", "student_level": "struggling"},
            "source_note": "Further Lesson 3: /b/ vs /p/ contrast, stretch-and-chop",
        },
    ]

    for i, meta in enumerate(further_fixtures):
        if i >= len(lessons):
            print(f"  SKIP {meta['id']} — no lesson content found")
            continue

        fixture = save_fixture(
            fixture_id=meta["id"],
            params=meta["params"],
            lesson_output=lessons[i],
            git_sha=git_sha,
        )
        fixture["source_file"] = "example-lesson-plans-high-low.md"
        fixture["source_note"] = meta["source_note"]

        path = os.path.join(FIXTURES_DIR, f"{meta['id']}.json")
        with open(path, "w") as f:
            json.dump(fixture, f, indent=2, ensure_ascii=False)

    print()
    fixtures = [f for f in os.listdir(FIXTURES_DIR) if f.endswith(".json")]
    print(f"Done: {len(fixtures)} expert fixtures in {FIXTURES_DIR}/")


if __name__ == "__main__":
    main()
