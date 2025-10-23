"""Default prompts used by the agent."""

# Greeting and welcome prompts
GREETING_WELCOME_MESSAGE = "Welcome! I'm here to help you build lesson plans. \n\nWhat would you like to work on?\n- Handwriting\n- Vocabulary\n- Idea Generation"

# Main router prompts
MAIN_ROUTER_SYSTEM_PROMPT = "You are a routing assistant. The user must choose one of: Handwriting, Vocabulary, or Idea Generation. Classify their response into exactly one of these three options based on their intent."

MAIN_ROUTER_ERROR_MESSAGE = "I'm sorry, I didn't understand that choice. Can you please pick from Handwriting, Vocabulary, or Idea Generation?"

# Stub feature prompts
HANDWRITING_STUB_MESSAGE = "*Handwriting feature coming soon!*"
VOCABULARY_STUB_MESSAGE = "*Vocabulary feature coming soon!*"
IDEA_GENERATION_STUB_MESSAGE = "*Idea Generation feature coming soon!*"
