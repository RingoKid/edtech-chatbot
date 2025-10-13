"""
Studio-friendly Routing Graph that shows the complete intent → specialist flow.
This version removes complex dependencies to ensure it loads in LangGraph Studio.
"""
from typing import Dict, Any
from langgraph.graph import StateGraph, END, START
from langchain_core.messages import HumanMessage, AIMessage
from app.graph.routing_state import RoutingState

# Mock intent classification for studio visualization
async def classify_intent_node(state: RoutingState) -> Dict[str, Any]:
    """
    Intent Classification Node - Analyzes teacher query and assigns confidence.
    In production, this uses OpenAI GPT-4 for classification.
    """
    messages = state.get("messages", [])
    if not messages:
        return {"intent": "general", "confidence": 0.5}
    
    # Handle different message formats
    latest_message = messages[-1]
    if hasattr(latest_message, 'content'):
        query = latest_message.content
    elif isinstance(latest_message, dict) and 'content' in latest_message:
        query = latest_message['content']
    elif isinstance(latest_message, list):
        # Handle LangGraph Studio format: [{'type': 'text', 'text': 'content'}]
        if len(latest_message) > 0 and isinstance(latest_message[0], dict):
            if 'text' in latest_message[0]:
                query = latest_message[0]['text'].strip()
            elif 'content' in latest_message[0]:
                query = latest_message[0]['content'].strip()
            else:
                query = str(latest_message[0])
        else:
            query = " ".join(str(item) for item in latest_message)
    else:
        query = str(latest_message)
    
    # Ensure query is a string and clean it
    if not isinstance(query, str):
        query = str(query)
    query = query.strip()
    
    # Demo classification logic (in production, this uses OpenAI)
    query_lower = query.lower()

    # Check for domain-specific keywords FIRST (before greetings)
    if any(word in query_lower for word in ["letter", "handwriting", "write", "pencil", "grip", "formation", "stroke"]):
        intent = "handwriting"
        confidence = 0.9
        reasoning = "Strong handwriting keywords detected"
    elif any(word in query_lower for word in ["word", "vocabulary", "spelling", "reading", "phonics", "sight"]):
        intent = "vocabulary"
        confidence = 0.85
        reasoning = "Strong vocabulary/reading keywords detected"
    elif any(word in query_lower for word in ["story", "creative", "ideas", "brainstorm", "narrative", "writing"]):
        intent = "ideas"
        confidence = 0.8
        reasoning = "Strong creative writing keywords detected"
    # Handle pure greetings (with no other content)
    elif any(word in query_lower for word in ["hi", "hello", "hey", "greetings", "good morning", "good afternoon"]) and len(query_lower.split()) <= 3:
        intent = "general"
        confidence = 0.8  # High confidence for greeting - should get natural response
        reasoning = "Greeting detected - starting conversation"
    elif any(word in query_lower for word in ["help", "teach", "student", "classroom", "lesson"]):
        intent = "general"
        confidence = 0.6
        reasoning = "General education keywords detected"
    else:
        intent = "general"
        confidence = 0.3
        reasoning = "No clear domain keywords, low confidence"
    
    return {
        "original_query": query,
        "intent": intent,
        "confidence": confidence,
        "classification_reasoning": reasoning,
        "processing_steps": [f"Intent: {intent} (confidence: {confidence})"],
        "needs_clarification": confidence < 0.5
    }

