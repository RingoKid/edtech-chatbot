"""
Dedicated routing nodes for the master routing graph.
Handles intent classification and complexity detection to route queries appropriately.
"""
import re
from typing import Dict, Any, List, Optional
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from app.config import settings
from app.services.intent_classifier import intent_service
from app.chatbot.routing.router_state import RoutingState


async def detect_complexity(message: str, conversation_history: Optional[List[BaseMessage]] = None) -> str:
    """
    Detect query complexity using hybrid approach (rules + LLM fallback).

    Args:
        message: User's query
        conversation_history: Previous messages for context

    Returns:
        "simple" or "complex"
    """
    query_lower = message.lower()

    # ============================================================
    # FAST PATH 1: Obvious COMPLEX patterns (no LLM needed)
    # ============================================================
    obvious_complex = [
        "create lesson",
        "create a lesson",
        "generate lesson",
        "lesson plan",
        "scripted lesson",
        "step by step lesson",
        "full lesson",
        "complete lesson",
        "detailed lesson",
        "i need a lesson",
        "give me a lesson",
        "write a lesson",
        "build a lesson"
    ]

    if any(pattern in query_lower for pattern in obvious_complex):
        print(f"🎯 Rule-based: COMPLEX (lesson plan request detected)")
        return "complex"

    # ============================================================
    # FAST PATH 2: Obvious SIMPLE patterns (no LLM needed)
    # ============================================================
    obvious_simple = [
        "hi", "hello", "hey", "hey there",
        "good morning", "good afternoon", "good evening",
        "what is", "what are", "what's",
        "define", "briefly", "quickly",
        "in a few words", "simple answer"
    ]

    # Short greetings or definitional questions
    word_count = len(message.split())
    if any(pattern in query_lower for pattern in obvious_simple) and word_count < 12:
        print(f"🎯 Rule-based: SIMPLE (greeting or short question)")
        return "simple"

    # Single word queries
    if word_count <= 2:
        print(f"🎯 Rule-based: SIMPLE (very short query)")
        return "simple"

    # ============================================================
    # FAST PATH 3: Specific letter + teaching request = COMPLEX
    # ============================================================
    has_specific_letter = bool(re.search(r'\bletter\s+[A-Za-z]\b', query_lower))

    # Simplified teaching indicators - just check for the word "teach" or "teaching"
    # This catches: "teach letter f", "I wanna teach letter f", "teaching letter M", etc.
    teaching_words = ["teach", "teaching", "learn", "learning", "show", "showing"]
    has_teaching_word = any(word in query_lower for word in teaching_words)

    if has_specific_letter and has_teaching_word:
        print(f"🎯 Rule-based: COMPLEX (specific letter + teaching request)")
        return "complex"

    # Additional patterns that indicate lesson plan needs
    lesson_patterns = [
        "help me teach",
        "how do i teach",
        "how to teach",
        "activities for",
        "step by step for",
        "stroke sequence",
        "formation cues",
        "help with letter"
    ]

    if has_specific_letter and any(pattern in query_lower for pattern in lesson_patterns):
        print(f"🎯 Rule-based: COMPLEX (specific letter + detailed teaching request)")
        return "complex"

    # ============================================================
    # FAST PATH 4: Extended conversation = COMPLEX
    # ============================================================
    if conversation_history and len(conversation_history) >= 7:
        # 7+ messages = 3-4 exchanges, likely needs specialist
        print(f"🎯 Rule-based: COMPLEX (extended conversation depth)")
        return "complex"

    # ============================================================
    # AMBIGUOUS CASE: Use LLM for nuanced decision
    # ============================================================
    print(f"🤔 Ambiguous query, using LLM for intelligent classification...")

    # Build conversation context for LLM
    context_summary = ""
    if conversation_history and len(conversation_history) > 1:
        recent_msgs = conversation_history[-4:]  # Last 2 exchanges
        context_parts = []
        for msg in recent_msgs:
            if hasattr(msg, 'content'):
                content = msg.content
                if isinstance(content, str):
                    role = "Teacher" if (hasattr(msg, 'type') and msg.type == 'human') else "Assistant"
                    context_parts.append(f"{role}: {content[:120]}")

        if context_parts:
            context_summary = f"\n**Recent Conversation:**\n" + "\n".join(context_parts)

    # LLM classification prompt
    classification_prompt = f"""You are a routing classifier for an educational chatbot system.

Your job: Classify this teacher query as "simple" or "complex".

**Current Query**: "{message}"
{context_summary}

**Classification Guidelines**:

**SIMPLE** queries (general bot handles):
- Greetings: "hi", "hello", "can you help?"
- Quick questions: "what is handwriting?", "why teach phonics?"
- General tips: "tips for teaching", "strategies for..."
- Clarifications: "what do you mean?", "can you explain?"
- Short follow-ups: "okay", "yes", "that helps"

**COMPLEX** queries (needs specialist for structured lesson):
- Lesson plan requests: "create a lesson", "I need a lesson plan"
- Detailed teaching guides: "how do I teach letter M step by step?"
- Structured activities: "give me activities for teaching..."
- Full instructional sequences: "walk me through teaching..."
- Multi-part requests: requests combining multiple elements

**Context Clues**:
- If conversation history shows they're exploring a topic → might need specialist
- If query asks for "quick" or "brief" → likely simple
- If query mentions specific letters/topics with "teach" or "lesson" → likely complex

Respond with ONLY ONE WORD: "simple" or "complex"

Classification:"""

    try:
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.1,
            api_key=settings.openai_api_key.get_secret_value()
        )

        from langchain_core.messages import HumanMessage
        response = await llm.ainvoke([HumanMessage(content=classification_prompt)])
        classification = response.content.strip().lower()

        # Validate LLM response
        if classification not in ["simple", "complex"]:
            print(f"⚠️ Invalid LLM response: '{classification}', defaulting to 'simple'")
            return "simple"

        print(f"🤖 LLM classified as: {classification.upper()}")
        return classification

    except Exception as e:
        print(f"❌ LLM classification error: {str(e)}, defaulting to 'simple'")
        return "simple"


