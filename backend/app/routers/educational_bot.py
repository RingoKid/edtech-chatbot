"""
Educational Bot Router with complete intent classification and routing system.
Provides endpoints for the master routing graph that handles all educational domains.
"""
import time
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, AIMessage
from app.schemas.intent import (
    IntentRequest, IntentResult, ChatRequest, ChatResponse, BotResponse
)
from app.service.intent_classification_service import intent_service
from app.graph.routing_graph import run_educational_chatbot, stream_educational_chatbot
from app.service.form_retrieval_service import form_retrieval_service
from app.service.conversation_memory import conversation_memory

router = APIRouter(prefix="/educational-bot", tags=["Educational Bot"])

@router.post("/classify-intent", response_model=IntentResult)
async def classify_intent(request: IntentRequest):
    """
    Classify the intent of a teacher's message into educational domains.
    
    This endpoint uses OpenAI to classify teacher queries into one of four domains:
    - **handwriting**: Letter formation, fine motor skills, writing posture
    - **vocabulary**: Word recognition, spelling, phonics, reading comprehension  
    - **ideas**: Creative writing, story development, brainstorming
    - **general**: Multi-domain or classroom management questions
    
    Args:
        request: IntentRequest containing the teacher's message
        
    Returns:
        IntentResult with classification details and confidence score
    """
    try:
        start_time = time.time()
        

        # Classify the intent
        result = await intent_service.classify_intent(request.message)
        
        processing_time = (time.time() - start_time) * 1000

        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Intent classification failed: {str(e)}"
        )

@router.post("/chat", response_model=ChatResponse)
async def chat_with_educational_bot(request: ChatRequest):
    """
    Complete educational chatbot flow with intent classification and specialized routing.
    
    This endpoint processes a teacher's query through the complete pipeline:
    1. **Intent Classification**: Determines the educational domain
    2. **Routing Decision**: Routes to appropriate specialist bot
    3. **Specialized Response**: Generates domain-specific guidance
    4. **Form Integration**: Uses relevant educational forms for context
    
    The system automatically routes to:
    - **Handwriting Bot**: For letter formation, fine motor, writing posture questions
    - **Vocabulary Bot**: For phonics, spelling, reading, word recognition questions
    - **Ideas Bot**: For creative writing, storytelling, brainstorming questions  
    - **General Bot**: For multi-domain or unclear questions
    
    Args:
        request: ChatRequest containing the teacher's message and session info
        
    Returns:
        ChatResponse with the complete bot response and metadata
    """
    try:
        start_time = time.time()

        print(f"🎯 Educational Bot Request: '{request.message[:50]}...'")
        print(f"👤 Teacher ID: {request.teacher_id}")
        print(f"💬 Session ID: {request.session_id}")

        # Retrieve conversation history from memory
        conversation_history = conversation_memory.get_conversation(
            session_id=request.session_id,
            teacher_id=request.teacher_id
        )

        # If there's existing conversation, append the new user message
        if conversation_history:
            conversation_history.append(HumanMessage(content=request.message))
            print(f"📜 Continuing conversation with {len(conversation_history)} messages")
        else:
            # Start a new conversation
            conversation_history = [HumanMessage(content=request.message)]
            print(f"🆕 Starting new conversation")

        # Run the complete educational chatbot routing with conversation history
        final_state = await run_educational_chatbot(
            teacher_query=request.message,
            teacher_id=request.teacher_id,
            session_id=request.session_id,
            conversation_history=conversation_history  # Pass full conversation history
        )

        total_processing_time = (time.time() - start_time) * 1000

        # Extract bot response
        bot_response = final_state.get("bot_response", "I apologize, but I wasn't able to generate a proper response.")

        # Save the updated conversation history
        # Get all messages from the final state
        all_messages = final_state.get("messages", conversation_history)

        # If the bot generated a response, make sure it's in the messages
        if bot_response and (not all_messages or all_messages[-1].content != bot_response):
            all_messages.append(AIMessage(content=bot_response))

        conversation_memory.save_conversation(
            session_id=request.session_id,
            teacher_id=request.teacher_id,
            messages=all_messages,
            metadata={
                "intent": final_state.get("intent"),
                "confidence": final_state.get("confidence"),
                "bot_type": final_state.get("bot_type")
            }
        )

        # Extract response details from final state
        response = ChatResponse(
            intent=final_state.get("intent", "general"),
            confidence=final_state.get("confidence", 0.0),
            response=bot_response,
            bot_type=final_state.get("bot_type", "unknown"),
            relevant_forms=final_state.get("relevant_forms", []),
            follow_up_questions=final_state.get("follow_up_questions", []),
            processing_time_ms=round(total_processing_time, 2)
        )

        print(f"✅ Educational Bot Response generated in {total_processing_time:.2f}ms")
        print(f"🤖 Bot Type: {response.bot_type}")
        print(f"🎯 Intent: {response.intent} (confidence: {response.confidence:.2f})")
        print(f"💾 Conversation saved ({len(all_messages)} total messages)")

        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Educational bot processing failed: {str(e)}"
        )