async def route_to_bot_node(state: RoutingState) -> Dict[str, Any]:
    """
    Routing Decision Node - Decides which specialist bot to use based on confidence.
    This is the core routing logic that sends low confidence queries to general bot.
    """
    intent = state.get("intent", "general")
    confidence = state.get("confidence", 0.0)
    
    print(f"🔀 Routing: intent='{intent}', confidence={confidence:.2f}")
    
    # CORE ROUTING LOGIC - This is what you wanted to see!
    if confidence >= 0.7:
        # High confidence - route to specialist
        if intent == "handwriting":
            target_bot = "handwriting"
            routing_decision = f"HIGH CONFIDENCE ({confidence:.2f}) → Handwriting Specialist"
        elif intent == "vocabulary":
            target_bot = "vocabulary"
            routing_decision = f"HIGH CONFIDENCE ({confidence:.2f}) → Vocabulary Specialist"
        elif intent == "ideas":
            target_bot = "ideas"
            routing_decision = f"HIGH CONFIDENCE ({confidence:.2f}) → Ideas Specialist"
        else:
            target_bot = "general"
            routing_decision = f"General intent → General Bot"
    elif confidence >= 0.5:
        # Medium confidence - still route to specialist but with caution
        target_bot = intent
        routing_decision = f"MEDIUM CONFIDENCE ({confidence:.2f}) → {intent.title()} Specialist (with caution)"
    else:
        # LOW CONFIDENCE - route to general bot for clarification
        target_bot = "general"
        routing_decision = f"LOW CONFIDENCE ({confidence:.2f}) → General Bot (needs clarification)"
    
    return {
        "target_bot": target_bot,
        "routing_decision": routing_decision,
        "processing_steps": state.get("processing_steps", []) + [f"Routing: → {target_bot} bot"]
    }

async def execute_handwriting_bot_node(state: RoutingState) -> Dict[str, Any]:
    """Handwriting Specialist Bot - Uses actual handwriting graph implementation."""
    try:
        from app.graph.handwriting_graph import run_handwriting_bot

        query = state.get("original_query", "")
        teacher_id = state.get("teacher_id", "studio_teacher")
        session_id = state.get("session_id", "studio_session")

        print(f"🖊️ Executing real handwriting bot in Studio for query: {query}")

        # Run the actual handwriting bot graph
        handwriting_result = await run_handwriting_bot(
            teacher_query=query,
            teacher_id=teacher_id,
            session_id=session_id
        )

        # Extract response from handwriting bot result
        bot_messages = handwriting_result.get("messages", [])
        bot_response = ""

        # Find the last AI message
        for message in reversed(bot_messages):
            if hasattr(message, 'type') and message.type == 'ai':
                bot_response = message.content
                break
            elif hasattr(message, 'content') and isinstance(message.content, str):
                bot_response = message.content
                break

        if not bot_response:
            bot_response = "I apologize, but I wasn't able to generate a proper handwriting response."

        # Extract relevant forms
        relevant_forms = handwriting_result.get("relevant_forms", [])
        form_letters = [f"Form {form.get('form_letter', 'Unknown')}" for form in relevant_forms] if relevant_forms else []

        # Extract follow-up questions
        follow_up_questions = handwriting_result.get("follow_up_questions", [])

        return {
            "messages": [AIMessage(content=bot_response)],
            "bot_response": bot_response,
            "bot_type": "handwriting_specialist",
            "relevant_forms": form_letters,
            "follow_up_questions": follow_up_questions
        }

    except Exception as e:
        print(f"❌ Error in studio handwriting bot: {str(e)}")
        fallback_response = f"I apologize, but I'm having trouble with the handwriting bot. Error: {str(e)}"
        return {
            "messages": [AIMessage(content=fallback_response)],
            "bot_response": fallback_response,
            "bot_type": "handwriting_specialist_error",
            "relevant_forms": [],
            "follow_up_questions": []
        }

async def execute_vocabulary_bot_node(state: RoutingState) -> Dict[str, Any]:
    """Vocabulary Specialist Bot - Forms I-L (Reading, phonics, word recognition)."""
    query = state.get("original_query", "")
    
    response = f"""📚 **VOCABULARY SPECIALIST** (Forms I-L)

For your question: "{query}"

**Phonics Instruction:**
• Teach letter-sound correspondences systematically
• Use multi-sensory approaches (visual, auditory, kinesthetic)
• Practice blending and segmenting activities

**Sight Word Development:**
• Focus on high-frequency words
• Use repeated exposure and practice
• Create word walls and word banks

**Reading Comprehension:**
• Build background knowledge
• Teach context clue strategies
• Practice questioning techniques

**Forms Used:** I (Phonics Framework), J (Word Recognition), K (Vocabulary Activities)
"""
    
    return {
        "messages": [AIMessage(content=response)],
        "bot_response": response,
        "bot_type": "vocabulary_specialist",
        "relevant_forms": ["Form-I", "Form-J", "Form-K"],
        "follow_up_questions": ["Need phonics activity ideas?", "Want sight word strategies?"]
    }

