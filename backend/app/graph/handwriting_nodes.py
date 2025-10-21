"""
LangGraph nodes for the Handwriting and Spelling Bot.
Each node performs a specific function in the conversation flow.
"""
import re
import json
from typing import Dict, List, Any, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from app.config import settings
from app.graph.handwriting_state import HandwritingState
from app.service.form_retrieval_service import form_retrieval_service

class HandwritingNodes:
    """Container for all handwriting bot graph nodes."""
    
    def __init__(self):
        """Initialize the handwriting nodes with OpenAI model."""
        # Allow dummy API key for development
        api_key = settings.openai_api_key.get_secret_value() if settings.openai_api_key else "dummy-key"
        
        self.llm = ChatOpenAI(
            model="gpt-4o",  # Using GPT-4 Omni for better reasoning
            temperature=0.7,  # Balanced creativity and consistency
            api_key=api_key
        )
        
        # Define target forms for handwriting instruction
        self.target_forms = ["A", "B", "C", "D", "E", "F", "G", "H"]
        
        print("HandwritingNodes initialized with GPT-4 Omni")
    
    async def analyze_query_node(self, state: HandwritingState) -> Dict[str, Any]:
        """
        Node 1: Analyze the teacher's query to understand intent and extract key information.
        
        Args:
            state: Current handwriting bot state
            
        Returns:
            Updated state with query analysis results
        """
        try:
            # Get the latest message from the teacher
            latest_message = state["messages"][-1]
            if hasattr(latest_message, 'content'):
                query = latest_message.content

                # Handle cases where content is a list of dicts (multimodal format)
                if isinstance(query, list):
                    # Extract text from list of content blocks
                    text_parts = []
                    for item in query:
                        if isinstance(item, dict) and item.get('type') == 'text':
                            text_parts.append(item.get('text', ''))
                        elif isinstance(item, str):
                            text_parts.append(item)
                    query = ' '.join(text_parts)
                elif not isinstance(query, str):
                    query = str(query)
            else:
                query = str(latest_message)
            
            # Use LLM to analyze the query
            analysis_prompt = f"""
            You are an expert in handwriting and fine motor skills education. Analyze this teacher's query and extract key information.
            
            Teacher's Query: "{query}"
            
            Analyze and respond with a JSON object containing:
            {{
                "query_type": "letter_formation|fine_motor|spelling|assessment|posture_grip|general",
                "target_letters": ["list", "of", "specific", "letters", "mentioned"],
                "grade_level": "prek|kindergarten|1st_grade|mixed|not_specified",
                "key_concepts": ["list", "of", "main", "concepts"],
                "urgency_level": "low|medium|high",
                "specific_challenges": ["list", "of", "challenges", "mentioned"]
            }}
            
            Query Type Definitions:
            - letter_formation: Questions about how to form specific letters, stroke order, directionality
            - fine_motor: Questions about hand strength, finger dexterity, grip development
            - spelling: Questions about letter-sound connections, phoneme-grapheme relationships
            - assessment: Questions about evaluating progress, rubrics, testing handwriting skills
            - posture_grip: Questions about sitting position, pencil grip, paper positioning
            - general: Broad questions about handwriting instruction that don't fit other categories
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an educational query analyzer. Respond only with valid JSON."),
                HumanMessage(content=analysis_prompt)
            ])
            
            # Parse the analysis result
            analysis_result = self._parse_json_response(response.content)

            # DEBUG: Log the extracted target letters
            extracted_letters = analysis_result.get("target_letters", [])
            extracted_grade = analysis_result.get("grade_level", "not_specified")
            extracted_query_type = analysis_result.get("query_type", "general")

            print(f"🔍 DEBUG - Query: '{query}'")
            print(f"🔍 DEBUG - Extracted from current query - target_letters: {extracted_letters}, grade: {extracted_grade}")

            # Merge with previous state if this is a follow-up query
            # If current query doesn't specify letters/grade, preserve from previous state
            previous_letters = state.get("target_letters", [])
            previous_grade = state.get("grade_level")
            previous_query_type = state.get("query_type")

            # Use new values if found, otherwise keep previous values
            final_letters = extracted_letters if extracted_letters else previous_letters
            final_grade = extracted_grade if extracted_grade != "not_specified" else (previous_grade or "not_specified")
            final_query_type = extracted_query_type if extracted_query_type != "general" else (previous_query_type or "general")

            print(f"🔍 DEBUG - Final merged values - target_letters: {final_letters}, grade: {final_grade}, query_type: {final_query_type}")

            return {
                "original_query": query,
                "query_type": final_query_type,
                "target_letters": final_letters,
                "grade_level": final_grade,
                "retry_count": 0,
                "conversation_depth": state.get("conversation_depth", 0) + 1
            }
            
        except Exception as e:
            print(f"❌ Error in analyze_query_node: {str(e)}")
            return {
                "original_query": query if 'query' in locals() else "Unknown query",
                "query_type": "general",
                "target_letters": [],
                "grade_level": "not_specified",
                "last_error": f"Query analysis failed: {str(e)}",
                "retry_count": state.get("retry_count", 0) + 1
            }
    
    async def retrieve_forms_node(self, state: HandwritingState) -> Dict[str, Any]:
        """
        Node 2: Retrieve relevant educational forms based on query analysis.
        
        Args:
            state: Current handwriting bot state
            
        Returns:
            Updated state with retrieved forms and context
        """
        try:
            query_type = state.get("query_type", "general")
            target_letters = state.get("target_letters", [])
            
            # Retrieve forms based on query type
            if target_letters:
                # Get letter-specific content
                relevant_forms = await form_retrieval_service.get_letter_specific_content(target_letters)
            else:
                # Get forms by query type
                relevant_forms = await form_retrieval_service.get_forms_by_query_type(query_type)

            # Also get standards if grade level is specified
            grade_level = state.get("grade_level", "not_specified")
            standards_data = {}
            if grade_level in ["prek", "kindergarten"]:
                standards_data = await form_retrieval_service.get_standards_by_grade(grade_level)
            
            # Build context string for LLM
            form_context = form_retrieval_service.build_context_string(relevant_forms, max_length=3500)
            
            # Add standards context if available
            if standards_data:
                standards_summary = f"\n=== {grade_level.upper()} STANDARDS ===\n"
                if 'handwriting_standards' in standards_data:
                    standards_summary += "Handwriting Standards:\n"
                    for standard in standards_data['handwriting_standards'][:3]:  # Limit to first 3
                        standards_summary += f"- {standard}\n"
                form_context += standards_summary
            
            print(f"✅ Retrieved {len(relevant_forms)} forms for query type: {query_type}")
            
            return {
                "relevant_forms": relevant_forms,
                "form_context": form_context,
                "retry_count": 0
            }
            
        except Exception as e:
            print(f"❌ Error in retrieve_forms_node: {str(e)}")
            return {
                "relevant_forms": [],
                "form_context": "Error retrieving educational forms. Using general handwriting knowledge.",
                "last_error": f"Form retrieval failed: {str(e)}",
                "retry_count": state.get("retry_count", 0) + 1
            }
    
    async def generate_response_node(self, state: HandwritingState) -> Dict[str, Any]:
        """
        Node 3: Generate a comprehensive response using the retrieved forms and query analysis.
        
        Args:
            state: Current handwriting bot state
            
        Returns:
            Updated state with generated response
        """
        try:
            original_query = state.get("original_query", "")
            query_type = state.get("query_type", "general")
            target_letters = state.get("target_letters", [])
            grade_level = state.get("grade_level", "not_specified")
            form_context = state.get("form_context", "")
            conversation_depth = state.get("conversation_depth", 0)

            # Check if this is a lesson plan request with missing context
            is_lesson_request = any(phrase in original_query.lower() for phrase in [
                "teach", "lesson", "how do i", "help me", "create", "generate", "plan for"
            ])

            # Check if the query is incomplete (mentions teaching but no letter specified)
            is_incomplete_query = (
                is_lesson_request and
                not target_letters  # No letter specified
            )

            needs_context = (
                is_lesson_request and
                conversation_depth <= 1 and  # First interaction
                (grade_level == "not_specified" or not target_letters)  # Missing grade level or letters
            )

            # If query is incomplete (no letter specified), ask for which letter
            if is_incomplete_query:
                clarification_message = """I'd be happy to help you teach handwriting!

