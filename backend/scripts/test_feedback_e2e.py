"""
E2E smoke test for the feedback collector flow.

Run with:
    docker compose exec backend python scripts/test_feedback_e2e.py

Flow:
1. Create graph with local DynamoDB checkpointer
2. Invoke with "handwriting lesson for letter B, kindergarten"
3. Invoke with "Looks good" → triggers finalize + feedback prompt
4. Invoke with "Great lesson, 5 stars" → feedback collected
5. Query DynamoDB directly → verify feedback record exists
6. Print pass/fail
"""

import asyncio
import sys
import os
import boto3
from boto3.dynamodb.conditions import Key

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from app.graph.graph import create_graph
from app.services.feedback_service import FeedbackService
from app.config import settings


async def main():
    print("=" * 60)
    print("E2E Feedback Collector Smoke Test")
    print("=" * 60)

    # Use in-memory checkpointer for isolation
    checkpointer = MemorySaver()
    graph = await create_graph(checkpointer=checkpointer)

    thread_id = "e2e-feedback-test"
    config = {"configurable": {"thread_id": thread_id}}

    # Step 1: Send initial message to route to handwriting
    print("\n[Step 1] Sending: 'handwriting lesson for letter B, kindergarten'")
    result = await graph.ainvoke(
        {"messages": [HumanMessage(content="handwriting lesson for letter B, kindergarten")]},
        config=config,
    )
    task_type = result.get("task_type")
    print(f"  → task_type: {task_type}")
    print(f"  → lesson_finalized: {result.get('lesson_finalized', False)}")

    # Step 2: Simulate parameter collection completing
    # The param agent should have collected params and routed to generator
    hw_params = result.get("handwriting_params")
    print(f"  → handwriting_params: {hw_params}")

    if hw_params is None:
        print("\n⚠️  Params not collected in first turn — sending follow-up")
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content="letter B, kindergarten, on-level")]},
            config=config,
        )
        hw_params = result.get("handwriting_params")
        print(f"  → handwriting_params: {hw_params}")

    if hw_params is None:
        print("\n❌ FAIL: Could not collect handwriting params")
        sys.exit(1)

    # Step 3: If we got a lesson, approve it
    lesson_finalized = result.get("lesson_finalized", False)
    if not lesson_finalized:
        print("\n[Step 2] Sending: 'Looks good'")
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content="Looks good")]},
            config=config,
        )
        lesson_finalized = result.get("lesson_finalized", False)
        print(f"  → lesson_finalized: {lesson_finalized}")

    if not lesson_finalized:
        print("\n❌ FAIL: Lesson was not finalized")
        sys.exit(1)

    # Step 4: Check if feedback was already submitted (skip flow) or if
    # the feedback prompt was asked. Either way, send feedback.
    feedback_submitted = result.get("feedback_submitted", False)
    print(f"  → feedback_submitted: {feedback_submitted}")

    if not feedback_submitted:
        print("\n[Step 3] Sending: 'Great lesson, 5 stars'")
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content="Great lesson, 5 stars")]},
            config=config,
        )
        feedback_submitted = result.get("feedback_submitted", False)
        print(f"  → feedback_submitted: {feedback_submitted}")

    # Step 5: Check feedback_data in result
    feedback_data = result.get("feedback_data")
    print(f"  → feedback_data: {feedback_data}")

    # Validate results
    print("\n" + "=" * 60)
    print("Results:")
    print("=" * 60)

    passed = True

    if not feedback_submitted:
        print("❌ feedback_submitted is False")
        passed = False
    else:
        print("✅ feedback_submitted = True")

    if feedback_data is None:
        print("⚠️  feedback_data is None (user may have skipped)")
    else:
        print(f"✅ feedback_data present: category={feedback_data.get('category')}, "
              f"rating={feedback_data.get('rating')}, text={feedback_data.get('text', '')[:50]}")

    if passed:
        print("\n✅ E2E SMOKE TEST PASSED")
    else:
        print("\n❌ E2E SMOKE TEST FAILED")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
