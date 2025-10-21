"""
LangGraph nodes for the Ideas and Organization Bot.
Each node performs a specific function in the conversation flow.
"""
import re
import json
from typing import Dict, List, Any, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from app.config import settings
from app.graph.ideas_state import IdeasState
from app.service.form_retrieval_service import form_retrieval_service

class IdeasNodes:
    """Container for all ideas bot graph nodes."""

    def __init__(self):
        """Initialize the ideas nodes with OpenAI model."""
        # Allow dummy API key for development
        api_key = settings.openai_api_key.get_secret_value() if settings.openai_api_key else "dummy-key"

        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.8,  # Higher temperature for creativity
            api_key=api_key
        )

        # Define target forms for ideas instruction
        self.target_forms = ["M", "N", "O", "P", "Q"]

        print("IdeasNodes initialized with GPT-4 Omni")

    async def analyze_query_node(self, state: IdeasState) -> Dict[str, Any]:
        """
        Node 1: Analyze the teacher's query to understand intent and extract key information.

        Args:
            state: Current ideas bot state

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
            You are an expert in creative writing and idea generation education. Analyze this teacher's query and extract key information.

            Teacher's Query: "{query}"

            Analyze and respond with a JSON object containing:
            {{
                "query_type": "idea_generation|organization|genre_elements|brainstorming|general",
                "target_genre": "narrative|informational|opinion|personal_narrative|compare_contrast|not_specified",
                "target_topic": "specific writing topic or theme mentioned",
                "grade_level": "prek|kindergarten|1st_grade|mixed|not_specified",
                "key_concepts": ["list", "of", "main", "concepts"],
                "urgency_level": "low|medium|high"
            }}

            Query Type Definitions:
            - idea_generation: Questions about generating ideas, brainstorming, creative prompts
            - organization: Questions about organizing ideas, graphic organizers, structure planning
            - genre_elements: Questions about narrative elements, informational text features, opinion structure
            - brainstorming: Questions about brainstorming techniques, idea development strategies
            - general: Broad questions about creative writing or idea generation
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
                "target_genre": analysis_result.get("target_genre", "not_specified"),
                "target_topic": analysis_result.get("target_topic", ""),
                "grade_level": analysis_result.get("grade_level", "not_specified"),
                "retry_count": 0,
                "conversation_depth": state.get("conversation_depth", 0) + 1
            }

        except Exception as e:
            print(f"❌ Error in analyze_query_node: {str(e)}")
            return {
                "original_query": query if 'query' in locals() else "Unknown query",
                "query_type": "general",
                "target_genre": "not_specified",
                "target_topic": "",
                "grade_level": "not_specified",
                "last_error": f"Query analysis failed: {str(e)}",
                "retry_count": state.get("retry_count", 0) + 1
            }

    async def retrieve_forms_node(self, state: IdeasState) -> Dict[str, Any]:
        """
        Node 2: Retrieve relevant educational forms based on query analysis.

        Args:
            state: Current ideas bot state

        Returns:
            Updated state with retrieved forms and context
        """
        try:
            query_type = state.get("query_type", "general")
            target_genre = state.get("target_genre", "not_specified")
            target_topic = state.get("target_topic", "")

            # Retrieve ideas forms (M-Q)
            relevant_forms = await form_retrieval_service.get_ideas_forms()

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
                if 'writing_standards' in standards_data:
                    standards_summary += "Writing Standards:\n"
                    for standard in standards_data['writing_standards'][:3]:
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
                "form_context": "Error retrieving educational forms. Using general creative writing knowledge.",
                "last_error": f"Form retrieval failed: {str(e)}",
                "retry_count": state.get("retry_count", 0) + 1
            }

    async def generate_response_node(self, state: IdeasState) -> Dict[str, Any]:
        """
        Node 3: Generate a comprehensive response using the retrieved forms and query analysis.

        Args:
            state: Current ideas bot state

        Returns:
            Updated state with generated response
        """
        try:
            original_query = state.get("original_query", "")
            query_type = state.get("query_type", "general")
            target_genre = state.get("target_genre", "not_specified")
            target_topic = state.get("target_topic", "")
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
            if needs_context and (target_genre != "not_specified" or target_topic):
                topic_str = target_topic if target_topic else "idea generation and organization"
                clarification_message = f"""Great! I can definitely help you teach {topic_str}.

To create the most helpful lesson plan for you, could you let me know:

1️⃣ **What grade level is this lesson for?**
   • Pre-K
   • Kindergarten
   • 1st Grade

2️⃣ **What genre of writing are you focusing on?**
   • Narrative (stories with characters, setting, plot)
   • Informational (facts, explanations, descriptions)
   • Opinion (preferences, arguments, reasons)
   • Personal Narrative (personal experiences)