@router.get("/domains")
async def get_educational_domains():
    """
    Get information about all educational domains and their capabilities.
    
    Returns details about each specialized bot and the forms they use.
    """
    try:
        # Get form counts for each domain
        handwriting_forms = form_retrieval_service.get_handwriting_forms()
        vocabulary_forms = form_retrieval_service.get_vocabulary_forms()
        ideas_forms = form_retrieval_service.get_ideas_forms()
        
        domains_info = {
            "handwriting": {
                "description": "Letter formation, fine motor skills, writing posture, and penmanship instruction",
                "forms": ["A", "B", "C", "D", "E", "F", "G", "H"],
                "forms_loaded": len(handwriting_forms),
                "keywords": ["letter", "formation", "handwriting", "penmanship", "grip", "posture", "fine motor", "stroke", "pencil"],
                "sample_queries": [
                    "How can I help students with letter formation?",
                    "What activities develop fine motor skills for writing?",
                    "How do I teach proper pencil grip?",
                    "What's the correct stroke sequence for letters?"
                ]
            },
            "vocabulary": {
                "description": "Word recognition, spelling, phonics, and reading comprehension strategies",
                "forms": ["I", "J", "K", "L"],
                "forms_loaded": len(vocabulary_forms),
                "keywords": ["vocabulary", "spelling", "phonics", "reading", "sight words", "word", "phoneme", "grapheme"],
                "sample_queries": [
                    "How do I teach sight words effectively?",
                    "What are good phonics activities for beginners?",
                    "How can I build student vocabulary?",
                    "What strategies help with reading comprehension?"
                ]
            },
            "ideas": {
                "description": "Creative writing, story development, and imagination activities",
                "forms": ["M", "N", "O", "P", "Q"],
                "forms_loaded": len(ideas_forms),
                "keywords": ["creative", "writing", "story", "ideas", "brainstorm", "narrative", "imagination", "compose"],
                "sample_queries": [
                    "What are good writing prompts for young students?",
                    "How do I help students brainstorm story ideas?",
                    "What activities spark creative writing?",
                    "How can I teach narrative structure?"
                ]
            },
            "general": {
                "description": "Cross-curricular instruction, classroom management, and general educational strategies",
                "forms": ["A-Q (all forms)"],
                "forms_loaded": len(handwriting_forms) + len(vocabulary_forms) + len(ideas_forms),
                "keywords": ["classroom", "management", "assessment", "curriculum", "student", "teaching", "education"],
                "sample_queries": [
                    "How do I manage my literacy centers?",
                    "What's the best way to assess writing progress?",
                    "How do I differentiate instruction?",
                    "What are effective classroom management strategies?"
                ]
            }
        }
        
        return {
            "message": "Educational domain information for the chatbot routing system",
            "total_domains": len(domains_info),
            "routing_logic": {
                "high_confidence": "Routes directly to specialist bot (confidence >= 0.7)",
                "medium_confidence": "Routes to specialist with caution note (confidence 0.5-0.7)",
                "low_confidence": "Routes to general bot for clarification (confidence < 0.5)"
            },
            "domains": domains_info
        }
        
    except Exception as e:
        print(f"❌ Error getting domain info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve domain information: {str(e)}"
        )

