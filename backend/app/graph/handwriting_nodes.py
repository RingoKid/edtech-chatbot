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
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        
        self.llm = ChatOpenAI(
            model="gpt-4o",  # Using GPT-4 Omni for better reasoning
            temperature=0.7,  # Balanced creativity and consistency
            api_key=settings.openai_api_key.get_secret_value()
        )
        
        # Define target forms for handwriting instruction
        self.target_forms = ["A", "B", "C", "D", "E", "F", "G", "H"]
        
        print("✅ HandwritingNodes initialized with GPT-4 Omni")
    
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
            
            return {
                "original_query": query,
                "query_type": analysis_result.get("query_type", "general"),
                "target_letters": analysis_result.get("target_letters", []),
                "grade_level": analysis_result.get("grade_level", "not_specified"),
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

            needs_context = (
                is_lesson_request and
                conversation_depth <= 1 and  # First interaction
                grade_level == "not_specified"  # Missing grade level
            )

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

            You generate COMPLETE, SCRIPTED LESSON PLANS in this exact structure:

            **LESSON PLAN STRUCTURE:**

            **A. Standards**
            - Reference appropriate Pre-K/Kindergarten standards from the provided forms
            - Example: "ELAGSEKRF3a: Demonstrate basic knowledge of letter-sound correspondences"

            **B. Objectives**
            - Derive specific, measurable objectives from lesson content
            - Example: "Pronounce the /z/ sound correctly"
            - Example: "Form uppercase and lowercase z using correct stroke sequence"

            **C. Materials**
            - List everything needed with bullet points
            - Example: "Zebra sound cards, handwriting worksheets, pencils, visual charts"

            **D. Scripted Lesson Plan for Handwriting & Spelling**

            **1. Review & Connect**

            [The purpose of this part of the lesson is to start with a quick review of previously learned sounds. Do not use sounds that have not been directly taught. Do not use words that have sounds that have not been directly taught.]

            Teacher Script:

            Let's review our sounds. We are doing our Sound Sparks game. Look up here. When I point to a sound, you will all say that sound when I say go, and when you see my hand close to a fist.

            Ready. My Turn. {{Teacher points to /m/.}}

            Get Ready. Go. (children chorally respond /m/)

            {{Teacher continues this process, reviewing previous sounds. Should be around 2-3 minutes.}}

            ---

            **2. Model, Explain & Engage**

            [The purpose of this part of the lesson is to connect a sound or sound patterns that you focused on during your reading block to writing its corresponding grapheme patterns. First, make sure children clearly can distinguish the targeted sound; then, hook that sound to the letter patterns through modeling and explaining the sequence of strokes for letters and correct order of letters.]

            Teacher Script:

            We've been working on the /z/ sound. My turn. Listen to my sound /z/.

            Put your hand on your vocal box–now say the sound /z/. Did you feel your vocal box? (Children should respond yes)

            That means you are using your voice, so we use our voice to make the /z/ sound.

            Where are your lips when you make the sound? (Children expected to say something like opened).

            Right, you part your lips and your mouth is spread. And where is your tongue? (Children expected to say top).

            Yes, the top of your mouth and slightly behind your teeth.

            Let's do our sound motion. Get Ready Go. (children use the buzzing bee gesture while saying /z/. Gesture: Move hand in a zigzag motion through the air while making the /z/ sound).

            Let's try. My turn. /z/. Jenna, get ready. Go. (child pronounces /z/ sound)

            {{The teacher has each child in the group demonstrate the correct pronunciation and provides correction if necessary; if this is a whole group lesson, the teacher has all children repeat first. Then, the teacher will call on a few children who may need extra support}}.

            Great! Now we are going to play our Sound Hunt Game. Each of you has a zebra card because zebra starts with the /z/ sound. We are listening for the /z/ sound at the beginning of the word. I will say a word, and if you hear the /z/ sound at the beginning, I want you to lift up your zebra card when I say go. If you don't hear it, do not lift up the card.

            My turn. The word is zebra. Get Ready...Go. (children should have lifted the zebra card). Right. Everyone should have lifted the card because zebra begins with /z/. Alright put your listening ears on. My turn. The word is tiger. Get Ready…Go. (children should not have lifted their card).

            {{Teacher repeats this process to cement sound to memory then connects to letter form}}

            Wonderful! The letter that matches the /z/ sound – is the letter z. Watch me closely. I will show you how to form uppercase Z then lower case z. No one is using their pencil yet or writing. You are watching me.

            {{Teacher demonstrates on a visual that shows children the correct sequence of letter strokes and uses sequence verbal cues}}.

            **Sequence Verbal Cues for letter z:** Little line across. Slant down the stairs. Little line across.

            First, start at the top line. Little line across. Next, slant down the stairs. And then little line across. 1, 2, 3 lines.

            Say it with me as you watch. Start at the top line. Say It. (children repeat). Little line across. Say it. (children repeat). Slant down the stairs. Say It (children repeat). Little line across. (children repeat). Let's Count. Ready. Go. (Children count 1, 2, 3 lines).

            {{Teacher repeats this process for lowercase z–drawing children's attention to where lowercase z starts, on the dotted middle line.}}

            ---

            **3. Guided Practice**

            [The purpose is to give children practice writing the letter while supporting proper pencil grip and correct sequence of stroke formation using handwriting lines.]

            Teacher Script:

            Let's practice how to write uppercase letter z first. We are not using our pencils yet. Let's do our Magic Finger Write. Place your finger at the top of the line. Let me see {{Teacher checks students finger placement}}. Remember it's important when we are writing to try to touch the lines. The lines are there to help us.

            Little line across. (children move finger across)

            Slant down the stairs. (children move finger in a slant downwards)

            Little line across. (children move finger across)

            {{Teacher has students do that a few times and repeat for lowercase z}}.

            Now, pick up the pencil. Show me how you hold your pencil. Remember we slant our paper. Your free hand holds the paper.

            Let's do our Trace & Say. I have dotted lines for you to trace. We are doing uppercase Z first {{Teacher points to uppercase Z}}. Where do we start if we want to write uppercase Z? (children should say the top line). Yes. Everyone put your pencil at the top line on the left. You want to start here. {{Teacher points to top left-hand line}} Let me see. {{Teacher corrects students if needed}}. Ready. Write and say. Go. (Children write using dotted lines as guides and say the sequence verbal cues: "Little line across. Slant down the stairs. Little line across.")

            Now you do one using the dotted lines. {{Teacher monitors children's letter writing}}.

            Do one more using the dotted lines {{Teacher monitors and repeats process for lowercase z}}.

            ---

            **4. Application**

            [The purpose of this part of the lesson is to facilitate children's spelling of the letter or letter patterns when they hear the sound(s). This supports children's early coordination of matching sound to letter(s) for the purpose of spelling words.]

            Teacher Script:

            Boys and girls, I am going back to the /z/ Sound Hunt game, but now it's the Sound-Letter Hunt game. I am going to say a word. You are listening to the beginning sound of that word. You are going to write the letter of the sound you hear in the beginning of the word. Let me show you. My turn. The word is apple. So I am thinking the beginning sound of apple is /a/. I know that the /a/ sound is written with the letter a. I am going to look at my handwriting Sound-Letter Hunt worksheet. {{Teacher directs students' attention to the handwriting sound-hunt worksheet. The worksheet displays some previously learned letter-sounds along with the new targeted letter-sound. The handout shows the proper way to write those letters and dotted lines for children to use as guides}}

            I see letter a. Now I am going to look to find letter a on my paper. I am going to look at how to write the letter a. Then, I am going to use the dotted lines to write the letter a.

            Okay are you ready? Listen. My turn. The word is zebra. Get ready. Go. (children should hear the sound /z/ and write the letter z). {{Teacher uses the same list of words that were used in the Sound Hunt activity above. Teacher monitors students' answers providing corrective feedback.}}

            ---

            **5. Wrap-Up**

            [The purpose of this part of the lesson is to remind students what they were focused on and provide praise for their accomplishments.]

            Teacher Script:

            Alright, boys and girls I am so proud of you. What sound have we been working on? {{Teacher holds up zebra sound card}} (Children respond /z/).

            Perfect! And which of these letters say /z/? {{Teacher provides children with a choice}} (Children can touch the correct letter that is displayed in small groups, or the teacher can call on a student to circle the correct letter for the whole class).

            Show me how to write it (children air write with sequence verbal cues: little line across, slant down the stairs, little line across)

            Wonderful! Kiss your brains.

            **EVIDENCE-BASED PRACTICES TO INCORPORATE:**
            - Teach proper pencil grip and left-to-right writing
            - Help children pronounce, identify, and isolate phonemes
            - Teach letter formation step-by-step with exact stroke order
            - Compare letter shapes and strokes
            - Retrieve prior phoneme-grapheme knowledge
            - Provide corrective and confirmatory feedback
            - Encourage invented spelling attempts

            **CRITICAL OUTPUT REQUIREMENTS:**
            ✅ Be a complete, rehearsal-ready lesson plan
            ✅ Include ALL 5 subsections with detailed scripts
            ✅ MUST include the bracketed [Explanation] at the start of EVERY section (1-5)
            ✅ MUST include full "Teacher Script:" with complete dialogue for every section
            ✅ Use clean formatting: [explanations], plain Teacher Script sections, (responses), {{actions}}
            ✅ DO NOT use hashtags (#), plus signs (+Level), asterisks (*Adaptation), or double hashtags (##) in user-facing output
            ✅ Include specific letter formation activities and evidence-based practices
            ✅ Provide sequence verbal cues and gesture descriptions naturally within the script
            ✅ Be 20-25 minutes total lesson time
            ✅ NEVER mention "Forms A-H", "Form D", "Form E", "Form F", "Form G" or any form letters/numbers to users
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

            # Build specific response prompt based on query analysis
            response_prompt = f"""
            {conversation_context}CURRENT TEACHER REQUEST: "{original_query}"

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

            → THEN generate a **COMPLETE SCRIPTED LESSON PLAN** using the structure in your system prompt.

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
            original_query = state.get("original_query", "")
            query_type = state.get("query_type", "general")
            
            # Use LLM to evaluate response quality
            quality_check_prompt = f"""
            Evaluate this handwriting instruction response for a teacher's question.
            
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
                "improvement_suggestions": ["list", "of", "specific", "improvements"],
                "quality_score": 1-10
            }}
            
            A quality response should:
            - Directly answer the teacher's question
            - Include specific, actionable activities
            - List required materials
            - Provide differentiation strategies
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