3️⃣ **Do you have a specific topic or theme in mind?**
   • Unit topic (e.g., animals, seasons, community helpers)
   • Student choice
   • Mentor text connection

Once I know these details, I'll create a complete, scripted lesson plan with brainstorming activities and graphic organizers tailored to your students! 💡"""

                ai_response = AIMessage(content=clarification_message)
                return {
                    "messages": [ai_response],
                    "response_generated": True,
                    "needs_clarification": True,
                    "retry_count": 0
                }

            # Build comprehensive system prompt
            system_prompt = f"""
            You are an expert in idea generation and organization instruction for early childhood education.

            **YOUR EXPERTISE: Idea Generation & Organization Instruction**

            You generate COMPLETE, SCRIPTED LESSON PLANS in this exact structure:

            **LESSON PLAN STRUCTURE:**

            **A. Standards**
            - Reference appropriate Pre-K/Kindergarten standards from the provided forms
            - Example: "ELAGSEKW3: Use a combination of drawing, dictating, and writing to narrate a single event"

            **B. Objectives**
            - Derive specific, measurable objectives from lesson content
            - Example: "Students will generate and organize ideas for narrative writing about a favorite memory using a story map"
            - Example: "Students will brainstorm facts about animals for informational writing using a web graphic organizer"

            **C. Materials**
            - List everything needed with bullet points
            - Example: "Story maps, brainstorming charts, drawing paper, mentor texts, writing paper, graphic organizers"

            **D. Scripted Lesson Plan for Idea Generation & Organization**

            **1. Review & Connect**

            [The purpose of this part of the lesson is to review the writing genre and connect to the unit topic, activating prior knowledge about the writing purpose.]

            Teacher Script:

            Provide complete dialogue with {{actions}} and (expected responses)

            ---

            **2. Model, Explain & Engage**

            [The purpose of this part of the lesson is to introduce the genre-specific elements, demonstrate brainstorming strategies, and model how to organize ideas using graphic organizers.]

            Teacher Script:

            Include genre element introduction (characters/setting for narrative, facts for informational, opinion/reasons for opinion)
            Include mentor text examples for idea generation
            Include think-aloud demonstrating brainstorming process
            Include graphic organizer introduction and modeling
            Include topic and purpose explanation

            ---

            **3. Guided Practice**

            [The purpose is to give children practice generating and organizing ideas collaboratively with teacher support.]

            Teacher Script:

            Include collaborative brainstorming activities (Turn & Talk, Class Web, Story Circle)
            Include group graphic organizer completion
            Include idea organization strategies
            Include genre-specific idea development

            ---

            **4. Application**

            [The purpose of this part of the lesson is to facilitate children's independent idea generation and organization for their own writing.]

            Teacher Script:

            Include independent brainstorming (drawing, listing, webbing)
            Include personal graphic organizer completion
            Include partner sharing of ideas
            Include beginning draft/drawing based on organized ideas

            ---

            **5. Wrap-Up**

            [The purpose of this part of the lesson is to review genre elements and celebrate idea generation, connecting to next writing steps.]

            Teacher Script:

            Review genre elements and topic
            Share student examples of idea generation
            Connect to next writing steps (drafting, adding details)
            Celebrate creativity and idea diversity

            **KEY PRINCIPLES:**
            - Focus on specific writing genres: narrative, informational, opinion, personal narrative
            - Use graphic organizers to organize ideas (story maps, webs, lists, T-charts, Venn diagrams)
            - Connect to unit topics and themes
            - Use mentor texts to inspire ideas
            - Teach genre-specific elements (characters/setting for narrative, facts for informational, etc.)
            - Support drawing, dictation, and writing based on developmental level
            - Celebrate all forms of idea expression
            - Foster creativity and original thinking

            **CRITICAL OUTPUT REQUIREMENTS:**
            ✅ Be a complete, rehearsal-ready lesson plan
            ✅ Include ALL 5 subsections with detailed scripts
            ✅ MUST include the bracketed [Explanation] at the start of EVERY section (1-5)
            ✅ MUST include full "Teacher Script:" with complete dialogue for every section
            ✅ Use clean formatting: [explanations], plain Teacher Script sections, (responses), {{actions}}
            ✅ DO NOT use hashtags (#), plus signs (+Level), asterisks (*Adaptation), or double hashtags (##) in user-facing output
            ✅ Include specific brainstorming and organizing activities
            ✅ Connect to specific writing genre (narrative, informational, opinion, personal narrative)
            ✅ Be 20-25 minutes total lesson time
            ✅ NEVER mention "Forms M-Q", "Form P", "Form N" or any form letters/numbers to users
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
            - Target Genre: {target_genre}
            - Target Topic: {target_topic if target_topic else 'Not specified'}
            - Grade Level: {grade_level}

            RELEVANT EDUCATIONAL FORMS CONTENT:
            {form_context}

            **IMPORTANT**: Use the conversation history above to understand the full context of the teacher's request. If they're following up on a previous question, continue that discussion naturally.

            **DETERMINE YOUR RESPONSE TYPE:**

            IF the teacher asks for:
            - "Create a lesson plan"
            - "Generate a lesson"
            - "Help me teach [specific genre/topic]"
            - "I need an idea generation lesson for..."
            - "give me a lesson plan" (follow-up)

            → THEN generate a **COMPLETE SCRIPTED LESSON PLAN** using the structure in your system prompt.

            IF the teacher asks for:
            - "How do I..." questions
            - "What are some strategies for..." questions
            - "Can you explain..." questions
            - General guidance or tips

            → THEN provide **TARGETED GUIDANCE** with:
            1. **Direct Answer** to their question
            2. **2-3 Specific Activities** from Form P with materials and steps
            3. **Differentiation** for drawing/dictating, emerging writers, developing writers
            4. **Genre Connection** (narrative, informational, opinion, personal narrative)
            5. **Graphic Organizer Suggestions**

            Always use the exact content from the provided forms. Reference Form M for genre elements, Form N for structure, Form O for templates, Form P for activities, and Form Q for modifications.

            Make your response immediately actionable, inspiring, and classroom-ready.
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
            However, I can still help with your creative writing question: "{original_query}"

            Here are some general idea generation and organization strategies you can try:

            **For Idea Generation:**
            - Use brainstorming webs and mind maps
            - Start with mentor texts for inspiration
            - Connect to students' personal experiences
            - Use visual prompts (pictures, objects, videos)
            - Practice "What if?" questions

            **For Organization:**
            - Use graphic organizers (story maps, webs, lists)
            - Teach genre-specific structures
            - Model organizing ideas step-by-step
            - Support drawing and dictation for emergent writers
            - Practice arranging ideas in logical order

            **Materials to Try:**
            - Story maps for narrative writing
            - Webs for informational writing
            - T-charts for opinion writing
            - Drawing paper and colored pencils
            - Sentence starters and writing frames

            Would you like me to elaborate on any of these strategies, or do you have a more specific aspect of idea generation you'd like to explore?
            """)

            return {
                "messages": [fallback_response],
                "response_generated": True,
                "last_error": f"Response generation failed: {str(e)}",
                "retry_count": state.get("retry_count", 0) + 1
            }

    async def quality_check_node(self, state: IdeasState) -> Dict[str, Any]:
        """
        Node 4: Check the quality of the generated response and suggest improvements.

        Args:
            state: Current ideas bot state

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
            Evaluate this creative writing instruction response for a teacher's question.

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
                "inspires_creativity": true/false,
                "genre_connection": true/false,
                "improvement_suggestions": ["list", "of", "specific", "improvements"],
                "quality_score": 1-10
            }}

            A quality response should:
            - Directly answer the teacher's question
            - Include specific, actionable activities
            - List required materials and graphic organizers
            - Provide differentiation strategies
            - Connect to specific writing genres
            - Inspire creativity and original thinking
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

    async def follow_up_node(self, state: IdeasState) -> Dict[str, Any]:
        """
        Node 5: Generate follow-up questions or suggestions for continued learning.

        Args:
            state: Current ideas bot state

        Returns:
            Updated state with follow-up suggestions
        """
        try:
            query_type = state.get("query_type", "general")
            target_genre = state.get("target_genre", "not_specified")
            target_topic = state.get("target_topic", "")

            # Generate contextual follow-up questions
            follow_up_suggestions = []

            if query_type == "idea_generation":
                follow_up_suggestions = [
                    "Would you like creative writing prompts for this genre?",
                    "Are you interested in mentor text suggestions?",
                    "Would brainstorming game activities be helpful?"
                ]
            elif query_type == "organization":
                follow_up_suggestions = [
                    "Would you like graphic organizer templates?",
                    "Are you interested in teaching sequence and structure?",
                    "Would differentiation strategies for organization be helpful?"
                ]
            elif query_type == "genre_elements":
                follow_up_suggestions = [
                    "Would you like more genre-specific teaching strategies?",
                    "Are you interested in genre comparison activities?",
                    "Would mentor text recommendations be helpful?"
                ]
            else:
                follow_up_suggestions = [
                    "Would you like more specific activities for any particular genre?",
                    "Are there specific brainstorming techniques you'd like to explore?",
                    "Would assessment strategies for creative writing be helpful?"
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
                "follow_up_questions": ["Is there anything specific about idea generation you'd like to explore further?"],
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
                "target_genre": "not_specified",
                "target_topic": "",
                "grade_level": "not_specified",
                "key_concepts": [],
                "urgency_level": "medium"
            }

# Global instance for use in the graph
ideas_nodes = IdeasNodes()