async def execute_ideas_bot_node(state: RoutingState) -> Dict[str, Any]:
    """Ideas Specialist Bot - Forms M-Q (Creative writing, story development)."""
    query = state.get("original_query", "")
    
    response = f"""💡 **IDEAS SPECIALIST** (Forms M-Q)

For your question: "{query}"

**Creative Writing Prompts:**
• "What if animals could talk for one day?"
• "Design your dream playground - what would it have?"
• "Write about a magic pencil that draws real things"

**Story Development:**
• Use story maps (beginning, middle, end)
• Develop characters with interesting traits
• Create conflicts and resolutions

**Brainstorming Techniques:**
• Mind mapping for idea generation
• "What if" scenarios
• Collaborative storytelling circles

**Forms Used:** M (Genre Elements), N (Creative Techniques), O (Story Development)
"""
    
    return {
        "messages": [AIMessage(content=response)],
        "bot_response": response,
        "bot_type": "ideas_specialist",
        "relevant_forms": ["Form-M", "Form-N", "Form-O"],
        "follow_up_questions": ["Want more story prompts?", "Need character development ideas?"]
    }

async def execute_general_bot_node(state: RoutingState) -> Dict[str, Any]:
    """General Education Bot - For unclear queries or multi-domain questions."""
    query = state.get("original_query", "")
    confidence = state.get("confidence", 0.0)
    reasoning = state.get("classification_reasoning", "")
    
    # Check if this is a greeting
    is_greeting = "greeting detected" in reasoning.lower()
    
    if is_greeting:
        # Natural greeting response
        response = f"""👋 **Hello there!**

Welcome to your Educational Assistant! I'm here to help you with early childhood education strategies and lesson planning.

**I can assist you with:**

🖊️ **Handwriting & Fine Motor Skills**
   • Letter formation, pencil grip, writing posture, fine motor development

📚 **Vocabulary & Sentence Structure**
   • Vocabulary building, sentence patterns, word recognition strategies

💡 **Idea Generation & Writing Organization**
   • Brainstorming strategies, story planning, writing across different genres

🎓 **General Teaching Strategies**
   • Classroom management, assessment, differentiation, lesson planning

**What would you like help with today?** Just ask me about any teaching challenge you're facing!

*Examples: "How do I teach letter Z formation?" or "I need vocabulary activities" or "Help with brainstorming for narrative writing"*
"""
    elif confidence < 0.5:
        # Low confidence - ask for clarification  
        response = f"""🎓 **I'd love to help you!**

I want to give you the most helpful response possible. Could you help me understand what you're looking for?

**Are you asking about:**

🖊️ **Handwriting & Fine Motor Skills**
   • Letter formation, pencil grip, writing posture
   
📚 **Vocabulary & Reading**
   • Sight words, phonics, spelling, word recognition
   
💡 **Creative Writing & Ideas**
   • Story prompts, brainstorming, narrative development
   
🎓 **General Teaching Strategies**
   • Classroom management, assessment, differentiation

**Just let me know which area interests you, and I'll provide targeted strategies and resources!**
"""
    else:
        # General multi-domain response
        response = f"""🎓 **Educational Strategies & Tips**

**Cross-Domain Approach:**
• Integrate handwriting practice with vocabulary lessons
• Use creative writing to reinforce letter formation
• Combine phonics instruction with story writing activities

**General Teaching Best Practices:**
• Differentiate instruction for diverse learners
• Use ongoing assessment to guide instruction
• Create supportive, engaging learning environments
• Foster strong family and community connections

**Implementation Tips:**
• Start with foundational skills (handwriting, phonics)
• Gradually build towards creative expression
• Maintain consistent practice and feedback cycles
• Celebrate student progress and achievements

**Need More Specific Help?** I can provide detailed strategies for handwriting, vocabulary, or creative writing - just let me know which area you'd like to focus on!
"""
    
    return {
        "messages": [AIMessage(content=response)],
        "bot_response": response,
        "bot_type": "general_education_bot",
        "relevant_forms": ["All Forms A-Q"],
        "follow_up_questions": ["Which specific area would you like to focus on?", "Need more targeted strategies?"]
    }

