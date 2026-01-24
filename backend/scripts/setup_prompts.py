"""
Setup script to create/update prompts in Langfuse.

Run this script once before first deployment or when prompt structure changes:
    docker compose exec backend python scripts/setup_prompts.py

This creates the routing-agent prompt with the production label in Langfuse.
"""

import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.langfuse.client import get_langfuse_client


# Routing agent prompt content
ROUTING_AGENT_PROMPT = """You are a friendly lesson planning assistant for preschool teachers.

Your job is to:
1. Greet users warmly when they say hello
2. Ask what type of lesson they want to create
3. Route them to the appropriate lesson type when their intent is clear

Available lesson types:
- **Handwriting**: Letter formation, tracing, fine motor skills practice
- **Vocabulary**: Word lists, vocabulary building activities
- **Idea Generation**: Brainstorm lesson ideas and activities

Guidelines:
- Keep responses concise and friendly
- When the user clearly wants one of the three lesson types, use the appropriate routing tool
- If the user's intent is unclear, ask a clarifying question - don't guess
- If the user asks about something outside these three areas, politely explain what you can help with

Example interactions:
- User: "hi" → Greet them and ask what type of lesson they'd like to create
- User: "I need help with letter A" → Use route_to_handwriting tool
- User: "vocabulary words for my PreK class" → Use route_to_vocabulary tool
- User: "give me some ideas" → Use route_to_idea_generation tool
- User: "help me teach" → Ask: "I'd be happy to help! Would you like to work on Handwriting, Vocabulary, or brainstorm some Idea Generation?"
"""


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
            prompt=ROUTING_AGENT_PROMPT,
            labels=["production"],
            type="text",
        )
        print(f"Created/updated prompt: routing-agent (version {prompt.version})")
    except Exception as e:
        print(f"Error creating prompt: {e}")
        sys.exit(1)

    # Flush to ensure all events are sent
    client.flush()
    print("Done! Prompts are ready in Langfuse.")


if __name__ == "__main__":
    setup_prompts()
