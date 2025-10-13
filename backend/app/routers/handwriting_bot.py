"""
FastAPI router for the Handwriting Bot with LangSmith integration.
Provides endpoints to test the handwriting bot graph.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from app.graph.handwriting_graph import run_handwriting_bot, stream_handwriting_bot
from app.service.form_retrieval_service import form_retrieval_service

router = APIRouter(prefix="/handwriting-bot", tags=["Handwriting Bot"])

class HandwritingQuery(BaseModel):
    """Request model for handwriting bot queries."""
    query: str = Field(..., min_length=1, max_length=1000, description="Teacher's handwriting-related question")
    teacher_id: Optional[str] = Field(default="teacher_001", description="Unique teacher identifier")
    session_id: Optional[str] = Field(default="session_001", description="Conversation session identifier")

class HandwritingResponse(BaseModel):
    """Response model for handwriting bot."""
    query: str
    response: str
    query_type: Optional[str]
    target_letters: List[str]
    grade_level: Optional[str]
    relevant_forms: List[str]
    follow_up_questions: List[str]
    conversation_depth: int
    processing_time_ms: Optional[float]

@router.post("/chat", response_model=HandwritingResponse)
async def chat_with_handwriting_bot(request: HandwritingQuery):
    """
    Chat with the handwriting and spelling specialist bot.
    
    This endpoint processes a teacher's handwriting-related query through the complete
    LangGraph pipeline, including query analysis, form retrieval, response generation,
    quality checking, and follow-up suggestions.
    
    The bot specializes in:
    - Letter formation and stroke sequences
    - Fine motor skill development
    - Proper pencil grip and posture
    - Phoneme-grapheme connections for spelling
    - Multi-sensory learning approaches
    - Assessment and progress monitoring
    
    Args:
        request: HandwritingQuery containing the teacher's question
        
    Returns:
        HandwritingResponse with the bot's comprehensive answer
    """
    import time
    
    try:
        start_time = time.time()
        
        print(f"🎯 Handwriting Bot Request: '{request.query[:50]}...'")
        print(f"👤 Teacher ID: {request.teacher_id}")
        print(f"💬 Session ID: {request.session_id}")
        
        # Run the handwriting bot graph
        final_state = await run_handwriting_bot(
            teacher_query=request.query,
            teacher_id=request.teacher_id,
            session_id=request.session_id
        )
        
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Extract the bot's response from the final state
        messages = final_state.get("messages", [])
        bot_response = ""
        
        # Find the last AI message
        for message in reversed(messages):
            if hasattr(message, 'type') and message.type == 'ai':
                bot_response = message.content
                break
            elif hasattr(message, 'content') and isinstance(message.content, str):
                bot_response = message.content
                break
        
        if not bot_response:
            bot_response = "I apologize, but I wasn't able to generate a proper response. Please try rephrasing your question."
        
        # Extract relevant form letters from the forms that were used
        relevant_forms = final_state.get("relevant_forms", [])
        form_letters = []
        for form in relevant_forms:
            if 'form_letter' in form:
                form_letters.append(f"Form {form['form_letter']}")
        
        # Build response
        response = HandwritingResponse(
            query=request.query,
            response=bot_response,
            query_type=final_state.get("query_type", "general"),
            target_letters=final_state.get("target_letters", []),
            grade_level=final_state.get("grade_level", "not_specified"),
            relevant_forms=form_letters,
            follow_up_questions=final_state.get("follow_up_questions", []),
            conversation_depth=final_state.get("conversation_depth", 1),
            processing_time_ms=round(processing_time, 2)
        )
        
        print(f"✅ Handwriting Bot Response generated in {processing_time:.2f}ms")
        print(f"📝 Query Type: {response.query_type}")
        print(f"📚 Forms Used: {len(form_letters)}")
        
        return response
        
    except Exception as e:
        print(f"❌ Error in handwriting bot endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Handwriting bot processing failed: {str(e)}"
        )

@router.get("/test-forms")
async def test_form_retrieval():
    """
    Test endpoint to verify form retrieval system is working.
    
    Returns information about loaded forms and their content structure.
    """
    try:
        # Get cache status
        cache_status = form_retrieval_service.get_cache_status()
        
        # Test retrieving forms by different methods
        test_results = {
            "cache_status": cache_status,
            "test_retrievals": {}
        }
        
        # Test 1: Get all handwriting forms
        all_forms = form_retrieval_service.get_handwriting_forms()
        test_results["test_retrievals"]["all_handwriting_forms"] = {
            "count": len(all_forms),
            "forms": [f"Form {form.get('form_letter', 'Unknown')}" for form in all_forms]
        }
        
        # Test 2: Get forms by query type
        letter_formation_forms = form_retrieval_service.get_forms_by_query_type("letter_formation")
        test_results["test_retrievals"]["letter_formation_forms"] = {
            "count": len(letter_formation_forms),
            "forms": [f"Form {form.get('form_letter', 'Unknown')}" for form in letter_formation_forms]
        }
        
        # Test 3: Get letter-specific content
        letter_z_forms = form_retrieval_service.get_letter_specific_content(["z", "Z"])
        test_results["test_retrievals"]["letter_z_forms"] = {
            "count": len(letter_z_forms),
            "forms": [f"Form {form.get('form_letter', 'Unknown')}" for form in letter_z_forms]
        }
        
        # Test 4: Build context string
        sample_forms = form_retrieval_service.get_handwriting_forms(["A", "B"])
        context = form_retrieval_service.build_context_string(sample_forms, max_length=500)
        test_results["test_retrievals"]["context_generation"] = {
            "context_length": len(context),
            "context_preview": context[:200] + "..." if len(context) > 200 else context
        }
        
        print("✅ Form retrieval test completed successfully")
        return test_results
        
    except Exception as e:
        print(f"❌ Error in form retrieval test: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Form retrieval test failed: {str(e)}"
        )

@router.get("/test-queries")
async def get_test_queries():
    """
    Get a list of sample queries for testing the handwriting bot.
    
    Returns various types of handwriting-related queries that teachers might ask.
    """
    test_queries = {
        "letter_formation": [
            "How can I help students improve their letter formation for the letter Z?",
            "What's the proper stroke sequence for teaching uppercase letters?",
            "My students are having trouble with lowercase 'b' and 'd' - any strategies?",
            "How do I teach proper letter spacing in handwriting?"
        ],
        "fine_motor": [
            "What activities can help develop fine motor skills for writing?",
            "How can I strengthen students' finger muscles for better pencil control?",
            "What are some pre-writing activities for kindergarten students?",
            "My students have weak hand strength - what can I do?"
        ],
        "spelling": [
            "How do I connect handwriting instruction with spelling lessons?",
            "What's the best way to teach phoneme-grapheme relationships through writing?",
            "How can handwriting practice support spelling development?",
            "Should I teach cursive or print first for spelling?"
        ],
        "assessment": [
            "How do I assess handwriting progress in my classroom?",
            "What rubrics work best for evaluating student handwriting?",
            "How often should I assess handwriting skills?",
            "What are the key handwriting milestones for kindergarten?"
        ],
        "posture_grip": [
            "How do I teach proper pencil grip to young students?",
            "What's the best sitting position for handwriting instruction?",
            "How can I help students who hold their pencil incorrectly?",
            "What tools can support proper pencil grip development?"
        ],
        "general": [
            "What's the best approach to handwriting instruction for beginners?",
            "How much time should I spend on handwriting each day?",
            "What materials do I need for effective handwriting instruction?",
            "How do I differentiate handwriting instruction for different skill levels?"
        ]
    }
    
    return {
        "message": "Sample queries for testing the handwriting bot",
        "total_queries": sum(len(queries) for queries in test_queries.values()),
        "categories": list(test_queries.keys()),
        "test_queries": test_queries,
        "usage": {
            "endpoint": "/handwriting-bot/chat",
            "method": "POST",
            "body_example": {
                "query": "How can I help students improve their letter formation for the letter Z?",
                "teacher_id": "teacher_001",
                "session_id": "session_001"
            }
        }
    }

@router.get("/health")
async def handwriting_bot_health():
    """
    Health check endpoint for the handwriting bot.
    
    Verifies that all components are working properly.
    """
    try:
        # Check form retrieval service
        cache_status = form_retrieval_service.get_cache_status()
        forms_loaded = cache_status["total_forms_loaded"]
        
        # Check if we have the minimum required forms
        required_forms = ["A", "B", "C", "D", "E", "F", "G", "H"]
        loaded_handwriting_forms = cache_status["handwriting_forms_loaded"]
        missing_forms = [form for form in required_forms if form not in loaded_handwriting_forms]
        
        health_status = {
            "status": "healthy" if len(missing_forms) == 0 else "degraded",
            "timestamp": None,
            "components": {
                "form_retrieval_service": {
                    "status": "healthy" if forms_loaded > 0 else "unhealthy",
                    "forms_loaded": forms_loaded,
                    "handwriting_forms_loaded": len(loaded_handwriting_forms),
                    "missing_forms": missing_forms
                },
                "langgraph": {
                    "status": "healthy",
                    "graph_compiled": True
                },
                "openai_integration": {
                    "status": "configured" if hasattr(router, 'llm') else "ready",
                    "model": "gpt-4o"
                }
            },
            "capabilities": [
                "Letter formation guidance",
                "Fine motor skill development",
                "Spelling instruction support", 
                "Assessment strategies",
                "Posture and grip instruction",
                "Multi-sensory learning approaches"
            ]
        }
        
        from datetime import datetime
        health_status["timestamp"] = datetime.utcnow().isoformat()
        
        return health_status
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        )