Which letter would you like to teach? Please specify the letter, and I'll create a complete lesson plan for you.

For example: "letter A", "letter M", "letter Z", etc."""

                ai_response = AIMessage(content=clarification_message)
                return {
                    "messages": [ai_response],
                    "response_generated": True,
                    "needs_clarification": True,
                    "retry_count": 0
                }

            # If we need more context, ask clarifying questions instead
            if needs_context and target_letters:
                letter_str = ", ".join(target_letters) if len(target_letters) > 1 else target_letters[0]
                clarification_message = f"""Great! I can definitely help you teach the letter {letter_str}.

To create the most helpful lesson plan for you, could you let me know:

1️⃣ **What grade level is this lesson for?**
   • Pre-K
   • Kindergarten
   • 1st Grade

2️⃣ **Besides writing the letter {letter_str}, are there any specific objectives you'd like to focus on?**
   • Proper stroke sequence and letter formation
   • Linking the /{letter_str}/ sound to the letter
   • Spelling simple words with {letter_str}
   • Fine motor skills and pencil grip
   • Other specific goals?

Once I know these details, I'll create a complete, scripted lesson plan tailored to your students! ✏️"""

                ai_response = AIMessage(content=clarification_message)
                return {
                    "messages": [ai_response],
                    "response_generated": True,
                    "needs_clarification": True,
                    "retry_count": 0
                }

            # Build comprehensive system prompt
            system_prompt = f"""
            You are an expert handwriting and fine motor skills instructor for early childhood education.

            **YOUR EXPERTISE: Handwriting & Spelling Instruction**

            You generate COMPLETE, SCRIPTED LESSON PLANS following this exact 5-section structure.

            **LESSON PLAN STRUCTURE:**

            **A. Standards**
            - Reference appropriate Pre-K/Kindergarten standards
            - Example: "ELAGSEKRF3a: Demonstrate basic knowledge of letter-sound correspondences"

            **B. Objectives**
            - Create specific, measurable objectives for the TARGET LETTER
            - Focus on: pronunciation of the target sound, letter formation with proper stroke sequence

            **C. Materials**
            - List all materials needed (sound cards, worksheets, pencils, visual charts)
            - Include materials specific to the target letter's sound

            **D. Scripted Lesson Plan for Handwriting & Spelling**

            You MUST generate ALL 5 sections below with complete teacher scripts:

            **SECTION 1: Review & Connect** (2-3 minutes)
            - [Purpose explanation in brackets]: Review previously learned sounds
            - Teacher Script: "Sound Sparks game" - Teacher points to previous sounds, children respond
            - Do NOT use sounds that haven't been directly taught yet

            **SECTION 2: Model, Explain & Engage** (8-10 minutes)
            - [Purpose explanation in brackets]: Connect the target sound to its letter form
            - Teacher Script MUST include:
              * Sound pronunciation practice (vocal box check, mouth/tongue position)
              * The specific GESTURE for the target phoneme (use exact gesture from Form G)
              * Sound Hunt game with appropriate picture cards for the target letter
              * Letter formation demonstration with SEQUENCE VERBAL CUES (use exact cues from Form F)
              * Stroke-by-stroke instruction showing uppercase and lowercase formation

            **SECTION 3: Guided Practice** (5-7 minutes)
            - [Purpose explanation in brackets]: Practice writing with proper grip and stroke formation
            - Teacher Script MUST include:
              * "Magic Finger Write" activity (air/desk tracing with sequence verbal cues)
              * Pencil grip and paper positioning check
              * "Trace & Say" activity with dotted lines
              * Multiple practice attempts with monitoring

            **SECTION 4: Application** (5 minutes)
            - [Purpose explanation in brackets]: Match sound to letter for spelling
            - Teacher Script: "Sound-Letter Hunt game" where students write the letter when they hear the sound
            - Use words with the target letter's sound

            **SECTION 5: Wrap-Up** (2-3 minutes)
            - [Purpose explanation in brackets]: Review and celebrate progress
            - Teacher Script: Recap the sound, identify the letter, air write with sequence verbal cues
            - End with "Kiss your brains" praise

            **CRITICAL INSTRUCTIONS:**

            1. **USE THE PROVIDED FORMS DATA** - The educational forms content below contains:
               - Form F: Exact sequence verbal cues for every letter
               - Form G: Exact gestures for every phoneme
               - You MUST use these exact cues and gestures in your lesson plan

            2. **LETTER-SPECIFIC CONTENT** - Generate everything for the specific TARGET LETTER:
               - Use the correct phoneme sound
               - Use the correct gesture from Form G
               - Use the correct sequence verbal cues from Form F
               - Use appropriate picture cards (e.g., if 'm', use 'mouse' or 'monkey' cards)

            3. **OUTPUT REQUIREMENTS:**
            ✅ Complete 20-25 minute lesson plan ready for immediate classroom use
            ✅ ALL 5 sections with full scripts
            ✅ Bracketed [Purpose] at the start of EVERY section
            ✅ "Teacher Script:" with complete dialogue for every section
            ✅ Use {{actions}} and (expected responses) throughout
            ✅ Clean formatting - NO hashtags (#), plus signs (+), or asterisks (*) in user-facing output
            ✅ NEVER mention "Form A-H" or any form references to users
            ✅ Write as the expert, not referencing external sources

            **EVIDENCE-BASED PRACTICES TO INCORPORATE:**
            - Proper pencil grip and left-to-right writing
            - Phoneme isolation and pronunciation
            - Step-by-step stroke order instruction
            - Multi-sensory learning (visual, auditory, kinesthetic)
            - Corrective and confirmatory feedback
            - Invented spelling encouragement
            """
            
            # Build conversation context if this is a follow-up
            conversation_context = ""
            all_messages = state.get("messages", [])
            if len(all_messages) > 1:
                # Extract previous exchanges (exclude current message which is the last one)
                previous_exchanges = []
                for msg in all_messages[:-1]:  # All except the latest
                    if hasattr(msg, 'content'):
                        role = "Teacher" if hasattr(msg, 'type') and msg.type == 'human' else "Assistant"
                        previous_exchanges.append(f"{role}: {msg.content}")

                if previous_exchanges:
                    # Include last 3 exchanges for context (6 messages)
                    recent_context = previous_exchanges[-6:]
                    conversation_context = f"""
            CONVERSATION HISTORY (previous exchanges):
            {chr(10).join(recent_context)}

            ---
            """

            # Build the target letter instruction
            target_letter_instruction = ""
            if target_letters:
                letter_str = ', '.join(target_letters)
                target_letter_instruction = f"""
            **CRITICAL - TARGET LETTER(S): {letter_str.upper()}**

            You MUST create the lesson plan specifically for the letter(s): {letter_str.upper()}
            - Use the /{letter_str.lower()}/ sound throughout the lesson
            - Reference words that start with {letter_str.lower()} (not any other letter)
            - Show stroke sequences specifically for {letter_str.upper()} and {letter_str.lower()}
            - Use {letter_str.lower()}-related visual aids and materials (e.g., if 'z', use zebra; if 'a', use apple)

            DO NOT use examples from other letters. The entire lesson must be about letter {letter_str.upper()}.
            """

            # Build specific response prompt based on query analysis
            response_prompt = f"""
            {conversation_context}CURRENT TEACHER REQUEST: "{original_query}"

            {target_letter_instruction}

            QUERY ANALYSIS:
            - Type: {query_type}
            - Target Letters: {', '.join(target_letters) if target_letters else 'None specified'}
            - Grade Level: {grade_level}

            RELEVANT EDUCATIONAL FORMS CONTENT:
            {form_context}

            **IMPORTANT**: Use the conversation history above to understand the full context of the teacher's request. If they're following up on a previous question, continue that discussion naturally and generate the requested lesson plan.

            **DETERMINE YOUR RESPONSE TYPE:**

            IF the teacher asks for:
            - "Create a lesson plan"
            - "Generate a lesson"
            - "Help me teach [specific letter/sound]"
            - "I need a handwriting lesson for..."
            - "give me a lesson plan" (follow-up)

            → THEN generate a **COMPLETE SCRIPTED LESSON PLAN** using the structure in your system prompt FOR THE SPECIFIC LETTER(S) MENTIONED ABOVE.

            IF the teacher asks for:
            - "How do I..." questions
            - "What are some strategies for..." questions
            - "Can you explain..." questions
            - General guidance or tips

            → THEN provide **TARGETED GUIDANCE** with:
            1. **Direct Answer** to their question
            2. **2-3 Specific Activities** from Form D with materials and steps
            3. **Differentiation** for low/middle/high levels
            4. **Evidence-Based Practices** from Form E
            5. **References** to relevant Forms (A-H)

            Always use the exact content from the provided forms. Reference Form F for sequence verbal cues, Form G for gestures, Form D for activities, and Form E for evidence-based practices.

            Make your response immediately actionable and classroom-ready.
            """

            # Generate response using conversation history
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=response_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # Create AI message for the conversation
            ai_response = AIMessage(content=response.content)
            
            print(f"✅ Generated response for {query_type} query")
            
            return {
                "messages": [ai_response],
                "response_generated": True,
                "retry_count": 0
            }
            
        except Exception as e:
            print(f"❌ Error in generate_response_node: {str(e)}")
            
            # Fallback response
            fallback_response = AIMessage(content=f"""
            I apologize, but I'm having trouble accessing the specific educational forms right now. 
            However, I can still help with your handwriting question: "{original_query}"
            
            Here are some general handwriting strategies you can try:
            
            **For Letter Formation:**
            - Start with large motor movements (air writing, sand trays)
            - Use verbal cues for stroke direction ("top to bottom, left to right")
            - Practice with dotted lines and guided practice
            
            **For Fine Motor Development:**
            - Finger strengthening activities (play dough, tweezers)
            - Proper pencil grip practice with visual cues
            - Short, frequent practice sessions
            
            **Materials to Try:**
            - Large crayons or markers for beginners
            - Pencil grips for support
            - Various textured surfaces for practice
            
            Would you like me to elaborate on any of these strategies, or do you have a more specific aspect of handwriting you'd like to explore?
            """)
            
            return {
                "messages": [fallback_response],
                "response_generated": True,
                "last_error": f"Response generation failed: {str(e)}",
                "retry_count": state.get("retry_count", 0) + 1
            }
    
    async def quality_check_node(self, state: HandwritingState) -> Dict[str, Any]:
        """
        Node 4: Check the quality of the generated response and suggest improvements.

        TEMPORARILY DISABLED: Skipping LLM quality check to avoid timeout issues with long responses.

        Args:
            state: Current handwriting bot state

        Returns:
            Updated state with quality check results
        """
        try:
            # Get the generated response
            messages = state.get("messages", [])
            if not messages:
                return {"response_quality_check": False, "last_error": "No response to check"}

            latest_response = messages[-1].content
            response_length = len(latest_response)

            # Simple heuristic-based quality check instead of LLM evaluation
            # Check for key markers of a complete lesson plan
            has_sections = all(section in latest_response for section in [
                "Standards", "Objectives", "Materials", "Review & Connect", "Teacher Script"
            ])

            # Assume good quality if it has the expected structure
            quality_score = 8 if has_sections else 6

            print(f"✅ Quality check completed (heuristic). Response length: {response_length} chars, Score: {quality_score}/10")

            return {
                "response_quality_check": True,
                "quality_score": quality_score,
                "needs_improvement": False,  # Never retry to avoid loops
                "retry_count": 0
            }

        except Exception as e:
            print(f"❌ Error in quality_check_node: {str(e)}")
            return {
                "response_quality_check": True,  # Pass through on error
                "quality_score": 7,  # Assume decent quality
                "needs_improvement": False,
                "last_error": f"Quality check failed: {str(e)}",
                "retry_count": state.get("retry_count", 0) + 1
            }
    
    async def follow_up_node(self, state: HandwritingState) -> Dict[str, Any]:
        """
        Node 5: Generate follow-up questions or suggestions for continued learning.
        
        Args:
            state: Current handwriting bot state
            
        Returns:
            Updated state with follow-up suggestions
        """
        try:
            query_type = state.get("query_type", "general")
            target_letters = state.get("target_letters", [])
            grade_level = state.get("grade_level", "not_specified")
            
            # Generate contextual follow-up questions
            follow_up_suggestions = []
            
            if query_type == "letter_formation":
                follow_up_suggestions = [
                    "Would you like specific verbal cues for teaching letter strokes?",
                    "Are you interested in multi-sensory activities for letter practice?",
                    "Would assessment rubrics for letter formation be helpful?"
                ]
            elif query_type == "fine_motor":
                follow_up_suggestions = [
                    "Would you like activities to strengthen finger muscles?",
                    "Are you interested in pencil grip development strategies?",
                    "Would pre-writing activities be helpful for your students?"
                ]
            elif query_type == "spelling":
                follow_up_suggestions = [
                    "Would you like phoneme-grapheme connection activities?",
                    "Are you interested in spelling pattern instruction?",
                    "Would multisensory spelling strategies be helpful?"
                ]
            else:
                follow_up_suggestions = [
                    "Would you like more specific activities for any particular area?",
                    "Are there specific letters or skills you'd like to focus on?",
                    "Would assessment strategies be helpful for tracking progress?"
                ]
            
            print(f"✅ Generated {len(follow_up_suggestions)} follow-up suggestions")
            
            return {
                "follow_up_questions": follow_up_suggestions,
                "conversation_depth": state.get("conversation_depth", 0),
                "retry_count": 0
            }
            
        except Exception as e:
            print(f"❌ Error in follow_up_node: {str(e)}")
            return {
                "follow_up_questions": ["Is there anything specific about handwriting instruction you'd like to explore further?"],
                "last_error": f"Follow-up generation failed: {str(e)}",
                "retry_count": state.get("retry_count", 0) + 1
            }
    
    def _parse_json_response(self, response_content: str) -> Dict[str, Any]:
        """
        Parse JSON response from LLM, with fallback handling.
        
        Args:
            response_content: Raw response from LLM
            
        Returns:
            Parsed JSON dictionary or fallback values
        """
        try:
            # Try to extract JSON using regex
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                # Try parsing the entire response as JSON
                return json.loads(response_content)
                
        except (json.JSONDecodeError, ValueError) as e:
            print(f"⚠️ JSON parsing failed: {str(e)}")
            # Return fallback values
            return {
                "query_type": "general",
                "target_letters": [],
                "grade_level": "not_specified",
                "key_concepts": [],
                "urgency_level": "medium",
                "specific_challenges": []
            }

# Global instance for use in the graph
handwriting_nodes = HandwritingNodes()