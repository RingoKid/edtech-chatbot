"""
Master Routing Graph for Educational Chatbot.
Routes teacher queries to specialized bots based on intent classification.
"""
import time
from typing import Dict, Any, Optional
from langraph.graph import StateGraph, END, START
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import HumanMessage, AIMessage

from app.graph.routing_state import RoutingState
from app.service.intent_classification_service import intent_service
from app.graph.handwriting_graph import run_handwriting_bot
from app.graph.vocabulary_graph import run_vocabulary_bot
from app.graph.ideas_graph import run_ideas_bot
from app.service.form_retrieval_service import form_retrieval_service
from app.schemas.intent import IntentType
from app.config import settings

# Import general bot for unclear queries
from app.service.specialized_bots import GeneralBot

class RoutingNodes:
    """Container for all routing graph nodes."""

    def __init__(self):
        """Initialize routing nodes with general bot only."""
        self.general_bot = GeneralBot()
        print("✅ Routing nodes initialized with general bot")

async def classify_intent_node(state: RoutingState) -> Dict[str, Any]:
    """
    Node 1: Classify the teacher's intent to determine routing.

    Args:
        state: Current routing state

    Returns:
        Updated state with intent classification results
    """
    try:
        start_time = time.time()

        # Get the teacher's message
        messages = state.get("messages", [])
        if not messages:
            raise ValueError("No messages found in state")

        latest_message = messages[-1]
        if hasattr(latest_message, 'content'):
            query = latest_message.content
        else:
            query = str(latest_message)

        # Build conversation context for better intent classification
        conversation_context = ""
        if len(messages) > 1:
            # Include previous messages for context with more detail
            previous_messages = []
            for i, msg in enumerate(messages[:-1]):  # All except latest
                if hasattr(msg, 'content'):
                    role = "Teacher" if hasattr(msg, 'type') and msg.type == 'human' else "Assistant"
                    # Include more context for better domain detection
                    content = msg.content[:200] if len(msg.content) > 200 else msg.content
                    previous_messages.append(f"{role}: {content}")

            if previous_messages:
                # Include more exchanges for better context (last 4 instead of 3)
                conversation_context = "\n".join(previous_messages[-4:])
                print(f"🔍 Conversation context for intent classification: {conversation_context[:200]}...")

        # Classify intent using the service with conversation context
        intent_result = await intent_service.classify_intent(query, conversation_context=conversation_context)
        processing_time = time.time() - start_time
        
        print(f"🎯 Intent Classification Result:")
        print(f"   Query: '{query[:50]}...'")
        print(f"   Intent: {intent_result.intent}")
        print(f"   Confidence: {intent_result.confidence:.2f}")
        print(f"   Reasoning: {intent_result.reasoning}")
        
        return {
            "original_query": query,
            "intent": intent_result.intent,
            "confidence": intent_result.confidence,
            "classification_reasoning": intent_result.reasoning,
            "processing_steps": [f"Intent classification: {intent_result.intent} ({intent_result.confidence:.2f})"],
            "total_processing_time": processing_time,
            "needs_clarification": intent_result.confidence < 0.5
        }
        
    except Exception as e:
        print(f"❌ Intent classification error: {str(e)}")
        return {
            "original_query": query if 'query' in locals() else "Unknown query",
            "intent": IntentType.GENERAL,
            "confidence": 0.3,
            "classification_reasoning": f"Classification failed: {str(e)}",
            "processing_steps": ["Intent classification failed, defaulting to general"],
            "last_error": str(e),
            "retry_count": state.get("retry_count", 0) + 1
        }

