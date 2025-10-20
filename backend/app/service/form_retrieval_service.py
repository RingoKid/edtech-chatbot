"""
Form Retrieval Service for accessing educational content from DynamoDB.
Handles loading and processing of Forms A-H (handwriting), I-L (vocabulary), M-Q (ideas).
"""
import asyncio
import json
from typing import List, Dict, Any, Optional
from boto3.dynamodb.conditions import Attr
from app.database import get_db

class FormRetrievalService:
    """Service for retrieving and processing educational forms from DynamoDB."""

    def __init__(self):
        """Initialize the form retrieval service."""
        self.table = get_db()

        # Define all form categories by domain
        self.handwriting_forms = ["A", "B", "C", "D", "E", "F", "G", "H"]
        self.vocabulary_forms = ["I", "J", "K", "L"]
        self.ideas_forms = ["M", "N", "O", "P", "Q"]
        self.all_forms = self.handwriting_forms + self.vocabulary_forms + self.ideas_forms

        print("✅ FormRetrievalService initialized with DynamoDB backend")

    def _get_forms_by_categories_sync(self, categories: List[str]) -> List[Dict[str, Any]]:
        """
        Synchronous helper to retrieve forms from DynamoDB by category.
        Used internally by async wrapper.

        Args:
            categories: List of form categories (e.g., ["A", "B", "C"])

        Returns:
            List of form data dictionaries
        """
        try:
            forms = []

            # Query DynamoDB using CategoryIndex
            for category in categories:
                response = self.table.query(
                    IndexName='CategoryIndex',
                    KeyConditionExpression='category = :cat',
                    ExpressionAttributeValues={':cat': category.upper()}
                )

                for item in response.get('Items', []):
                    forms.append({
                        'form_id': item.get('form_id'),
                        'form_letter': item.get('category'),
                        'category': item.get('category'),
                        'domain': item.get('domain'),
                        'title': item.get('title'),
                        'content': item.get('content', {}),
                        'created_at': item.get('created_at'),
                        'updated_at': item.get('updated_at')
                    })

            return forms

        except Exception as e:
            print(f"❌ Error retrieving forms from DynamoDB: {e}")
            return []

    async def _get_forms_by_categories(self, categories: List[str]) -> List[Dict[str, Any]]:
        """
        Async wrapper for retrieving forms from DynamoDB by category.
        Runs synchronous DynamoDB call in thread pool to avoid blocking event loop.

        Args:
            categories: List of form categories (e.g., ["A", "B", "C"])

        Returns:
            List of form data dictionaries
        """
        return await asyncio.to_thread(self._get_forms_by_categories_sync, categories)

    async def get_handwriting_forms(self, form_letters: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve specific handwriting forms or all handwriting forms.

        Args:
            form_letters: List of form letters to retrieve (e.g., ["A", "B"]).
                         If None, returns all handwriting forms A-H.

        Returns:
            List of form data dictionaries.
        """
        if form_letters is None:
            form_letters = self.handwriting_forms

        return await self._get_forms_by_categories(form_letters)

    async def get_vocabulary_forms(self, form_letters: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve specific vocabulary forms or all vocabulary forms.

        Args:
            form_letters: List of form letters to retrieve (e.g., ["I", "J"]).
                         If None, returns all vocabulary forms I-L.

        Returns:
            List of form data dictionaries.
        """
        if form_letters is None:
            form_letters = self.vocabulary_forms

        return await self._get_forms_by_categories(form_letters)

    async def get_ideas_forms(self, form_letters: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve specific ideas forms or all ideas forms.

        Args:
            form_letters: List of form letters to retrieve (e.g., ["M", "N"]).
                         If None, returns all ideas forms M-Q.

        Returns:
            List of form data dictionaries.
        """
        if form_letters is None:
            form_letters = self.ideas_forms

        return await self._get_forms_by_categories(form_letters)

    async def get_forms_by_domain(self, domain: str) -> List[Dict[str, Any]]:
        """
        Get forms for a specific educational domain.

        Args:
            domain: Educational domain ("handwriting", "vocabulary", "ideas", "all")

        Returns:
            List of relevant form data.
        """
        if domain == "handwriting":
            return await self.get_handwriting_forms()
        elif domain == "vocabulary":
            return await self.get_vocabulary_forms()
        elif domain == "ideas":
            return await self.get_ideas_forms()
        elif domain == "all":
            handwriting = await self.get_handwriting_forms()
            vocabulary = await self.get_vocabulary_forms()
            ideas = await self.get_ideas_forms()
            return handwriting + vocabulary + ideas
        else:
            # Default to all forms for unknown domains
            return await self.get_forms_by_domain("all")

    async def get_forms_by_query_type(self, query_type: str) -> List[Dict[str, Any]]:
        """
        Get forms relevant to a specific query type.

        Args:
            query_type: Type of handwriting query ("letter_formation", "fine_motor", etc.)

        Returns:
            List of relevant form data.
        """
        # Define which forms are most relevant for each query type
        form_mapping = {
            "letter_formation": ["A", "B", "C", "F", "G"],  # Letter formation and cues
            "fine_motor": ["D", "E", "F"],  # Activities and development
            "spelling": ["B", "C", "G"],  # Phoneme-grapheme connections
            "assessment": ["E", "H"],  # Assessment and progress monitoring
            "posture_grip": ["F", "D"],  # Physical aspects of writing
            "general": self.handwriting_forms  # All forms for general queries
        }

        relevant_letters = form_mapping.get(query_type, self.handwriting_forms)
        return await self.get_handwriting_forms(relevant_letters)

    async def get_letter_specific_content(self, letters: List[str]) -> List[Dict[str, Any]]:
        """
        Get content specifically related to certain letters.

        Args:
            letters: List of letters to find content for (e.g., ["z", "A", "b"])

        Returns:
            List of forms containing relevant letter content.
        """
        # Always include core forms that contain letter formation patterns
        return await self.get_handwriting_forms(["A", "B", "C", "F", "G"])

    async def get_letter_formation_cues(self, letter: str) -> Dict[str, str]:
        """
        Get specific sequence verbal cues for a letter from Form F.
        
        Args:
            letter: The letter to get formation cues for (e.g., "J", "z")
            
        Returns:
            Dictionary with uppercase and lowercase formation cues
        """
        try:
            # Get Form F which contains sequence verbal cues
            form_f = await self.get_handwriting_forms(["F"])
            
            if not form_f:
                return {"uppercase": "Letter formation cues not available", "lowercase": "Letter formation cues not available"}
            
            # Extract the content from Form F
            form_content = form_f[0].get('content', {})
            form_f_data = form_content.get('form_f', {})
            
            uppercase_cues = form_f_data.get('uppercase_letters', {})
            lowercase_cues = form_f_data.get('lowercase_letters', {})
            
            # Get the specific letter cues
            letter_upper = letter.upper()
            letter_lower = letter.lower()
            
            return {
                "uppercase": uppercase_cues.get(letter_upper, f"Formation cues for {letter_upper} not found"),
                "lowercase": lowercase_cues.get(letter_lower, f"Formation cues for {letter_lower} not found")
            }
            
        except Exception as e:
            print(f"❌ Error getting letter formation cues for {letter}: {e}")
            return {"uppercase": "Error retrieving formation cues", "lowercase": "Error retrieving formation cues"}

    async def get_phoneme_gesture(self, sound: str) -> Dict[str, str]:
        """
        Get specific gesture for a phoneme from Form G.
        
        Args:
            sound: The phoneme sound (e.g., "/z/", "/m/", "/s/")
            
        Returns:
            Dictionary with gesture and sound word
        """
        try:
            # Get Form G which contains phoneme gestures
            form_g = await self.get_handwriting_forms(["G"])
            
            if not form_g:
                return {"gesture": "Gesture not available", "sound_word": "Sound word not available"}
            
            # Extract the content from Form G
            form_content = form_g[0].get('content', {})
            form_g_data = form_content.get('form_g', {})
            
            # Check different phoneme categories
            consonant_phonemes = form_g_data.get('consonant_phonemes', {})
            short_vowel_phonemes = form_g_data.get('short_vowel_phonemes', {})
            long_vowel_phonemes = form_g_data.get('long_vowel_phonemes', {})
            digraphs_blends = form_g_data.get('digraphs_blends', {})
            r_controlled_vowels = form_g_data.get('r_controlled_vowels', {})
            
            # Search for the sound in all categories
            sound_data = None
            if sound in consonant_phonemes:
                sound_data = consonant_phonemes[sound]
            elif sound in short_vowel_phonemes:
                sound_data = short_vowel_phonemes[sound]
            elif sound in long_vowel_phonemes:
                sound_data = long_vowel_phonemes[sound]
            elif sound in digraphs_blends:
                sound_data = digraphs_blends[sound]
            elif sound in r_controlled_vowels:
                sound_data = r_controlled_vowels[sound]
            
            if sound_data:
                return {
                    "gesture": sound_data.get('gesture', f"Gesture for {sound} not found"),
                    "sound_word": sound_data.get('sound', f"Sound word for {sound} not found")
                }
            else:
                return {"gesture": f"Gesture for {sound} not found", "sound_word": f"Sound word for {sound} not found"}
                
        except Exception as e:
            print(f"❌ Error getting phoneme gesture for {sound}: {e}")
            return {"gesture": "Error retrieving gesture", "sound_word": "Error retrieving sound word"}

    async def get_ability_modifications(self, activity: str, level: str) -> List[Dict[str, str]]:
        """
        Get specific modifications from Form H for different ability levels.
        
        Args:
            activity: The activity name (e.g., "Sound Sparks", "Magic Finger Write")
            level: The ability level ("low", "middle", "high")
            
        Returns:
            List of modification dictionaries
        """
        try:
            # Get Form H which contains modification examples
            form_h = await self.get_handwriting_forms(["H"])
            
            if not form_h:
                return [{"modification": "Modifications not available", "level": level}]
            
            # Extract the content from Form H
            form_content = form_h[0].get('content', {})
            form_h_data = form_content.get('form_h', {})
            
            # Get ability level modifications
            ability_modifications = form_h_data.get('ability_level_modifications', {})
            
            # Look for the specific activity and level
            modifications = []
            
            # Check if there's a specific example for this activity and level
            if 'example_high_level' in ability_modifications:
                example = ability_modifications['example_high_level']
                if level == "high" and activity.lower() in example.get('activity', '').lower():
                    modifications.append({
                        "modification": example.get('description', ''),
                        "level": level,
                        "activity": example.get('activity', '')
                    })
            
            # If no specific match, return general guidance
            if not modifications:
                modifications.append({
                    "modification": f"Modify {activity} for {level} level students - adjust pace, complexity, and support level",
                    "level": level,
                    "activity": activity
                })
            
            return modifications
            
        except Exception as e:
            print(f"❌ Error getting ability modifications for {activity} at {level} level: {e}")
            return [{"modification": "Error retrieving modifications", "level": level}]

    async def get_handwriting_activities_by_level(self, level: str) -> List[Dict[str, str]]:
        """
        Get handwriting activities from Form D by ability level.
        
        Args:
            level: The ability level ("low", "middle", "high")
            
        Returns:
            List of activity dictionaries
        """
        try:
            # Get Form D which contains suggested activities
            form_d = await self.get_handwriting_forms(["D"])
            
            if not form_d:
                return [{"name": "Activities not available", "description": "No activities found"}]
            
            # Extract the content from Form D
            form_content = form_d[0].get('content', {})
            form_d_data = form_content.get('form_d', {})
            
            activities = []
            
            # Get activities by level from adaptation_3_activities
            adaptation_3 = form_d_data.get('adaptation_3_activities', {})
            
            if level == "low":
                level_activities = adaptation_3.get('level_1_motor_foundation', [])
            elif level == "middle":
                level_activities = adaptation_3.get('level_2_guided_formation', [])
            elif level == "high":
                level_activities = adaptation_3.get('level_3_semi_independent', [])
            else:
                level_activities = []
            
            for activity in level_activities:
                activities.append({
                    "name": activity.get('name', 'Unknown Activity'),
                    "description": activity.get('description', 'No description available'),
                    "level": level
                })
            
            return activities
            
        except Exception as e:
            print(f"❌ Error getting handwriting activities for {level} level: {e}")
            return [{"name": "Error retrieving activities", "description": "Error occurred", "level": level}]

    def build_context_string(self, forms: List[Dict[str, Any]], max_length: int = 4000) -> str:
        """
        Build a context string from form content for LLM processing.

        Args:
            forms: List of form data dictionaries
            max_length: Maximum length of the context string

        Returns:
            Formatted context string for the LLM
        """
        if not forms:
            return "No relevant educational forms found."

        context_parts = []
        current_length = 0

        for form in forms:
            form_letter = form.get('form_letter', form.get('category', 'Unknown'))
            content = form.get('content', {})

            # Build form summary
            form_summary = f"\n=== FORM {form_letter} ===\n"

            # Add title if available
            title = form.get('title')
            if title:
                form_summary += f"Title: {title}\n"

            # Add content summary (handling various content structures)
            if isinstance(content, dict):
                # Process content keys
                for key, value in list(content.items())[:5]:  # Limit to first 5 keys
                    if isinstance(value, dict) and 'title' in value:
                        form_summary += f"\n{key.upper()}:\n  Title: {value['title']}\n"
                        if 'description' in value:
                            form_summary += f"  {value['description'][:200]}...\n"
                    elif isinstance(value, str):
                        form_summary += f"\n{key}: {value[:200]}...\n"
                    elif isinstance(value, list) and value:
                        form_summary += f"\n{key}: {len(value)} items\n"

            # Check if adding this form would exceed max length
            if current_length + len(form_summary) > max_length:
                # Add truncation notice
                context_parts.append("\n[Additional forms truncated to stay within context limits]")
                break

            context_parts.append(form_summary)
            current_length += len(form_summary)

        return "\n".join(context_parts)

    def _search_forms_for_keyword_sync(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Synchronous helper to search all forms for keyword.
        Used internally by async wrapper.

        Args:
            keyword: Keyword to search for (case-insensitive)

        Returns:
            List of forms containing the keyword
        """
        try:
            # Scan DynamoDB table for forms
            response = self.table.scan(
                FilterExpression=Attr('type').eq('Form')
            )

            matching_forms = []
            keyword_lower = keyword.lower()

            for item in response.get('Items', []):
                # Convert form to string and search
                form_str = json.dumps(item.get('content', {})).lower()
                if keyword_lower in form_str:
                    matching_forms.append({
                        'form_id': item.get('form_id'),
                        'form_letter': item.get('category'),
                        'category': item.get('category'),
                        'title': item.get('title'),
                        'content': item.get('content', {})
                    })

            return matching_forms

        except Exception as e:
            print(f"❌ Error searching forms: {e}")
            return []

    async def search_forms_for_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Search all forms for content containing a specific keyword.
        Runs synchronous DynamoDB scan in thread pool to avoid blocking event loop.

        Args:
            keyword: Keyword to search for (case-insensitive)

        Returns:
            List of forms containing the keyword
        """
        return await asyncio.to_thread(self._search_forms_for_keyword_sync, keyword)

    def _get_standards_by_grade_sync(self, grade_level: str) -> Dict[str, Any]:
        """
        Synchronous helper to get educational standards for a specific grade level.
        Used internally by async wrapper.

        Args:
            grade_level: Grade level ("prek", "kindergarten", "1st_grade")

        Returns:
            Standards data for the specified grade level
        """
        try:
            # Normalize grade level
            grade_map = {
                "prek": "Pre-K",
                "pre-k": "Pre-K",
                "pre_k": "Pre-K",
                "kindergarten": "Kindergarten",
                "k": "Kindergarten",
                "1st_grade": "1st Grade",
                "first_grade": "1st Grade",
                "1st": "1st Grade"
            }

            normalized_grade = grade_map.get(grade_level.lower(), grade_level)

            # Query DynamoDB for standards
            response = self.table.query(
                IndexName='TypeIndex',
                KeyConditionExpression='#type = :type_val',
                FilterExpression='grade = :grade',
                ExpressionAttributeNames={'#type': 'type'},
                ExpressionAttributeValues={
                    ':type_val': 'Standard',
                    ':grade': normalized_grade
                }
            )

            items = response.get('Items', [])

            if not items:
                print(f"⚠️ No standards found for grade: {normalized_grade}")
                return {}

            # Extract standards data
            standards_item = items[0]

            # Extract handwriting standards specifically
            handwriting_standards = []
            domains = standards_item.get('content', {}).get('domains', {})

            if 'foundations' in domains:
                foundations = domains['foundations']
                if 'big_ideas' in foundations and 'handwriting' in foundations['big_ideas']:
                    hw_data = foundations['big_ideas']['handwriting']
                    if 'standards' in hw_data:
                        for standard_key, standard_val in hw_data['standards'].items():
                            if isinstance(standard_val, dict):
                                desc = standard_val.get('description', '')
                                sub_standards = standard_val.get('sub_standards', {})
                                handwriting_standards.append({
                                    'code': standard_val.get('code', ''),
                                    'title': standard_val.get('title', ''),
                                    'description': desc,
                                    'sub_standards': sub_standards
                                })

            return {
                'grade': normalized_grade,
                'handwriting_standards': handwriting_standards,
                'full_data': standards_item.get('content', {})
            }

        except Exception as e:
            print(f"❌ Error retrieving standards for grade {grade_level}: {e}")
            return {}

    async def get_standards_by_grade(self, grade_level: str) -> Dict[str, Any]:
        """
        Get educational standards for a specific grade level.
        Runs synchronous DynamoDB query in thread pool to avoid blocking event loop.

        Args:
            grade_level: Grade level ("prek", "kindergarten", "1st_grade")

        Returns:
            Standards data for the specified grade level
        """
        return await asyncio.to_thread(self._get_standards_by_grade_sync, grade_level)

    def get_cache_status(self) -> Dict[str, Any]:
        """
        Get status of the forms in DynamoDB for debugging.

        Returns:
            Form status information
        """
        try:
            # Count forms by category
            response = self.table.scan(
                FilterExpression=Attr('type').eq('Form')
            )

            items = response.get('Items', [])
            categories_found = [item.get('category') for item in items]

            return {
                "total_forms_loaded": len(items),
                "handwriting_forms_loaded": [c for c in categories_found if c in self.handwriting_forms],
                "vocabulary_forms_loaded": [c for c in categories_found if c in self.vocabulary_forms],
                "ideas_forms_loaded": [c for c in categories_found if c in self.ideas_forms],
                "all_categories": sorted(set(categories_found))
            }

        except Exception as e:
            print(f"❌ Error getting cache status: {e}")
            return {
                "error": str(e),
                "total_forms_loaded": 0
            }


# Global instance for use throughout the application
form_retrieval_service = FormRetrievalService()