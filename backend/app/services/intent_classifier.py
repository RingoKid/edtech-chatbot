"""
Intent Classification Service using OpenAI for educational domain routing.
"""
import re
import json
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.config import settings
from app.schemas.intent import IntentResult, IntentType

class IntentClassificationService:
    """Service for classifying teacher queries into educational domains."""
    
    def __init__(self):
        """Initialize the intent classification service."""
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured for intent classification")
        
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.1,  # Low temperature for consistent classification
            api_key=settings.openai_api_key.get_secret_value()
        )
        
        # Define lesson type characteristics based on Forms JSON data
        self.domain_definitions = {
            "handwriting": {
                "keywords": ["letter", "formation", "handwriting", "spelling", "phonics", "sound", "grip", "posture", "fine motor", "stroke", "pencil", "writing", "phoneme", "grapheme"],
                "forms": ["A", "B", "C", "D", "E", "F", "G", "H"],
                "description": "Handwriting & Spelling direct instruction lessons with structured 5-part format",
                "lesson_structure": ["Review & Connect", "Model Explain & Engage", "Guided Practice", "Application", "Wrap-Up"],
                "components": ["explanation", "teacher_script", "child_response", "teacher_does", "gesture", "sequence_verbal_cues", "adaptation", "modification"],
                "grade_levels": ["PreK", "Kindergarten", "First"],
                "requires_collection": ["grade_level", "objectives", "letters_sounds_focus"]
            },
            "vocabulary": {
                "keywords": ["vocabulary", "sentence", "structure", "grammar", "subject", "verb", "genre", "writing", "unit", "theme", "informational", "narrative", "opinion"],
                "forms": ["I", "J", "K", "L"],
                "description": "Vocabulary & Sentence Structure direct instruction lessons within genre-specific writing",
                "lesson_structure": ["Review & Connect", "Model Explain & Engage", "Guided Practice", "Application", "Wrap-Up"],
                "components": ["explanation", "teacher_script", "child_response", "teacher_does", "adaptation", "modification"],
                "grade_levels": ["PreK", "Kindergarten", "First"],
                "requires_collection": ["writing_type", "key_vocabulary", "objectives"]
            },
            "ideas": {
                "keywords": ["ideas", "brainstorm", "story", "creative", "writing", "narrative", "informational", "opinion", "topic", "genre", "organize", "plan", "generation", "organization"],
                "forms": ["M", "N", "O", "P", "Q"],
                "description": "Idea Generation & Organization direct instruction lessons for genre-specific writing",
                "lesson_structure": ["Review & Connect", "Model Explain & Engage", "Guided Practice", "Application", "Wrap-Up"],
                "components": ["explanation", "teacher_script", "child_response", "teacher_does", "adaptation", "modification"],
                "grade_levels": ["PreK", "Kindergarten", "First"],
                "requires_collection": ["writing_topic", "genre", "objectives"]
            },
            "general": {
                "keywords": ["classroom", "management", "assessment", "curriculum", "student", "teaching", "education", "help", "general", "reading", "literacy"],
                "forms": ["A-Q"],
                "description": "General education support and clarification requests within literacy scope",
                "lesson_structure": [],
                "components": [],
                "grade_levels": ["All"],
                "requires_collection": []
            },
            "out_of_scope": {
                "keywords": ["math", "mathematics", "numbers", "counting", "addition", "subtraction", "science", "experiment", "animals", "plants", "social studies", "history", "geography", "community"],
                "forms": [],
                "description": "Queries outside literacy/language arts scope (math, science, social studies, etc.)",
                "lesson_structure": [],
                "components": [],
                "grade_levels": [],
                "requires_collection": []
            }
        }
        
        print("✅ Intent Classification Service initialized with GPT-4o")
    
    async def classify_intent(self, message: str, conversation_context: str = "") -> IntentResult:
        """
        Classify a teacher's message into an educational domain.

        Args:
            message: Teacher's question or input
            conversation_context: Previous conversation messages for context

        Returns:
            IntentResult with classification details
        """
        try:
            # Create comprehensive classification prompt with conversation context
            classification_prompt = self._build_classification_prompt(message, conversation_context)

            response = await self.llm.ainvoke([
                SystemMessage(content="You are an expert educational domain classifier. Respond only with valid JSON."),
                HumanMessage(content=classification_prompt)
            ])
            
            # Parse the response
            result_dict = self._parse_classification_response(response.content)
            
            return IntentResult(
                intent=IntentType(result_dict["intent"]),
                confidence=float(result_dict["confidence"]),
                reasoning=result_dict.get("reasoning", ""),
                suggested_forms=result_dict.get("suggested_forms", [])
            )
            
        except Exception as e:
            return IntentResult(
                intent=IntentType.GENERAL,
                confidence=0.3,
                reasoning=f"Classification failed, defaulting to general: {str(e)}",
                suggested_forms=["A", "B", "C"]
            )
    
    def _build_classification_prompt(self, message: str, conversation_context: str = "") -> str:
        """Build the classification prompt with domain definitions based on Forms JSON data."""

        context_section = ""
        if conversation_context:
            context_section = f"""
        **CONVERSATION HISTORY (for context):**
        {conversation_context}

        **CRITICAL INSTRUCTIONS FOR FOLLOW-UP MESSAGES:**
        - If the teacher previously asked about a specific LETTER (A, B, C, etc.), ANY follow-up question should be classified as "handwriting"
        - If the teacher previously asked about handwriting, letter formation, or spelling, maintain "handwriting" intent
        - If the teacher previously asked about vocabulary, sentence structure, or grammar, maintain "vocabulary" intent  
        - If the teacher previously asked about ideas, brainstorming, or creative writing, maintain "ideas" intent
        - Follow-up questions like "What about...", "How do I...", "Can you explain...", "Tell me more..." should inherit the previous intent
        - Only classify as "general" if the conversation context doesn't provide clear domain context
        """

        return f"""
        You are an expert in early childhood LITERACY education. Classify this teacher's request into ONE of these categories:

        **🎯 IN-SCOPE: LITERACY & LANGUAGE ARTS (Forms A-Q)**

        1. **HANDWRITING** (Forms A-H) - Requests for lessons about:
           - Letter formation and stroke sequences using sequence verbal cues
           - Fine motor skill development and pencil grip instruction
           - Handwriting and spelling integration with phoneme-grapheme connections
           - Sound-letter coordination activities and proper writing posture
           - Structured handwriting lessons with Review & Connect, Model Explain & Engage, Guided Practice, Application, and Wrap-Up
           - Teaching specific letters, sounds, or handwriting objectives
           Keywords: letter, formation, handwriting, spelling, phonics, sound, grip, posture, fine motor, stroke, pencil, writing

        2. **VOCABULARY** (Forms I-L) - Requests for lessons about:
           - Vocabulary and sentence structure instruction within genre-specific writing
           - Teaching sentence patterns (subject-verb, be-verbs, action verbs)
           - Connecting unit vocabulary to sentence writing tasks
           - Building sentences with proper grammar structures for specific writing genres
           - Structured vocabulary lessons with Review & Connect, Model Explain & Engage, Guided Practice, Application, and Wrap-Up
           Keywords: vocabulary, sentence, structure, grammar, subject, verb, genre, writing, unit, theme, informational, narrative, opinion

        3. **IDEAS** (Forms M-Q) - Requests for lessons about:
           - Idea generation and organization for specific genres and writing purposes
           - Brainstorming strategies and note-taking for writing topics
           - Teaching genre-specific writing skills (informational, narrative, opinion, personal narrative)
           - Organizing ideas using graphic organizers and structured planning
           - Text-to-writing connections and unit topic integration
           - Structured idea generation lessons with Review & Connect, Model Explain & Engage, Guided Practice, Application, and Wrap-Up
           Keywords: ideas, brainstorm, story, creative, writing, narrative, informational, opinion, topic, genre, organize, plan

        4. **GENERAL** - General literacy/language arts questions within scope:
           - Reading instruction strategies
           - Literacy assessment
           - Language development
           - Writing instruction (when not specific to handwriting/vocabulary/ideas)
           Keywords: reading, literacy, language, assessment, instruction

        **❌ OUT OF SCOPE: NON-LITERACY SUBJECTS**

        5. **OUT_OF_SCOPE** - Queries about subjects NOT covered by Language For Composing curriculum:
           - **Math** (numbers, counting, addition, subtraction, shapes, measurement, patterns, problem-solving)
           - **Science** (experiments, animals, plants, weather, physical science, life science)
           - **Social Studies** (history, geography, community helpers, cultures, maps)
           - **Other** (art, music, PE, technology, health)
           Keywords: math, mathematics, numbers, counting, science, experiment, animals, plants, history, geography, community

        **⚠️ IMPORTANT SCOPE BOUNDARIES:**
        - ONLY classify as handwriting/vocabulary/ideas/general if the query relates to LITERACY, WRITING, LANGUAGE, or READING
        - If the query is about MATH, SCIENCE, SOCIAL STUDIES, or other non-literacy subjects → classify as "out_of_scope" with high confidence (0.9+)
        - The Language For Composing curriculum (Forms A-Q) covers ONLY literacy and language arts instruction
{context_section}
        **CURRENT TEACHER'S REQUEST:** "{message}"

        **CLASSIFICATION GUIDELINES:**
        - **CRITICAL SCOPE CHECK**: First determine if query is about literacy/language arts or OTHER subjects
        - If query mentions math, science, social studies → IMMEDIATELY classify as "out_of_scope" with 0.9+ confidence
        - **CRITICAL**: For follow-up messages, ALWAYS use conversation history to maintain intent continuity
        - If conversation history shows handwriting context (letters, formation, spelling), classify follow-ups as "handwriting" with high confidence (0.8+)
        - If conversation history shows vocabulary context (sentence structure, grammar), classify follow-ups as "vocabulary" with high confidence (0.8+)
        - If conversation history shows ideas context (brainstorming, creative writing), classify follow-ups as "ideas" with high confidence (0.8+)
        - Use confidence 0.9+ for very clear requests OR out-of-scope queries
        - Use confidence 0.8+ for requests clearly aligned with one lesson type's scope OR follow-up questions with clear context
        - Use confidence 0.7+ for moderately clear requests with some ambiguity
        - Use confidence 0.5-0.7 for somewhat ambiguous requests requiring clarification
        - Use confidence below 0.5 ONLY for unclear general requests with NO conversation context

        **FORM MAPPING:**
        - Handwriting/Spelling: Forms A (objectives), B (structure), C (template), D (activities), E (practices), F (verbal cues), G (gestures), H (adaptations)
        - Vocabulary/Sentence: Forms I (structure), J (template), K (activities), L (modifications)
        - Ideas/Organization: Forms M (genre elements), N (structure), O (template), P (activities), Q (modifications)
        - Out of Scope: No forms available (non-literacy subjects)

        Respond with ONLY this JSON format:
        {{
            "intent": "handwriting|vocabulary|ideas|general|out_of_scope",
            "confidence": 0.85,
            "reasoning": "Brief explanation connecting request to specific lesson type and forms OR explaining why it's out of scope",
            "suggested_forms": ["A", "B", "C"] or []
        }}
        """
    
    def _parse_classification_response(self, response_content: str) -> Dict[str, Any]:
        """
        Parse the JSON response from OpenAI with robust error handling.
        
        Args:
            response_content: Raw response from OpenAI
            
        Returns:
            Parsed classification dictionary
        """
        try:
            # Try to extract JSON using regex
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
                
                # Validate required fields
                if "intent" not in result or "confidence" not in result:
                    raise ValueError("Missing required fields in classification response")
                
                # Validate intent value
                valid_intents = ["handwriting", "vocabulary", "ideas", "general", "out_of_scope"]
                if result["intent"] not in valid_intents:
                    raise ValueError(f"Invalid intent: {result['intent']}")
                
                # Validate confidence range
                confidence = float(result["confidence"])
                if not (0.0 <= confidence <= 1.0):
                    raise ValueError(f"Confidence out of range: {confidence}")
                
                return result
            else:
                raise ValueError("No JSON found in response")
                
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"⚠️ Classification parsing error: {str(e)}")
            # Return safe fallback values
            return {
                "intent": "general",
                "confidence": 0.3,
                "reasoning": f"Failed to parse classification response: {str(e)}",
                "suggested_forms": ["A", "B", "C"]
            }
    
    def get_domain_info(self, intent: IntentType) -> Dict[str, Any]:
        """
        Get information about a specific domain.
        
        Args:
            intent: The intent type to get info for
            
        Returns:
            Domain information dictionary
        """
        return self.domain_definitions.get(intent.value, self.domain_definitions["general"])
    
    def suggest_clarifying_questions(self, message: str, confidence: float) -> List[str]:
        """
        Generate clarifying questions for low-confidence classifications.
        
        Args:
            message: Original teacher message
            confidence: Classification confidence score
            
        Returns:
            List of clarifying questions
        """
        if confidence >= 0.7:
            return []  # High confidence, no clarification needed
        
        # Generate clarifying questions aligned with lesson types
        questions = [
            "Would you like to focus on a handwriting & spelling, vocabulary and sentence structure, or text generation & organization lesson?",
            "Are you looking for a direct instruction lesson with scripted components and structured activities?",
            "Do you need help with letter formation, sentence building, or idea organization for writing?",
            "Would you like me to create a lesson plan with standards, objectives, materials, and detailed teacher scripts?"
        ]
        
        return questions[:3]  # Return top 3 questions

# Global instance
intent_service = IntentClassificationService()