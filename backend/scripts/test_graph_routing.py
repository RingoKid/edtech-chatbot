"""
Test script: trace graph routing to debug why image nodes are skipped.

This script:
1. Creates a graph with in-memory checkpointer
2. Simulates a handwriting lesson conversation
3. Traces each node execution and routing decision
4. Reports whether image_assembly and image_director ever execute

Usage:
    docker compose exec backend python scripts/test_graph_routing.py
"""

import asyncio
import sys
import time
from unittest.mock import patch, MagicMock

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver

# Patch the image_director_node to avoid real API calls
async def mock_image_director_node(state, config):
    print("  📸 [image_director_node] EXECUTED!")
    return {"image_requests": [{"prompt": "test", "placement": "test", "alt_text": "test"}]}

def mock_image_assembly_node(state, config):
    print("  🔧 [image_assembly_node] EXECUTED!")
    thread_id = config.get("configurable", {}).get("thread_id", "unknown")
    return {"image_urls": [f"https://example.com/images/{thread_id}/img_{n}.jpg" for n in range(1, 4)]}


async def main():
    print("🔍 Graph Routing Trace Test")
    print(f"   Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Import graph factory
    from app.graph.graph import create_graph, entry_router, route_after_handwriting_generator

    # Create graph with in-memory checkpointer
    checkpointer = MemorySaver()

    # Patch image nodes to avoid real API calls
    with patch("app.graph.graph.image_assembly_node", mock_image_assembly_node), \
         patch("app.graph.graph.image_director_node", mock_image_director_node):
        graph = await create_graph(checkpointer=checkpointer)

    thread_id = f"routing-test-{int(time.time())}"
    config = {"configurable": {"thread_id": thread_id}}

    # ─── Step 1: User requests a handwriting lesson ───
    print("=" * 60)
    print("STEP 1: User requests handwriting lesson")
    print("=" * 60)

    result = await graph.ainvoke(
        {"messages": [HumanMessage(content="I need a handwriting lesson for the letter D, kindergarten level, on-level student")]},
        config=config,
    )

    # Check state
    state = await graph.aget_state(config)
    vals = state.values
    print(f"\n  State after Step 1:")
    print(f"    task_type:        {vals.get('task_type')}")
    print(f"    routing_complete: {vals.get('routing_complete')}")
    print(f"    hw_params:        {vals.get('handwriting_params')}")
    print(f"    lesson_finalized: {vals.get('lesson_finalized')}")
    print(f"    image_urls:       {vals.get('image_urls')}")
    print(f"    image_requests:   {vals.get('image_requests')}")

    # Check last message
    messages = vals.get("messages", [])
    if messages:
        last = messages[-1]
        content_preview = last.content[:200] if last.content else "(empty)"
        print(f"    last_msg type:    {type(last).__name__}")
        print(f"    last_msg:         {content_preview}...")

    hw_params = vals.get("handwriting_params")
    if hw_params is None:
        print("\n  ⚠️  handwriting_params not set after Step 1.")
        print("  The routing agent may not have routed to param_agent.")
        print("  Check if the agent understood the user request.")
        # Still continue — the user might need to send another message

    # ─── Step 2: User approves the lesson ───
    print("\n" + "=" * 60)
    print("STEP 2: User approves the lesson (triggers finalize)")
    print("=" * 60)

    # If params not set yet, we need to continue the conversation
    if hw_params is None:
        print("  Sending additional context...")
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content="Yes, that sounds good. Kindergarten, letter D, on-level.")]},
            config=config,
        )

        state = await graph.aget_state(config)
        vals = state.values
        hw_params = vals.get("handwriting_params")
        lesson_finalized = vals.get("lesson_finalized")
        print(f"\n  State after additional message:")
        print(f"    hw_params:        {hw_params}")
        print(f"    lesson_finalized: {lesson_finalized}")

        if hw_params is None:
            print("\n  ❌ Still no handwriting_params — the agent couldn't route.")
            print("  This is a routing issue, not an image pipeline issue.")
            sys.exit(1)

        # If lesson was already generated but not finalized, approve it
        if not lesson_finalized:
            print("\n  Sending approval message...")
            result = await graph.ainvoke(
                {"messages": [HumanMessage(content="This looks great! I'm satisfied with the lesson.")]},
                config=config,
            )
    else:
        # Params already set from step 1 — check if lesson was generated
        lesson_finalized = vals.get("lesson_finalized")
        if lesson_finalized:
            print("  Lesson already finalized in Step 1!")
        else:
            # Need to wait for lesson then approve
            # The lesson was likely generated in Step 1 already
            print("  Sending approval message...")
            result = await graph.ainvoke(
                {"messages": [HumanMessage(content="This looks great! I'm satisfied with the lesson.")]},
                config=config,
            )

    # ─── Check final state ───
    print("\n" + "=" * 60)
    print("FINAL STATE CHECK")
    print("=" * 60)

    state = await graph.aget_state(config)
    vals = state.values
    print(f"  task_type:        {vals.get('task_type')}")
    print(f"  hw_params:        {'SET' if vals.get('handwriting_params') else 'None'}")
    print(f"  lesson_finalized: {vals.get('lesson_finalized')}")
    print(f"  image_urls:       {vals.get('image_urls')}")
    print(f"  image_requests:   {vals.get('image_requests')}")
    print(f"  feedback_submitted: {vals.get('feedback_submitted')}")

    # Check entry_router decision
    entry_decision = entry_router(vals)
    print(f"\n  entry_router would route to: {entry_decision}")

    # Check route_after_handwriting_generator
    route_decision = route_after_handwriting_generator(vals)
    print(f"  route_after_hw_gen would route to: {route_decision}")

    # Verdict
    print("\n" + "=" * 60)
    if vals.get("image_urls"):
        print("✅ Image pipeline EXECUTED — image_urls present in state")
    elif vals.get("lesson_finalized"):
        print("⚠️  Lesson finalized but image_urls NOT in state")
        print("   The image_assembly node may not have executed")
    else:
        print("⚠️  Lesson NOT finalized — image pipeline never triggered")
        print("   The generator may not have called finalize_lesson")

    # Count messages
    msg_count = len(vals.get("messages", []))
    print(f"\n  Total messages: {msg_count}")


if __name__ == "__main__":
    asyncio.run(main())
