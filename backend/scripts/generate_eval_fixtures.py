"""
Generate eval fixtures by running the handwriting generator for various param combos.

Saves lesson outputs as JSON to tests/fixtures/handwriting_generator/.
These fixtures are used by the LLM judge eval scripts (no live graph needed at eval time).

Usage:
    # Generate all fixtures (skip existing)
    docker compose exec backend python scripts/generate_eval_fixtures.py

    # Force regenerate all
    docker compose exec backend python scripts/generate_eval_fixtures.py --force
"""

import asyncio
import argparse
import json
import os
import subprocess
import uuid
from datetime import datetime, timezone

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver

from app.graph.graph import create_graph


# Fixture param matrix — 10 combos: 3×3 grid (grade × level) + expert mirror
# Every grade × student_level cell covered, each with a unique letter.
# Fixture #1 mirrors the expert fixture (PreK/Z/on-level) for reproducibility comparison.
FIXTURE_PARAMS = [
    # Expert mirror — same params as expert_prek_letter_z_onlevel
    {"id": "prek_letter_z_onlevel", "grade": "PreK", "letter": "Z", "student_level": "on-level"},
    # PreK
    {"id": "prek_letter_a_onlevel", "grade": "PreK", "letter": "A", "student_level": "on-level"},
    {"id": "prek_letter_s_struggling", "grade": "PreK", "letter": "S", "student_level": "struggling"},
    {"id": "prek_letter_m_advanced", "grade": "PreK", "letter": "M", "student_level": "advanced"},
    # K
    {"id": "k_letter_t_onlevel", "grade": "K", "letter": "T", "student_level": "on-level"},
    {"id": "k_letter_c_struggling", "grade": "K", "letter": "C", "student_level": "struggling"},
    {"id": "k_letter_w_advanced", "grade": "K", "letter": "W", "student_level": "advanced"},
    # 1st
    {"id": "first_letter_p_onlevel", "grade": "1st", "letter": "P", "student_level": "on-level"},
    {"id": "first_letter_r_struggling", "grade": "1st", "letter": "R", "student_level": "struggling"},
    {"id": "first_letter_q_advanced", "grade": "1st", "letter": "Q", "student_level": "advanced"},
]

FIXTURES_DIR = "tests/fixtures/handwriting_generator"


def get_git_sha() -> str:
    """Get current git commit SHA (short). Checks GIT_SHA env var first (for Docker), falls back to git command."""
    sha = os.environ.get("GIT_SHA")
    if sha:
        return sha
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True
        ).strip()
    except Exception:
        return "unknown"


async def run_handwriting_generator(graph, params: dict, thread_id: str) -> str | None:
    """
    Run the full flow: routing -> param extraction -> generation.

    Returns the lesson output text, or None on failure.
    """
    config = {"configurable": {"thread_id": thread_id}}

    # Step 1: Route to handwriting task
    routing_messages = [
        "I want to create a handwriting lesson",
        "Please create a handwriting lesson for my class",
        "handwriting lesson please",
    ]

    routing_result = None
    for attempt, routing_msg in enumerate(routing_messages):
        retry_thread = f"{thread_id}-retry{attempt}" if attempt > 0 else thread_id
        retry_config = {**config, "configurable": {"thread_id": retry_thread}}

        routing_result = await graph.ainvoke(
            {"messages": [HumanMessage(content=routing_msg)]},
            retry_config,
        )

        task_type = routing_result.get("task_type")
        if task_type == "handwriting":
            config = retry_config
            break

    task_type = routing_result.get("task_type") if routing_result else None
    if task_type != "handwriting":
        print(f"    Routing failed: got task_type={task_type}")
        return None

    # Step 2: Provide params to param agent
    grade = params["grade"]
    letter = params["letter"]
    student_level = params["student_level"]

    param_input = f"{grade} letter {letter}"
    if student_level != "on-level":
        param_input += f" for {student_level} students"

    param_result = await graph.ainvoke(
        {"messages": [HumanMessage(content=param_input)]},
        config=config,
    )

    if param_result.get("handwriting_params") is None:
        print(f"    Param extraction failed")
        return None

    # Extract lesson output from messages (last non-tool AI message)
    messages = param_result.get("messages", [])
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content:
            if not (hasattr(msg, "tool_calls") and msg.tool_calls):
                return msg.content

    print(f"    No lesson output found in messages")
    return None


async def generate_fixture(params: dict, force: bool = False) -> bool:
    """Generate a single fixture. Returns True if generated, False if skipped/failed."""
    fixture_id = params["id"]
    fixture_path = os.path.join(FIXTURES_DIR, f"{fixture_id}.json")

    if os.path.exists(fixture_path) and not force:
        print(f"  SKIP {fixture_id} (exists, use --force to regenerate)")
        return False

    print(f"  Generating {fixture_id}...")
    print(f"    Params: grade={params['grade']}, letter={params['letter']}, level={params['student_level']}")

    graph = await create_graph(checkpointer=MemorySaver())
    thread_id = f"fixture-{fixture_id}-{uuid.uuid4().hex[:8]}"

    lesson_output = await run_handwriting_generator(graph, params, thread_id)

    if lesson_output is None:
        print(f"  FAIL {fixture_id}")
        return False

    fixture_data = {
        "fixture_id": fixture_id,
        "params": {
            "grade": params["grade"],
            "letter": params["letter"],
            "student_level": params["student_level"],
        },
        "lesson_output": lesson_output,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator_model": "gpt-4o",
        "generator_prompt_version": "handwriting-generator:production",
        "generator_git_sha": get_git_sha(),
    }

    with open(fixture_path, "w") as f:
        json.dump(fixture_data, f, indent=2)

    output_len = len(lesson_output)
    print(f"  OK   {fixture_id} ({output_len:,} chars)")
    return True


async def main():
    parser = argparse.ArgumentParser(description="Generate eval fixtures for handwriting generator")
    parser.add_argument("--force", action="store_true", help="Force regenerate all fixtures")
    parser.add_argument("--fixture", type=str, help="Generate only a specific fixture by ID")
    args = parser.parse_args()

    os.makedirs(FIXTURES_DIR, exist_ok=True)

    params_to_generate = FIXTURE_PARAMS
    if args.fixture:
        params_to_generate = [p for p in FIXTURE_PARAMS if p["id"] == args.fixture]
        if not params_to_generate:
            print(f"Unknown fixture ID: {args.fixture}")
            print(f"Available: {[p['id'] for p in FIXTURE_PARAMS]}")
            return

    print(f"Generating {len(params_to_generate)} fixture(s)...")
    print(f"Output dir: {FIXTURES_DIR}/")
    print()

    generated = 0
    failed = 0
    skipped = 0

    for params in params_to_generate:
        try:
            result = await generate_fixture(params, force=args.force)
            if result:
                generated += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"  ERROR {params['id']}: {e}")
            failed += 1

    print()
    print(f"Done: {generated} generated, {skipped} skipped, {failed} failed")
    print(f"Total fixtures: {len(os.listdir(FIXTURES_DIR))} files in {FIXTURES_DIR}/")


if __name__ == "__main__":
    asyncio.run(main())
