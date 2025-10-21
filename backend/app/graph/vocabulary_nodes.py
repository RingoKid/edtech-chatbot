"""
LangGraph nodes for the Vocabulary and Sentence Structure Bot.
Each node performs a specific function in the conversation flow.
"""
import re
import json
from typing import Dict, List, Any, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from app.config import settings
from app.graph.vocabulary_state import VocabularyState
from app.service.form_retrieval_service import form_retrieval_service

class VocabularyNodes:
    """Container for all vocabulary bot graph nodes."""

    def __init__(self):
        """Initialize the vocabulary nodes with OpenAI model."""
        # Allow dummy API key for development
        api_key = settings.openai_api_key.get_secret_value() if settings.openai_api_key else "dummy-key"

        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.7,
            api_key=api_key
        )

        # Define target forms for vocabulary instruction
        self.target_forms = ["I", "J", "K", "L"]

        print("VocabularyNodes initialized with GPT-4 Omni")

    async def analyze_query_node(self, state: VocabularyState) -> Dict[str, Any]:
        """
        Node 1: Analyze the teacher's query to understand intent and extract key information.

        Args:
            state: Current vocabulary bot state

        Returns:
            Updated state with query analysis results
        """
        try:
            # Get the latest message from the teacher
            latest_message = state["messages"][-1]
            if hasattr(latest_message, 'content'):
                query = latest_message.content
            else:
                query = str(latest_message)

            # Use LLM to analyze the query
            analysis_prompt = f"""
            You are an expert in vocabulary and sentence structure education. Analyze this teacher's query and extract key information.

            Teacher's Query: "{query}"

            Analyze and respond with a JSON object containing:
            {{
                "query_type": "sentence_structure|vocabulary_building|grammar|genre_writing|general",
                "target_vocabulary": ["list", "of", "specific", "vocabulary", "words"],
                "target_genre": "narrative|informational|opinion|personal_narrative|not_specified",
                "grade_level": "prek|kindergarten|1st_grade|mixed|not_specified",
                "key_concepts": ["list", "of", "main", "concepts"],
                "urgency_level": "low|medium|high"
            }}

            Query Type Definitions:
            - sentence_structure: Questions about sentence patterns, subject-verb agreement, sentence frames
            - vocabulary_building: Questions about teaching new words, word meanings, vocabulary strategies
            - grammar: Questions about parts of speech, verb types, sentence components
            - genre_writing: Questions about vocabulary for specific genres (narrative, informational, opinion)
            - general: Broad questions about vocabulary/reading instruction
            """

            response = await self.llm.ainvoke([
                SystemMessage(content="You are an educational query analyzer. Respond only with valid JSON."),
                HumanMessage(content=analysis_prompt)
            ])

            # Parse the analysis result
            analysis_result = self._parse_json_response(response.content)

            return {
                "original_query": query,
                "query_type": analysis_result.get("query_type", "general"),
                "target_vocabulary": analysis_result.get("target_vocabulary", []),
                "target_genre": analysis_result.get("target_genre", "not_specified"),
                "grade_level": analysis_result.get("grade_level", "not_specified"),
                "retry_count": 0,
                "conversation_depth": state.get("conversation_depth", 0) + 1
            }

        except Exception as e:
            print(f"❌ Error in analyze_query_node: {str(e)}")
            return {
                "original_query": query if 'query' in locals() else "Unknown query",
                "query_type": "general",
                "target_vocabulary": [],
                "target_genre": "not_specified",
                "grade_level": "not_specified",
                "last_error": f"Query analysis failed: {str(e)}",
                "retry_count": state.get("retry_count", 0) + 1
            }

    async def retrieve_forms_node(self, state: VocabularyState) -> Dict[str, Any]:
        """
        Node 2: Retrieve relevant educational forms based on query analysis.

        Args:
            state: Current vocabulary bot state

        Returns:
            Updated state with retrieved forms and context
        """
        try:
            query_type = state.get("query_type", "general")
            target_vocabulary = state.get("target_vocabulary", [])
            target_genre = state.get("target_genre", "not_specified")

            # Retrieve vocabulary forms (I-L)
            relevant_forms = await form_retrieval_service.get_vocabulary_forms()

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
                if 'language_standards' in standards_data:
                    standards_summary += "Language Standards:\n"
                    for standard in standards_data['language_standards'][:3]:
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
                "form_context": "Error retrieving educational forms. Using general vocabulary knowledge.",
                "last_error": f"Form retrieval failed: {str(e)}",
                "retry_count": state.get("retry_count", 0) + 1
            }

    async def generate_response_node(self, state: VocabularyState) -> Dict[str, Any]:
        """
        Node 3: Generate a comprehensive response using the retrieved forms and query analysis.

        Args:
            state: Current vocabulary bot state

        Returns:
            Updated state with generated response
        """
        try:
            original_query = state.get("original_query", "")
            query_type = state.get("query_type", "general")
            target_vocabulary = state.get("target_vocabulary", [])
            target_genre = state.get("target_genre", "not_specified")
            grade_level = state.get("grade_level", "not_specified")
            form_context = state.get("form_context", "")
            conversation_depth = state.get("conversation_depth", 0)

            # Check if this is a lesson plan request with missing context
            is_lesson_request = any(phrase in original_query.lower() for phrase in [
                "teach", "lesson", "how do i", "help me", "create", "generate", "plan for"
            ])

            needs_context = (
                is_lesson_request and
                conversation_depth <= 1 and
                grade_level == "not_specified"
            )

            # If we need more context, ask clarifying questions instead
            if needs_context and (target_vocabulary or target_genre != "not_specified"):
                vocab_str = ", ".join(target_vocabulary) if target_vocabulary else "vocabulary and sentence structure"
                clarification_message = f"""Great! I can definitely help you teach {vocab_str}.

To create the most helpful lesson plan for you, could you let me know:

1️⃣ **What grade level is this lesson for?**
   • Pre-K
   • Kindergarten
   • 1st Grade

2️⃣ **What genre or writing type are you focusing on?**
   • Narrative writing (stories)
   • Informational writing (facts/explanations)
   • Opinion writing (preferences/arguments)
   • Personal narrative

3️⃣ **Are there specific objectives you'd like to address?**
   • Building complete sentences
   • Using action verbs or be-verbs
   • Expanding vocabulary
   • Sentence patterns for a specific genre

Once I know these details, I'll create a complete, scripted lesson plan tailored to your students! 📚"""

                ai_response = AIMessage(content=clarification_message)
                return {
                    "messages": [ai_response],
                    "response_generated": True,
                    "needs_clarification": True,
                    "retry_count": 0
                }

            # Build comprehensive system prompt
            system_prompt = f"""
            You are an expert in vocabulary and sentence structure instruction for early childhood education.

            **YOUR EXPERTISE: Vocabulary & Sentence Structure Instruction**

            You generate COMPLETE, SCRIPTED LESSON PLANS in this exact structure:

            **LESSON PLAN STRUCTURE:**

            **A. Standards**
            - Reference appropriate Pre-K/Kindergarten standards from the provided forms
            - Example: "ELAGSEKL1f: Produce and expand complete sentences in shared language activities"

            **B. Objectives**
            - Derive specific, measurable objectives from lesson content
            - Example: "Students will use action verbs to build complete sentences about animals"
            - Example: "Students will identify and use subject-verb patterns in narrative writing"

            **C. Materials**
            - List everything needed with bullet points
            - Example: "Vocabulary cards, sentence frames, writing paper, word wall, picture cards"

            **D. Scripted Lesson Plan for Vocabulary & Sentence Structure**

            **1. Review & Connect**

            [The purpose of this part of the lesson is to review previously learned vocabulary or sentence patterns and connect to the current writing unit/genre.]

            Teacher Script:

            Provide complete dialogue with {{actions}} and (expected responses)

            ---

            **2. Model, Explain & Engage**

            [The purpose of this part of the lesson is to introduce new vocabulary words and model how to use them in sentences aligned with the writing genre.]

            Teacher Script:

            Include vocabulary word introduction with definitions and visual support
            Include sentence structure modeling (subject-verb patterns, be-verbs, action verbs)
            Include genre-specific sentence examples (narrative, informational, opinion)
            Include think-aloud demonstrating vocabulary in sentences

            ---

            **3. Guided Practice**

            [The purpose is to give children practice building sentences using target vocabulary with teacher support.]

            Teacher Script:

            Include sentence building activities (Sentence Scramble, Fill-in-the-Blank, etc.)
            Include vocabulary practice in context
            Include collaborative sentence creation

            ---

            **4. Application**

            [The purpose of this part of the lesson is to facilitate children's independent use of vocabulary in genre-specific sentence writing.]

            Teacher Script:

            Include independent sentence writing using target vocabulary
            Include genre-specific writing application
            Include partner sharing and feedback

            ---

            **5. Wrap-Up**

            [The purpose of this part of the lesson is to review target vocabulary and sentence patterns and celebrate student work.]

            Teacher Script:

            Review target vocabulary and sentence patterns
            Share student examples
            Connect to ongoing writing unit

            **KEY PRINCIPLES:**
            - Connect vocabulary to specific writing genres (narrative, informational, opinion)
            - Teach sentence structures: subject-verb patterns, be-verbs, action verbs
            - Use unit themes and topics for vocabulary selection
            - Model sentence building explicitly before practice
            - Provide sentence frames for differentiation
            - Link to ongoing writing projects and genres

            **CRITICAL OUTPUT REQUIREMENTS:**
            ✅ Be a complete, rehearsal-ready lesson plan
            ✅ Include ALL 5 subsections with detailed scripts
            ✅ MUST include the bracketed [Explanation] at the start of EVERY section (1-5)
            ✅ MUST include full "Teacher Script:" with complete dialogue for every section
            ✅ Use clean formatting: [explanations], plain Teacher Script sections, (responses), {{actions}}
            ✅ DO NOT use hashtags (#), plus signs (+Level), asterisks (*Adaptation), or double hashtags (##) in user-facing output
            ✅ Include specific sentence-building activities
            ✅ Connect to specific writing genre when relevant
            ✅ Be 20-25 minutes total lesson time
            ✅ NEVER mention "Forms I-L", "Form K", "Form J" or any form letters/numbers to users
            ✅ Present all content as if you are the expert, not referencing external forms

            **MANDATORY STRUCTURE FOR EACH SECTION:**
            Each of the 5 sections MUST have:
            1. Section heading (e.g., "**1. Review & Connect**")
            2. Bracketed explanation (e.g., "[The purpose of this part of the lesson is to...]")
            3. "Teacher Script:" heading
            4. Complete, detailed dialogue with {{actions}} and (expected responses)
            """

            # Build conversation context if this is a follow-up
            conversation_context = ""
            all_messages = state.get("messages", [])
            if len(all_messages) > 1:
                previous_exchanges = []
                for msg in all_messages[:-1]:
                    if hasattr(msg, 'content'):
                        role = "Teacher" if hasattr(msg, 'type') and msg.type == 'human' else "Assistant"
                        previous_exchanges.append(f"{role}: {msg.content}")

                if previous_exchanges:
                    recent_context = previous_exchanges[-6:]
                    conversation_context = f"""
            CONVERSATION HISTORY (previous exchanges):
            {chr(10).join(recent_context)}

            ---
            """

            # Build specific response prompt based on query analysis
            response_prompt = f"""
            {conversation_context}CURRENT TEACHER REQUEST: "{original_query}"

            QUERY ANALYSIS:
            - Type: {query_type}
            - Target Vocabulary: {', '.join(target_vocabulary) if target_vocabulary else 'None specified'}
            - Genre: {target_genre}
            - Grade Level: {grade_level}

            RELEVANT EDUCATIONAL FORMS CONTENT:
            {form_context}

            **IMPORTANT**: Use the conversation history above to understand the full context of the teacher's request. If they're following up on a previous question, continue that discussion naturally.

            **DETERMINE YOUR RESPONSE TYPE:**

            IF the teacher asks for:
            - "Create a lesson plan"
            - "Generate a lesson"
            - "Help me teach [specific vocabulary/sentences]"
            - "I need a vocabulary lesson for..."
            - "give me a lesson plan" (follow-up)

            → THEN generate a **COMPLETE SCRIPTED LESSON PLAN** using the structure in your system prompt.

            IF the teacher asks for:
            - "How do I..." questions
            - "What are some strategies for..." questions
            - "Can you explain..." questions
            - General guidance or tips

            → THEN provide **TARGETED GUIDANCE** with:
            1. **Direct Answer** to their question
            2. **2-3 Specific Activities** from Form K with materials and steps
            3. **Differentiation** for beginning/developing/fluent writers
            4. **Genre Connection** (narrative, informational, opinion writing)
            5. **Sentence Building Strategies**

            Always use the exact content from the provided forms. Reference Form I for structure, Form J for templates, Form K for activities, and Form L for modifications.

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
            However, I can still help with your vocabulary question: "{original_query}"

            Here are some general vocabulary and sentence structure strategies you can try:

            **For Vocabulary Building:**
            - Use visual supports (pictures, objects, gestures)
            - Introduce words in meaningful contexts
            - Practice new words through games and activities
            - Connect vocabulary to students' experiences

            **For Sentence Structure:**
            - Model complete sentences explicitly
            - Use sentence frames for support
            - Practice subject-verb patterns
            - Connect sentences to genre-specific writing

            **Materials to Try:**
            - Vocabulary cards with pictures
            - Sentence strips and word cards
            - Graphic organizers for sentence building
            - Genre-specific writing frames

            Would you like me to elaborate on any of these strategies, or do you have a more specific aspect of vocabulary instruction you'd like to explore?
            """)

            return {
                "messages": [fallback_response],
                "response_generated": True,
                "last_error": f"Response generation failed: {str(e)}",
                "retry_count": state.get("retry_count", 0) + 1
            }

    async def quality_check_node(self, state: VocabularyState) -> Dict[str, Any]:
        """
        Node 4: Check the quality of the generated response and suggest improvements.

        Args:
            state: Current vocabulary bot state

        Returns:
            Updated state with quality check results
        """
        try:
            # Get the generated response
            messages = state.get("messages", [])
            if not messages:
                return {"response_quality_check": False, "last_error": "No response to check"}

            latest_response = messages[-1].content
            original_query = state.get("original_query", "")
            query_type = state.get("query_type", "general")

            # Use LLM to evaluate response quality
            quality_check_prompt = f"""
            Evaluate this vocabulary instruction response for a teacher's question.

            Original Question: "{original_query}"
            Query Type: {query_type}

            Generated Response: "{latest_response}"

            Rate the response quality and respond with JSON:
            {{
                "overall_quality": "excellent|good|fair|poor",
                "has_specific_activities": true/false,
                "addresses_original_question": true/false,
                "includes_materials": true/false,
                "provides_differentiation": true/false,
                "actionable_for_teachers": true/false,
                "genre_connection": true/false,
                "improvement_suggestions": ["list", "of", "specific", "improvements"],
                "quality_score": 1-10
            }}

            A quality response should:
            - Directly answer the teacher's question
            - Include specific, actionable activities
            - List required materials
            - Provide differentiation strategies
            - Connect to genre-specific writing when relevant
            - Be immediately implementable in a classroom
            """

            quality_response = await self.llm.ainvoke([
                SystemMessage(content="You are an educational content quality evaluator. Respond only with valid JSON."),
                HumanMessage(content=quality_check_prompt)
            ])

            quality_result = self._parse_json_response(quality_response.content)
            quality_score = quality_result.get("quality_score", 7)

            print(f"✅ Quality check completed. Score: {quality_score}/10")

            return {
                "response_quality_check": True,
                "quality_score": quality_score,
                "needs_improvement": quality_score < 7,
                "retry_count": 0
            }

        except Exception as e:
            print(f"❌ Error in quality_check_node: {str(e)}")
            return {
                "response_quality_check": True,
                "quality_score": 7,
                "needs_improvement": False,
                "last_error": f"Quality check failed: {str(e)}",
                "retry_count": state.get("retry_count", 0) + 1
            }

    async def follow_up_node(self, state: VocabularyState) -> Dict[str, Any]:
        """
        Node 5: Generate follow-up questions or suggestions for continued learning.

        Args:
            state: Current vocabulary bot state

        Returns:
            Updated state with follow-up suggestions
        """
        try:
            query_type = state.get("query_type", "general")
            target_vocabulary = state.get("target_vocabulary", [])
            target_genre = state.get("target_genre", "not_specified")

            # Generate contextual follow-up questions
            follow_up_suggestions = []

            if query_type == "sentence_structure":
                follow_up_suggestions = [
                    "Would you like sentence frames for different genres?",
                    "Are you interested in subject-verb agreement activities?",
                    "Would assessment strategies for sentence writing be helpful?"
                ]
            elif query_type == "vocabulary_building":
                follow_up_suggestions = [
                    "Would you like vocabulary games for practice?",
                    "Are you interested in multi-sensory vocabulary strategies?",
                    "Would word study activities be helpful for your students?"
                ]
            elif query_type == "genre_writing":
                follow_up_suggestions = [
                    "Would you like genre-specific vocabulary lists?",
                    "Are you interested in sentence patterns for this genre?",
                    "Would graphic organizers for this genre be helpful?"
                ]
            else:
                follow_up_suggestions = [
                    "Would you like more specific activities for any particular area?",
                    "Are there specific vocabulary words or sentence patterns you'd like to focus on?",
                    "Would assessment strategies be helpful for tracking vocabulary growth?"
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
                "follow_up_questions": ["Is there anything specific about vocabulary instruction you'd like to explore further?"],
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
                "target_vocabulary": [],
                "target_genre": "not_specified",
                "grade_level": "not_specified",
                "key_concepts": [],
                "urgency_level": "medium"
            }

# Global instance for use in the graph
vocabulary_nodes = VocabularyNodes()