async def routing_decision_node(state: RoutingState) -> Dict[str, Any]:
    """
    Dedicated routing node that determines which bot should handle the query.

    This node:
    1. Classifies intent using intent_classifier service
    2. Detects complexity (simple/complex)
    3. Makes routing decision based on both factors

    Args:
        state: Current routing state

    Returns:
        Updated state with routing decision
    """
    try:
        # Extract query and conversation history
        messages = state.get("messages", [])
        query = state.get("original_query", "")

        if not query and messages:
            latest_message = messages[-1]
            if hasattr(latest_message, 'content'):
                content = latest_message.content
                # Handle content that might be a list of dicts (e.g., [{'type': 'text', 'text': '...'}])
                if isinstance(content, list):
                    # Extract text from list of content blocks
                    text_parts = []
                    for item in content:
                        if isinstance(item, dict) and 'text' in item:
                            text_parts.append(item['text'])
                        elif isinstance(item, str):
                            text_parts.append(item)
                    query = " ".join(text_parts) if text_parts else str(content)
                elif isinstance(content, str):
                    query = content
                else:
                    query = str(content)
            else:
                query = str(latest_message)

        # Ensure query is a string
        if not isinstance(query, str):
            query = str(query)

        query = query.strip()

        print(f"\n🔀 ROUTER NODE: Processing query: '{query[:60]}...'")

        # Step 1: Classify intent using existing service
        print(f"📊 Step 1: Classifying intent...")

        # Build conversation context string for intent classifier
        conversation_context = ""
        if len(messages) > 1:
            # Get recent messages for context
            recent = messages[-6:]  # Last 3 exchanges
            context_parts = []
            for msg in recent[:-1]:  # Exclude current message
                if hasattr(msg, 'content'):
                    content = msg.content
                    if isinstance(content, str):
                        role = "Teacher" if (hasattr(msg, 'type') and msg.type == 'human') else "Assistant"
                        context_parts.append(f"{role}: {content[:150]}")

            if context_parts:
                conversation_context = "\n".join(context_parts)

        intent_result = await intent_service.classify_intent(query, conversation_context)
        intent = intent_result.intent.value
        confidence = intent_result.confidence

        print(f"   ✅ Intent: {intent} (confidence: {confidence:.2f})")
        print(f"   💭 Reasoning: {intent_result.reasoning}")

        # Step 2: Detect complexity
        print(f"🎯 Step 2: Detecting complexity...")
        complexity = await detect_complexity(query, messages)
        print(f"   ✅ Complexity: {complexity.upper()}")

        # Step 3: Make routing decision
        print(f"🧭 Step 3: Making routing decision...")

        target_bot = None
        routing_reasoning = ""

        # Rule 1: Out of scope or simple → General bot
        if intent == "out_of_scope":
            target_bot = "general"
            routing_reasoning = "Out of scope query - general bot will explain scope boundaries"
        elif complexity == "simple":
            target_bot = "general"
            routing_reasoning = f"Simple {intent} query - general bot can handle with overview"

        # Rule 2: Complex + specific domain → Specialist
        elif complexity == "complex":
            if intent == "handwriting":
                target_bot = "handwriting"
                routing_reasoning = "Complex handwriting query requiring structured lesson plan with exact form content"
            elif intent == "vocabulary":
                target_bot = "vocabulary"
                routing_reasoning = "Complex vocabulary query requiring structured lesson plan"
            elif intent == "ideas":
                target_bot = "ideas"
                routing_reasoning = "Complex idea generation query requiring structured lesson plan"
            else:
                # Complex but general → still use general bot
                target_bot = "general"
                routing_reasoning = "Complex but general query - general bot with expanded response"

        # Fallback
        if not target_bot:
            target_bot = "general"
            routing_reasoning = "Default routing to general bot"

        print(f"   ✅ Routing to: {target_bot.upper()}")
        print(f"   💡 Reasoning: {routing_reasoning}")

        # Determine if specialist is needed
        needs_specialist = target_bot in ["handwriting", "vocabulary", "ideas"]

        return {
            "intent": intent_result.intent,
            "confidence": confidence,
            "classification_reasoning": intent_result.reasoning,
            "target_bot": target_bot,
            "routing_decision": routing_reasoning,
            "needs_specialist": needs_specialist,
            "specialist_topic": target_bot if needs_specialist else None,
            "processing_steps": [
                f"Intent classified: {intent} ({confidence:.2f})",
                f"Complexity detected: {complexity}",
                f"Routing decision: {target_bot}"
            ]
        }

    except Exception as e:
        print(f"❌ Error in routing_decision_node: {str(e)}")
        import traceback
        traceback.print_exc()

        # Fallback to general bot on error
        return {
            "target_bot": "general",
            "routing_decision": f"Routing error - defaulting to general bot: {str(e)}",
            "needs_specialist": False,
            "last_error": f"Routing failed: {str(e)}",
            "processing_steps": [f"ERROR: {str(e)}"]
        }
