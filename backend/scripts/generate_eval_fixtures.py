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

from langchain_core.callbacks import UsageMetadataCallbackHandler
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver

from app.graph.graph import create_graph
from app.graph.agents.handwriting_generator import GENERATOR_MODEL

# Per-million-token pricing (USD) — update when models or pricing change
# Source: https://openai.com/api/pricing/
COST_PER_MILLION_TOKENS = {
    "gpt-4o-mini":  {"input": 0.15, "output": 0.60},
    "gpt-4o":       {"input": 2.50, "output": 10.00},
    "gpt-5.1":      {"input": 1.25, "output": 10.00},
    "gpt-5.2":      {"input": 1.75, "output": 14.00},
    "gpt-5.2-pro":  {"input": 1.75, "output": 14.00},
    "gpt-5.4":      {"input": 2.50, "output": 15.00},
    "gpt-5.4-mini": {"input": 0.75, "output": 4.50},
    "gpt-5.4-nano": {"input": 0.20, "output": 1.25},
    "gpt-5.4-pro":  {"input": 5.00, "output": 30.00},
}


def _find_pricing(model_name: str) -> dict | None:
    """Find pricing for a model name, handling versioned names like 'gpt-5.1-2025-04-14'."""
    if model_name in COST_PER_MILLION_TOKENS:
        return COST_PER_MILLION_TOKENS[model_name]
    for key, pricing in COST_PER_MILLION_TOKENS.items():
        if model_name.startswith(key):
            return pricing
    return None


def compute_cost(usage_by_model: dict) -> float:
    """Compute total cost in USD from UsageMetadataCallbackHandler.usage_metadata dict."""
    total = 0.0
    for model_name, usage in usage_by_model.items():
        pricing = _find_pricing(model_name)
        if not pricing:
            continue
        total += (usage.get("input_tokens", 0) / 1_000_000) * pricing["input"]
        total += (usage.get("output_tokens", 0) / 1_000_000) * pricing["output"]
    return total


# Fixture param matrix — 3×3 grid (grade × level) + expert mirrors + regression targets
# Every grade × student_level cell covered, each with a unique letter.
# Fixture #1 mirrors the expert fixture (PreK/Z/on-level) for reproducibility comparison.
FIXTURE_PARAMS = [
    # Expert mirror — same params as expert_prek_letter_z_onlevel
    {"id": "prek_letter_z_onlevel", "grade": "PreK", "letter": "Z", "student_level": "on-level"},
    # PreK
    {"id": "prek_letter_a_onlevel", "grade": "PreK", "letter": "A", "student_level": "on-level"},
    {"id": "prek_letter_s_struggling", "grade": "PreK", "letter": "S", "student_level": "struggling"},
    {"id": "prek_letter_m_advanced", "grade": "PreK", "letter": "M", "student_level": "advanced"},
    {"id": "prek_letter_b_onlevel", "grade": "PreK", "letter": "B", "student_level": "on-level"},
    {"id": "prek_letter_m_struggling", "grade": "PreK", "letter": "M", "student_level": "struggling"},
    # K
    {"id": "k_letter_t_onlevel", "grade": "K", "letter": "T", "student_level": "on-level"},
    {"id": "k_letter_c_struggling", "grade": "K", "letter": "C", "student_level": "struggling"},
    {"id": "k_letter_w_advanced", "grade": "K", "letter": "W", "student_level": "advanced"},
    {"id": "k_letter_b_advanced", "grade": "K", "letter": "B", "student_level": "advanced"},
    {"id": "k_letter_b_onlevel", "grade": "K", "letter": "B", "student_level": "on-level"},
    {"id": "k_letter_b_struggling", "grade": "K", "letter": "B", "student_level": "struggling"},
    # 1st
    {"id": "first_letter_p_onlevel", "grade": "1st", "letter": "P", "student_level": "on-level"},
    {"id": "first_letter_r_struggling", "grade": "1st", "letter": "R", "student_level": "struggling"},
    {"id": "first_letter_q_advanced", "grade": "1st", "letter": "Q", "student_level": "advanced"},
    {"id": "first_letter_i_onlevel", "grade": "1st", "letter": "I", "student_level": "on-level"},
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


async def run_handwriting_generator(graph, params: dict, thread_id: str, callbacks: list | None = None) -> str | None:
    """
    Run the full flow: routing -> param extraction -> generation.

    Returns the lesson output text, or None on failure.
    """
    config = {"configurable": {"thread_id": thread_id}}
    if callbacks:
        config["callbacks"] = callbacks

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
        if callbacks:
            retry_config["callbacks"] = callbacks

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

    usage_handler = UsageMetadataCallbackHandler()
    lesson_output = await run_handwriting_generator(graph, params, thread_id, callbacks=[usage_handler])

    if lesson_output is None:
        print(f"  FAIL {fixture_id}")
        return False

    # Aggregate token usage across all LLM calls (dict keyed by model name)
    usage_by_model = usage_handler.usage_metadata
    total_input = sum(u.get("input_tokens", 0) for u in usage_by_model.values())
    total_output = sum(u.get("output_tokens", 0) for u in usage_by_model.values())
    total_tokens = total_input + total_output
    cost_usd = compute_cost(usage_by_model)

    fixture_data = {
        "fixture_id": fixture_id,
        "params": {
            "grade": params["grade"],
            "letter": params["letter"],
            "student_level": params["student_level"],
        },
        "lesson_output": lesson_output,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator_model": GENERATOR_MODEL,
        "generator_prompt_version": "handwriting-generator:production",
        "generator_git_sha": get_git_sha(),
        "usage": {
            "input_tokens": total_input,
            "output_tokens": total_output,
            "total_tokens": total_tokens,
            "cost_usd": round(cost_usd, 6),
            "by_model": {
                model: {
                    "input_tokens": u.get("input_tokens", 0),
                    "output_tokens": u.get("output_tokens", 0),
                    "total_tokens": u.get("total_tokens", 0),
                }
                for model, u in usage_by_model.items()
            },
        },
    }

    with open(fixture_path, "w") as f:
        json.dump(fixture_data, f, indent=2)

    output_len = len(lesson_output)
    print(f"  OK   {fixture_id} ({output_len:,} chars, {total_tokens:,} tokens, ${cost_usd:.4f})")
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
            print(f"  ERROR {params['id']}: {type(e).__name__}: {e}")
            cause = e.__cause__ or e.__context__
            while cause:
                print(f"    caused by {type(cause).__name__}: {cause}")
                cause = cause.__cause__ or cause.__context__
            failed += 1

    print()
    print(f"Done: {generated} generated, {skipped} skipped, {failed} failed")
    print(f"Total fixtures: {len(os.listdir(FIXTURES_DIR))} files in {FIXTURES_DIR}/")


if __name__ == "__main__":
    asyncio.run(main())