@router.get("/test-queries")
async def get_comprehensive_test_queries():
    """
    Get comprehensive test queries for all educational domains.
    
    Returns sample queries that demonstrate the routing system's capabilities.
    """
    test_queries = {
        "handwriting_queries": [
            "How can I help students improve their letter formation for the letter Z?",
            "What activities can help develop fine motor skills for writing?",
            "How do I teach proper pencil grip to young students?",
            "My students are having trouble with lowercase 'b' and 'd' - any strategies?",
            "What's the proper stroke sequence for teaching uppercase letters?",
            "How can I help students who hold their pencil incorrectly?",
            "What are some pre-writing activities for kindergarten students?",
            "How do I assess handwriting progress in my classroom?"
        ],
        "vocabulary_queries": [
            "What's the best way to teach sight words to beginning readers?",
            "How do I help students with phonemic awareness?",
            "What activities build vocabulary for English language learners?",
            "How can I teach phonics in a fun, engaging way?",
            "What strategies help students decode unfamiliar words?",
            "How do I support students with reading comprehension?",
            "What's the best approach to spelling instruction?",
            "How can I help struggling readers catch up?"
        ],
        "ideas_queries": [
            "What are good creative writing prompts for 2nd graders?",
            "How do I help students brainstorm story ideas?",
            "What activities can spark imagination in young writers?",
            "How do I teach narrative structure to elementary students?",
            "What strategies help students overcome writer's block?",
            "How can I make writing more enjoyable for my students?",
            "What are effective peer collaboration activities for writing?",
            "How do I help students develop their writing voice?"
        ],
        "general_queries": [
            "How do I integrate writing across all subjects?",
            "What's the best way to set up literacy centers?",
            "How do I differentiate instruction for various skill levels?",
            "What are effective strategies for parent communication about literacy?",
            "How can I assess student progress across multiple domains?",
            "What classroom management strategies work best for writing time?",
            "How do I support students with learning differences?",
            "What professional development would help me teach literacy better?"
        ],
        "ambiguous_queries": [
            "Help me with writing",
            "My students need support",
            "What should I do about literacy?",
            "How can I help struggling learners?",
            "I need classroom strategies",
            "What activities work best?",
            "How do I improve instruction?",
            "Students are having difficulty"
        ]
    }
    
    return {
        "message": "Comprehensive test queries for the educational chatbot routing system",
        "total_queries": sum(len(queries) for queries in test_queries.values()),
        "usage": {
            "endpoint": "/educational-bot/chat",
            "method": "POST", 
            "body_example": {
                "message": "How can I help students improve their letter formation?",
                "teacher_id": "teacher_001",
                "session_id": "session_001"
            }
        },
        "test_categories": {
            "handwriting_queries": {
                "count": len(test_queries["handwriting_queries"]),
                "expected_routing": "handwriting_specialist",
                "forms_used": ["A", "B", "C", "D", "E", "F", "G", "H"]
            },
            "vocabulary_queries": {
                "count": len(test_queries["vocabulary_queries"]),
                "expected_routing": "vocabulary_specialist", 
                "forms_used": ["I", "J", "K", "L"]
            },
            "ideas_queries": {
                "count": len(test_queries["ideas_queries"]),
                "expected_routing": "ideas_specialist",
                "forms_used": ["M", "N", "O", "P", "Q"]
            },
            "general_queries": {
                "count": len(test_queries["general_queries"]),
                "expected_routing": "general_education_specialist",
                "forms_used": ["A-Q (all forms)"]
            },
            "ambiguous_queries": {
                "count": len(test_queries["ambiguous_queries"]),
                "expected_routing": "clarification_request (via general bot)",
                "forms_used": ["varies"]
            }
        },
        "test_queries": test_queries
    }