async def route_to_bot_node(state: RoutingState) -> Dict[str, Any]:
    """
    Node 2: Route to the appropriate specialized bot based on intent.
    
    Args:
        state: Current routing state
        
    Returns:
        Updated state with routing decision
    """
    try:
        start_time = time.time()
        
        intent = state.get("intent")
        confidence = state.get("confidence", 0.0)
        original_query = state.get("original_query", "")
        
        # Determine target bot based on intent and confidence
        if confidence >= 0.7:
            if intent == IntentType.HANDWRITING:
                target_bot = "handwriting"
                routing_decision = f"High confidence ({confidence:.2f}) handwriting query - routing to handwriting specialist"
            elif intent == IntentType.VOCABULARY:
                target_bot = "vocabulary"
                routing_decision = f"High confidence ({confidence:.2f}) vocabulary query - routing to vocabulary specialist"
            elif intent == IntentType.IDEAS:
                target_bot = "ideas"
                routing_decision = f"High confidence ({confidence:.2f}) ideas query - routing to ideas specialist"
            else:
                target_bot = "general"
                routing_decision = f"General intent with confidence {confidence:.2f} - routing to general bot"
        elif confidence >= 0.5:
            # Medium confidence - route to intended bot but note uncertainty
            target_bot = intent.value
            routing_decision = f"Medium confidence ({confidence:.2f}) - routing to {intent.value} specialist with caution"
        else:
            # Low confidence - route to general bot
            target_bot = "general"
            routing_decision = f"Low confidence ({confidence:.2f}) - routing to general bot for clarification"
        
        processing_time = time.time() - start_time
        
        current_steps = state.get("processing_steps", [])
        updated_steps = current_steps + [f"Routing decision: {target_bot} bot"]
        
        print(f"✅ Routing to {target_bot} bot")
        
        return {
            "target_bot": target_bot,
            "routing_decision": routing_decision,
            "processing_steps": updated_steps,
            "total_processing_time": state.get("total_processing_time", 0) + processing_time
        }
        
    except Exception as e:
        print(f"❌ Routing error: {str(e)}")
        return {
            "target_bot": "general",
            "routing_decision": f"Routing failed, defaulting to general bot: {str(e)}",
            "last_error": str(e),
            "retry_count": state.get("retry_count", 0) + 1
        }

