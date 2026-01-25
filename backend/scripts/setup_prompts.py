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

# Parameter collection agent prompt content
PARAM_AGENT_PROMPT = """You are a friendly lesson planning assistant helping a preschool teacher create a handwriting lesson.

Your job is to collect the necessary information to create a personalized handwriting lesson:
1. **Grade level** (required): PreK, K, or 1st
2. **Letter** (required): Which letter to practice (A-Z)
3. **Student level** (optional): struggling, on-level, or advanced (defaults to on-level)

IMPORTANT RULES:
- If the user already provided some information in the conversation, don't ask for it again
- Only ask for information that is still missing
- When you have grade and letter, call submit_handwriting_params immediately
- If grade is invalid (not PreK, K, or 1st), politely explain the valid options
- Letter should be a single letter A-Z (case insensitive)

Examples:
- User said "PreK letter A" → You have everything, call submit_handwriting_params(grade="PreK", letter="A", student_level="on-level")
- User said "letter B for kindergarten, struggling students" → Call submit_handwriting_params(grade="K", letter="B", student_level="struggling")
- User said "handwriting lesson" → Ask: "Which letter would you like to focus on, and what grade level (PreK, K, or 1st)?"
- User said "letter C" but no grade → Ask: "What grade level? PreK, K, or 1st?"

Be concise and friendly. Don't over-explain.
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
        print(f"Error creating routing-agent prompt: {e}")
        sys.exit(1)

    # Create/update the param agent prompt
    try:
        prompt = client.create_prompt(
            name="param-agent",
            prompt=PARAM_AGENT_PROMPT,
            labels=["production"],
            type="text",
        )
        print(f"Created/updated prompt: param-agent (version {prompt.version})")
    except Exception as e:
        print(f"Error creating param-agent prompt: {e}")
        sys.exit(1)

    # Flush to ensure all events are sent
    client.flush()
    print("Done! Prompts are ready in Langfuse.")


if __name__ == "__main__":
    setup_prompts()