# Conditional routing functions
def should_clarify(state: RoutingState) -> str:
    """
    CONFIDENCE CHECK - This is the key decision point!
    Low confidence → General Bot
    High confidence → Proceed to specialist routing
    """
    confidence = state.get("confidence", 0.0)
    needs_clarification = state.get("needs_clarification", False)
    
    if needs_clarification or confidence < 0.5:
        print(f"🤔 LOW CONFIDENCE ({confidence:.2f}) → Routing to General Bot")
        return "execute_general_bot"
    else:
        print(f"✅ SUFFICIENT CONFIDENCE ({confidence:.2f}) → Proceeding to specialist routing")
        return "route_to_bot"

def route_to_specialist(state: RoutingState) -> str:
    """
    SPECIALIST ROUTING - Routes to the appropriate domain expert.
    """
    target_bot = state.get("target_bot", "general")
    
    routing_map = {
        "handwriting": "execute_handwriting_bot",
        "vocabulary": "execute_vocabulary_bot", 
        "ideas": "execute_ideas_bot",
        "general": "execute_general_bot"
    }
    
    next_node = routing_map.get(target_bot, "execute_general_bot")
    print(f"🎯 ROUTING TO: {next_node}")
    return next_node

def create_studio_routing_graph():
    """
    Create the complete routing graph for LangGraph Studio visualization.
    Shows the full flow: Intent → Confidence Check → Specialist Routing
    """
    print("🔧 Building Complete Educational Routing Graph for Studio...")
    
    # Initialize the graph
    graph = StateGraph(RoutingState)
    
    # Add all nodes
    print("📍 Adding nodes...")
    graph.add_node("classify_intent", classify_intent_node)
    graph.add_node("route_to_bot", route_to_bot_node)
    graph.add_node("execute_handwriting_bot", execute_handwriting_bot_node)
    graph.add_node("execute_vocabulary_bot", execute_vocabulary_bot_node)
    graph.add_node("execute_ideas_bot", execute_ideas_bot_node)
    graph.add_node("execute_general_bot", execute_general_bot_node)
    
    # Set entry point
    print("🚀 Setting entry point...")
    graph.add_edge(START, "classify_intent")
    
    # Add conditional edges - THIS IS THE KEY FLOW YOU WANTED TO SEE!
    print("🔀 Adding conditional routing logic...")
    
    # Step 1: After intent classification → confidence check
    graph.add_conditional_edges(
        "classify_intent",
        should_clarify,  # This function checks confidence < 0.5
        {
            "route_to_bot": "route_to_bot",           # High confidence → proceed to specialist
            "execute_general_bot": "execute_general_bot"  # Low confidence → general bot
        }
    )
    
    # Step 2: After routing decision → go to appropriate specialist
    graph.add_conditional_edges(
        "route_to_bot", 
        route_to_specialist,  # This function routes to domain specialists
        {
            "execute_handwriting_bot": "execute_handwriting_bot",
            "execute_vocabulary_bot": "execute_vocabulary_bot",
            "execute_ideas_bot": "execute_ideas_bot",
            "execute_general_bot": "execute_general_bot"
        }
    )
    
    # All paths end the conversation
    graph.add_edge("execute_handwriting_bot", END)
    graph.add_edge("execute_vocabulary_bot", END)
    graph.add_edge("execute_ideas_bot", END)
    graph.add_edge("execute_general_bot", END)
    
    # Compile the graph
    compiled_graph = graph.compile()
    
    print("✅ Complete Educational Routing Graph compiled successfully!")
    print("📊 Graph Flow:")
    print("   START → classify_intent → [CONFIDENCE CHECK]")
    print("                               ↓ (high confidence)")
    print("                         route_to_bot → [SPECIALIST ROUTING]")
    print("                               ↓ (low confidence)")
    print("                         execute_general_bot → END")
    print("   Specialists: handwriting_bot, vocabulary_bot, ideas_bot → END")
    
    return compiled_graph

# Create the studio-friendly graph
studio_routing_graph = create_studio_routing_graph()