async def execute_handwriting_bot_node(state: RoutingState) -> Dict[str, Any]:
    """
    Node 3a: Execute the handwriting specialist bot.

    Args:
        state: Current routing state

    Returns:
        Updated state with handwriting bot response
    """
    try:
        start_time = time.time()

        original_query = state.get("original_query", "")
        teacher_id = state.get("teacher_id", "teacher_001")
        session_id = state.get("session_id", "session_001")
        messages = state.get("messages", [])

        print(f"🖊️ Executing handwriting bot for query")
        print(f"📝 Passing {len(messages)} messages as conversation history")

        # Run the existing handwriting bot graph with conversation history
        handwriting_result = await run_handwriting_bot(
            teacher_query=original_query,
            teacher_id=teacher_id,
            session_id=session_id,
            conversation_history=messages  # Pass full conversation history
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
        
        # Extract relevant forms from handwriting result
        relevant_forms = handwriting_result.get("relevant_forms", [])
        form_letters = [f"Form {form.get('form_letter', 'Unknown')}" for form in relevant_forms]
        
        # Extract follow-up questions
        follow_up_questions = handwriting_result.get("follow_up_questions", [])
        
        processing_time = time.time() - start_time
        
        # Create AI message for the conversation
        ai_response = AIMessage(content=bot_response)
        
        current_steps = state.get("processing_steps", [])
        updated_steps = current_steps + [f"Handwriting bot executed successfully"]
        
        print(f"✅ Handwriting bot completed in {processing_time:.2f}s")
        
        return {
            "messages": [ai_response],
            "bot_response": bot_response,
            "bot_type": "handwriting_specialist",
            "relevant_forms": form_letters,
            "follow_up_questions": follow_up_questions,
            "processing_steps": updated_steps,
            "total_processing_time": state.get("total_processing_time", 0) + processing_time
        }
        
    except Exception as e:
        print(f"❌ Handwriting bot error: {str(e)}")
        fallback_response = f"I apologize, but I'm having trouble with my handwriting expertise right now. Error: {str(e)}"
        return {
            "messages": [AIMessage(content=fallback_response)],
            "bot_response": fallback_response,
            "bot_type": "handwriting_specialist_error",
            "relevant_forms": [],
            "follow_up_questions": [],
            "last_error": str(e)
        }

async def execute_vocabulary_bot_node(state: RoutingState) -> Dict[str, Any]:
    """
    Node 3b: Execute the vocabulary specialist bot.

    Args:
        state: Current routing state

    Returns:
        Updated state with vocabulary bot response
    """
    try:
        start_time = time.time()

        original_query = state.get("original_query", "")
        teacher_id = state.get("teacher_id", "teacher_001")
        session_id = state.get("session_id", "session_001")
        messages = state.get("messages", [])

        print(f"📚 Executing vocabulary bot for query")
        print(f"📝 Passing {len(messages)} messages as conversation history")

        # Run the vocabulary bot graph with conversation history
        vocabulary_result = await run_vocabulary_bot(
            teacher_query=original_query,
            teacher_id=teacher_id,
            session_id=session_id,
            conversation_history=messages
        )

        # Extract response from vocabulary bot result
        bot_messages = vocabulary_result.get("messages", [])
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
            bot_response = "I apologize, but I wasn't able to generate a proper vocabulary response."

        # Extract relevant forms from vocabulary result
        relevant_forms = vocabulary_result.get("relevant_forms", [])
        form_letters = [f"Form {form.get('form_letter', 'Unknown')}" for form in relevant_forms] if isinstance(relevant_forms, list) and relevant_forms and isinstance(relevant_forms[0], dict) else relevant_forms

        # Extract follow-up questions
        follow_up_questions = vocabulary_result.get("follow_up_questions", [])

        processing_time = time.time() - start_time

        # Create AI message for the conversation
        ai_response = AIMessage(content=bot_response)

        current_steps = state.get("processing_steps", [])
        updated_steps = current_steps + [f"Vocabulary bot executed successfully"]

        print(f"✅ Vocabulary bot completed in {processing_time:.2f}s")

        return {
            "messages": [ai_response],
            "bot_response": bot_response,
            "bot_type": "vocabulary_specialist",
            "relevant_forms": form_letters if isinstance(form_letters, list) else [],
            "follow_up_questions": follow_up_questions,
            "processing_steps": updated_steps,
            "total_processing_time": state.get("total_processing_time", 0) + processing_time
        }

    except Exception as e:
        print(f"❌ Vocabulary bot error: {str(e)}")
        fallback_response = f"I apologize, but I'm having trouble with my vocabulary expertise right now. Error: {str(e)}"
        return {
            "messages": [AIMessage(content=fallback_response)],
            "bot_response": fallback_response,
            "bot_type": "vocabulary_specialist_error",
            "relevant_forms": [],
            "follow_up_questions": [],
            "last_error": str(e)
        }

async def execute_ideas_bot_node(state: RoutingState) -> Dict[str, Any]:
    """
    Node 3c: Execute the ideas specialist bot.

    Args:
        state: Current routing state

    Returns:
        Updated state with ideas bot response
    """
    try:
        start_time = time.time()

        original_query = state.get("original_query", "")
        teacher_id = state.get("teacher_id", "teacher_001")
        session_id = state.get("session_id", "session_001")
        messages = state.get("messages", [])

        print(f"💡 Executing ideas bot for query")
        print(f"📝 Passing {len(messages)} messages as conversation history")

        # Run the ideas bot graph with conversation history
        ideas_result = await run_ideas_bot(
            teacher_query=original_query,
            teacher_id=teacher_id,
            session_id=session_id,
            conversation_history=messages
        )

        # Extract response from ideas bot result
        bot_messages = ideas_result.get("messages", [])
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
            bot_response = "I apologize, but I wasn't able to generate a proper ideas response."

        # Extract relevant forms from ideas result
        relevant_forms = ideas_result.get("relevant_forms", [])
        form_letters = [f"Form {form.get('form_letter', 'Unknown')}" for form in relevant_forms] if isinstance(relevant_forms, list) and relevant_forms and isinstance(relevant_forms[0], dict) else relevant_forms

        # Extract follow-up questions
        follow_up_questions = ideas_result.get("follow_up_questions", [])

        processing_time = time.time() - start_time

        # Create AI message for the conversation
        ai_response = AIMessage(content=bot_response)

        current_steps = state.get("processing_steps", [])
        updated_steps = current_steps + [f"Ideas bot executed successfully"]

        print(f"✅ Ideas bot completed in {processing_time:.2f}s")

        return {
            "messages": [ai_response],
            "bot_response": bot_response,
            "bot_type": "ideas_specialist",
            "relevant_forms": form_letters if isinstance(form_letters, list) else [],
            "follow_up_questions": follow_up_questions,
            "processing_steps": updated_steps,
            "total_processing_time": state.get("total_processing_time", 0) + processing_time
        }

    except Exception as e:
        print(f"❌ Ideas bot error: {str(e)}")
        fallback_response = f"I apologize, but I'm having trouble with my creative writing expertise right now. Error: {str(e)}"
        return {
            "messages": [AIMessage(content=fallback_response)],
            "bot_response": fallback_response,
            "bot_type": "ideas_specialist_error",
            "relevant_forms": [],
            "follow_up_questions": [],
            "last_error": str(e)
        }

async def execute_general_bot_node(state: RoutingState) -> Dict[str, Any]:
    """
    Node 3d: Execute the general education bot.
    
    Args:
        state: Current routing state
        
    Returns:
        Updated state with general bot response
    """
    try:
        start_time = time.time()
        
        original_query = state.get("original_query", "")
        messages = state.get("messages", [])
        confidence = state.get("confidence", 0.0)

        print(f"🎓 Executing general bot for query")
        print(f"📝 Passing {len(messages)} messages as conversation history")

        # Use the routing nodes instance
        routing_nodes = RoutingNodes()

        # Always process through the GeneralBot (it handles greetings, clarifications, and general questions)
        result = await routing_nodes.general_bot.process_message(original_query, conversation_history=messages)
        result_response = result.response
        bot_type = result.bot_type
        
        processing_time = time.time() - start_time
        
        # Create AI message for the conversation
        ai_response = AIMessage(content=result_response)
        
        current_steps = state.get("processing_steps", [])
        updated_steps = current_steps + [f"General bot executed successfully"]
        
        print(f"✅ General bot completed in {processing_time:.2f}s")
        
        return {
            "messages": [ai_response],
            "bot_response": result_response,
            "bot_type": bot_type,
            "relevant_forms": ["A-Q"] if confidence >= 0.5 else [],
            "follow_up_questions": ["Would you like me to elaborate on any specific area?"],
            "processing_steps": updated_steps,
            "total_processing_time": state.get("total_processing_time", 0) + processing_time
        }
        
    except Exception as e:
        print(f"❌ General bot error: {str(e)}")
        fallback_response = f"I apologize, but I'm experiencing technical difficulties. Please try rephrasing your question."
        return {
            "messages": [AIMessage(content=fallback_response)],
            "bot_response": fallback_response,
            "bot_type": "general_bot_error", 
            "relevant_forms": [],
            "follow_up_questions": [],
            "last_error": str(e)
        }

def should_clarify(state: RoutingState) -> str:
    """
    Conditional edge function to determine if clarification is needed.
    
    Args:
        state: Current routing state
        
    Returns:
        Next node based on confidence level
    """
    confidence = state.get("confidence", 0.0)
    needs_clarification = state.get("needs_clarification", False)
    
    if needs_clarification or confidence < 0.5:
        print(f"🤔 Low confidence ({confidence:.2f}) - routing to general bot for clarification")
        return "execute_general_bot"
    else:
        return "route_to_bot"

def route_to_specialist(state: RoutingState) -> str:
    """
    Conditional edge function to route to the appropriate specialist bot.
    
    Args:
        state: Current routing state
        
    Returns:
        Target bot node name
    """
    target_bot = state.get("target_bot", "general")
    
    routing_map = {
        "handwriting": "execute_handwriting_bot",
        "vocabulary": "execute_vocabulary_bot", 
        "ideas": "execute_ideas_bot",
        "general": "execute_general_bot"
    }
    
    return routing_map.get(target_bot, "execute_general_bot")

def create_routing_graph():
    """
    Create and compile the master routing graph.
    
    Returns:
        Compiled LangGraph for educational chatbot routing
    """
    print("🔧 Building Master Routing Graph...")
    
    # Initialize the graph with our state schema
    graph = StateGraph(RoutingState)
    
    # Add all nodes to the graph
    print("📍 Adding nodes...")
    graph.add_node("classify_intent", classify_intent_node)
    graph.add_node("route_to_bot", route_to_bot_node)
    graph.add_node("execute_handwriting_bot", execute_handwriting_bot_node)
    graph.add_node("execute_vocabulary_bot", execute_vocabulary_bot_node)
    graph.add_node("execute_ideas_bot", execute_ideas_bot_node)
    graph.add_node("execute_general_bot", execute_general_bot_node)
    
    # Set the entry point
    print("🚀 Setting entry point...")
    graph.add_edge(START, "classify_intent")
    
    # Add conditional edges for routing logic
    print("🔀 Adding conditional edges...")
    
    # After intent classification, check if clarification is needed
    graph.add_conditional_edges(
        "classify_intent",
        should_clarify,
        {
            "route_to_bot": "route_to_bot",
            "execute_general_bot": "execute_general_bot"
        }
    )
    
    # After routing decision, go to appropriate specialist
    graph.add_conditional_edges(
        "route_to_bot", 
        route_to_specialist,
        {
            "execute_handwriting_bot": "execute_handwriting_bot",
            "execute_vocabulary_bot": "execute_vocabulary_bot",
            "execute_ideas_bot": "execute_ideas_bot",
            "execute_general_bot": "execute_general_bot"
        }
    )
    
    # All specialist bots end the conversation
    graph.add_edge("execute_handwriting_bot", END)
    graph.add_edge("execute_vocabulary_bot", END)
    graph.add_edge("execute_ideas_bot", END)
    graph.add_edge("execute_general_bot", END)
    
    # Compile the graph
    print("⚙️ Compiling graph...")
    compiled_graph = graph.compile()
    
    print("✅ Master Routing Graph compiled successfully!")
    print("📊 Graph structure:")
    print("   START -> classify_intent -> [clarification check] -> route_to_bot -> [specialist] -> END")
    print("   Specialists: handwriting, vocabulary, ideas, general")
    print("   Automatic fallback to general bot for low confidence or errors")
    
    return compiled_graph

# Create TWO graph instances:
# 1. For LangGraph Studio (no checkpointer)
routing_graph = create_routing_graph()

# 2. For API with conversation memory (with checkpointer)
print("🗄️ Creating API graph with SqliteSaver checkpointer...")
api_checkpointer = SqliteSaver.from_conn_string(":memory:")  # In-memory SQLite for persistence
routing_graph_with_memory = create_routing_graph()
# Re-compile with checkpointer for API use
graph_builder = StateGraph(RoutingState)
# Copy all nodes and edges (reuse the same structure)
for node_name in ["classify_intent", "route_to_bot", "execute_handwriting_bot", "execute_vocabulary_bot", "execute_ideas_bot", "execute_general_bot"]:
    if node_name == "classify_intent":
        graph_builder.add_node(node_name, classify_intent_node)
    elif node_name == "route_to_bot":
        graph_builder.add_node(node_name, route_to_bot_node)
    elif node_name == "execute_handwriting_bot":
        graph_builder.add_node(node_name, execute_handwriting_bot_node)
    elif node_name == "execute_vocabulary_bot":
        graph_builder.add_node(node_name, execute_vocabulary_bot_node)
    elif node_name == "execute_ideas_bot":
        graph_builder.add_node(node_name, execute_ideas_bot_node)
    elif node_name == "execute_general_bot":
        graph_builder.add_node(node_name, execute_general_bot_node)

graph_builder.add_edge(START, "classify_intent")
graph_builder.add_conditional_edges("classify_intent", should_clarify, {"route_to_bot": "route_to_bot", "execute_general_bot": "execute_general_bot"})
graph_builder.add_conditional_edges("route_to_bot", route_to_specialist, {"execute_handwriting_bot": "execute_handwriting_bot", "execute_vocabulary_bot": "execute_vocabulary_bot", "execute_ideas_bot": "execute_ideas_bot", "execute_general_bot": "execute_general_bot"})
graph_builder.add_edge("execute_handwriting_bot", END)
graph_builder.add_edge("execute_vocabulary_bot", END)
graph_builder.add_edge("execute_ideas_bot", END)
graph_builder.add_edge("execute_general_bot", END)

routing_graph_with_memory = graph_builder.compile(checkpointer=api_checkpointer)
print("✅ API graph with memory compiled successfully!")

# Function to run the complete routing system
async def run_educational_chatbot(teacher_query: str, teacher_id: str = "teacher_001", session_id: str = "session_001"):
    """
    Run the complete educational chatbot with intent classification and routing.

    Args:
        teacher_query: The teacher's question
        teacher_id: Unique identifier for the teacher
        session_id: Unique identifier for the conversation session

    Returns:
        Final state with the complete bot response
    """

    # Configuration for the graph execution
    config = {
        "configurable": {
            "thread_id": f"{teacher_id}_{session_id}"
        }
    }

    try:
        # Get existing conversation state from checkpointer if available
        existing_state = None
        try:
            existing_state = await routing_graph_with_memory.aget_state(config)
        except Exception as e:
            print(f"⚠️ No existing state found (this is normal for first message): {e}")

        # Build message history
        existing_messages = []
        if existing_state and existing_state.values and "messages" in existing_state.values:
            existing_messages = existing_state.values["messages"]
            print(f"📜 Found {len(existing_messages)} existing messages in conversation history")

        # Append the new message to conversation history
        all_messages = existing_messages + [HumanMessage(content=teacher_query)]
        print(f"💬 Total messages in conversation: {len(all_messages)}")

        initial_state = {
            "messages": all_messages,  # Include full conversation history
            "teacher_id": teacher_id,
            "session_id": session_id,
            "original_query": teacher_query,
            "intent": None,
            "confidence": 0.0,
            "classification_reasoning": None,
            "target_bot": None,
            "routing_decision": None,
            "bot_response": None,
            "bot_type": None,
            "relevant_forms": [],
            "follow_up_questions": [],
            "processing_steps": [],
            "total_processing_time": 0.0,
            "needs_clarification": False,
            "last_error": None,
            "retry_count": 0,
            "conversation_depth": len(existing_messages) // 2,  # Count conversation turns
            "previous_intents": []
        }

        # Use the graph WITH checkpointer for conversation memory
        final_state = await routing_graph_with_memory.ainvoke(initial_state, config)
        return final_state
        
    except Exception as e:
        # Return error state
        error_message = AIMessage(content=f"I apologize, but I encountered an error: {str(e)}. Please try again.")
        return {
            **initial_state,
            "messages": initial_state["messages"] + [error_message],
            "bot_response": f"Error: {str(e)}",
            "bot_type": "system_error",
            "last_error": str(e)
        }

# Function to stream the routing execution (for real-time responses)
async def stream_educational_chatbot(teacher_query: str, teacher_id: str = "teacher_001", session_id: str = "session_001"):
    """
    Stream the educational chatbot execution for real-time responses.
    
    Args:
        teacher_query: The teacher's question
        teacher_id: Unique identifier for the teacher  
        session_id: Unique identifier for the conversation session
        
    Yields:
        State updates as the graph executes
    """
    print(f"🎯 Streaming educational query: '{teacher_query[:50]}...'")
    
    # Create initial state (same as above)
    initial_state = {
        "messages": [HumanMessage(content=teacher_query)],
        "teacher_id": teacher_id,
        "session_id": session_id,
        "original_query": teacher_query,
        "intent": None,
        "confidence": 0.0,
        "classification_reasoning": None,
        "target_bot": None,
        "routing_decision": None,
        "bot_response": None,
        "bot_type": None,
        "relevant_forms": [],
        "follow_up_questions": [],
        "processing_steps": [],
        "total_processing_time": 0.0,
        "needs_clarification": False,
        "last_error": None,
        "retry_count": 0,
        "conversation_depth": 0,
        "previous_intents": []
    }
    
    # Configuration for the graph execution
    config = {
        "configurable": {
            "thread_id": f"{teacher_id}_{session_id}"
        }
    }
    
    try:
        # Stream the graph execution
        print("🚀 Streaming educational chatbot routing...")
        async for chunk in routing_graph.astream(initial_state, config):
            yield chunk
            
        print("✅ Routing streaming completed!")
        
    except Exception as e:
        print(f"❌ Error streaming educational chatbot: {str(e)}")
        # Yield error state
        error_message = AIMessage(content=f"I apologize, but I encountered an error: {str(e)}. Please try again.")
        yield {
            "error": {
                **initial_state,
                "messages": initial_state["messages"] + [error_message],
                "bot_response": f"Error: {str(e)}",
                "bot_type": "system_error",
                "last_error": str(e)
            }
        }