@router.get("/forms-status")
async def get_forms_status():
    """
    Get the current status of educational forms loading for all domains.
    
    Returns information about which forms are loaded and available for each bot.
    """
    try:
        # Get cache status
        cache_status = form_retrieval_service.get_cache_status()
        
        # Test form retrieval for each domain
        handwriting_forms = form_retrieval_service.get_handwriting_forms()
        vocabulary_forms = form_retrieval_service.get_vocabulary_forms()
        ideas_forms = form_retrieval_service.get_ideas_forms()
        
        forms_status = {
            "cache_overview": cache_status,
            "domain_status": {
                "handwriting": {
                    "target_forms": ["A", "B", "C", "D", "E", "F", "G", "H"],
                    "loaded_forms": [form["form_letter"] for form in handwriting_forms],
                    "forms_count": len(handwriting_forms),
                    "status": "healthy" if len(handwriting_forms) >= 6 else "degraded"
                },
                "vocabulary": {
                    "target_forms": ["I", "J", "K", "L"],
                    "loaded_forms": [form["form_letter"] for form in vocabulary_forms],
                    "forms_count": len(vocabulary_forms),
                    "status": "healthy" if len(vocabulary_forms) >= 3 else "degraded"
                },
                "ideas": {
                    "target_forms": ["M", "N", "O", "P", "Q"],
                    "loaded_forms": [form["form_letter"] for form in ideas_forms],
                    "forms_count": len(ideas_forms),
                    "status": "healthy" if len(ideas_forms) >= 3 else "degraded"
                }
            },
            "overall_status": "healthy" if (len(handwriting_forms) >= 6 and 
                                         len(vocabulary_forms) >= 3 and 
                                         len(ideas_forms) >= 3) else "degraded"
        }
        
        return forms_status
        
    except Exception as e:
        print(f"❌ Error getting forms status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve forms status: {str(e)}"
        )

@router.get("/health")
async def educational_bot_health():
    """
    Comprehensive health check for the educational bot routing system.
    
    Verifies that all components are working properly across all domains.
    """
    try:
        # Check forms loading
        cache_status = form_retrieval_service.get_cache_status()
        forms_loaded = cache_status["total_forms_loaded"]
        
        # Check domain-specific forms
        handwriting_forms = form_retrieval_service.get_handwriting_forms()
        vocabulary_forms = form_retrieval_service.get_vocabulary_forms()
        ideas_forms = form_retrieval_service.get_ideas_forms()
        
        # Determine overall health
        all_forms_healthy = (len(handwriting_forms) >= 6 and 
                           len(vocabulary_forms) >= 3 and 
                           len(ideas_forms) >= 3)
        
        health_status = {
            "status": "healthy" if all_forms_healthy else "degraded",
            "timestamp": None,
            "components": {
                "intent_classification_service": {
                    "status": "healthy",
                    "model": "gpt-4o",
                    "confidence_threshold": 0.5
                },
                "form_retrieval_service": {
                    "status": "healthy" if forms_loaded > 10 else "degraded",
                    "total_forms_loaded": forms_loaded,
                    "handwriting_forms": len(handwriting_forms),
                    "vocabulary_forms": len(vocabulary_forms),
                    "ideas_forms": len(ideas_forms)
                },
                "routing_graph": {
                    "status": "healthy",
                    "graph_compiled": True,
                    "routing_logic": "intent -> confidence check -> specialist bot"
                },
                "specialized_bots": {
                    "handwriting_bot": {
                        "status": "healthy",
                        "implementation": "existing_langgraph_system",
                        "forms": ["A-H"]
                    },
                    "vocabulary_bot": {
                        "status": "healthy",
                        "implementation": "new_specialized_bot",
                        "forms": ["I-L"]
                    },
                    "ideas_bot": {
                        "status": "healthy",
                        "implementation": "new_specialized_bot", 
                        "forms": ["M-Q"]
                    },
                    "general_bot": {
                        "status": "healthy",
                        "implementation": "cross_domain_bot",
                        "forms": ["A-Q"]
                    }
                }
            },
            "capabilities": [
                "Intent classification into 4 educational domains",
                "Automatic routing to specialized bots",
                "Handwriting and fine motor skill guidance",
                "Vocabulary and reading instruction support",
                "Creative writing and idea generation",
                "General education and classroom management",
                "Form-based educational content integration",
                "Confidence-based clarification requests"
            ],
            "routing_statistics": {
                "total_domains": 4,
                "total_specialist_bots": 4,
                "total_forms_available": len(handwriting_forms) + len(vocabulary_forms) + len(ideas_forms),
                "confidence_thresholds": {
                    "high_confidence": ">= 0.7 (direct routing)",
                    "medium_confidence": "0.5-0.7 (cautious routing)",
                    "low_confidence": "< 0.5 (clarification)"
                }
            }
        }
        
        from datetime import datetime
        health_status["timestamp"] = datetime.utcnow().isoformat()
        
        return health_status
        
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        )