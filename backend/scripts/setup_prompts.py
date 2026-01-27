"""
Setup script to create/update prompts in Langfuse.

Run this script once before first deployment or when prompt structure changes:
    docker compose exec backend python scripts/setup_prompts.py

This creates the agent prompts with the production label in Langfuse.
Prompts are imported from the agent modules (single source of truth).
"""

import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.langfuse.client import get_langfuse_client
from app.graph.agents.routing import DEFAULT_ROUTING_PROMPT
from app.graph.agents.param import DEFAULT_PARAM_PROMPT
from app.graph.agents.handwriting_generator import DEFAULT_HANDWRITING_GENERATOR_PROMPT


def setup_prompts():
    """Create or update prompts in Langfuse."""
    client = get_langfuse_client()

    if client is None:
        print("ERROR: Langfuse is not configured.")
        print("Set LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, and optionally LANGFUSE_HOST")
        sys.exit(1)

    print("Setting up prompts in Langfuse...")

    # Create/update the routing agent prompt
    try:
        prompt = client.create_prompt(
            name="routing-agent",
            prompt=DEFAULT_ROUTING_PROMPT,
            labels=["production"],
            type="text",
        )
        print(f"Created/updated prompt: routing-agent (version {prompt.version})")
    except Exception as e:
        print(f"Error creating routing-agent prompt: {e}")
        sys.exit(1)

    # Create/update the param agent prompt
    try:
        prompt = client.create_prompt(
            name="param-agent",
            prompt=DEFAULT_PARAM_PROMPT,
            labels=["production"],
            type="text",
        )
        print(f"Created/updated prompt: param-agent (version {prompt.version})")
    except Exception as e:
        print(f"Error creating param-agent prompt: {e}")
        sys.exit(1)

    # Create/update the handwriting generator prompt
    try:
        prompt = client.create_prompt(
            name="handwriting-generator",
            prompt=DEFAULT_HANDWRITING_GENERATOR_PROMPT,
            labels=["production"],
            type="text",
        )
        print(f"Created/updated prompt: handwriting-generator (version {prompt.version})")
    except Exception as e:
        print(f"Error creating handwriting-generator prompt: {e}")
        sys.exit(1)

    # Flush to ensure all events are sent
    client.flush()
    print("Done! Prompts are ready in Langfuse.")


if __name__ == "__main__":
    setup_prompts()
