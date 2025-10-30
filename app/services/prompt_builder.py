from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.utils.form_loader import get_form_loader


class PromptBuilder:
    def __init__(self, task_name: str, params: Dict[str, Any]) -> None:
        self.task_name = task_name
        self.params = params
        self.metadata: Dict[str, Any] = {
            "forms_used": [],
            "sections_included": [],
            "letters_included": [],
            "token_estimate": 0,
            "truncations": [],
        }

    def build_prompt(self) -> str:
        loader = get_form_loader()
        forms = loader.get_forms_for_task(self.task_name, self.params.get("query_type"))
        self.metadata["forms_used"] = list(forms.keys())

        if self.task_name == "Handwriting":
            return self._build_handwriting_prompt(forms)
        if self.task_name == "Vocabulary":
            return self._build_vocabulary_prompt(forms)
        if self.task_name == "Idea Generation":
            return self._build_idea_generation_prompt(forms)
        raise ValueError(f"Unknown task: {self.task_name}")

    def _build_handwriting_prompt(self, forms: Dict[str, Dict[str, Any]]) -> str:
        grade = self.params.get("target_grade", "")
        query_type = self.params.get("query_type", "")
        target_letters = (self.params.get("target_letters") or "").strip()
        if target_letters:
            letters = [l.strip() for l in target_letters.split(",") if l.strip()]
            self.metadata["letters_included"] = letters

        sections = self._get_handwriting_sections(query_type)
        self.metadata["sections_included"] = sections

        parts: List[str] = []
        parts.append("You are an expert early literacy teacher. Generate a detailed lesson.")
        parts.append(f"Grade: {grade}\nFocus: {query_type}")
        if target_letters:
            parts.append(f"Target letters: {target_letters}")

        # Structure and formatting
        parts.append("\n[Lesson Structure]\n")
        parts.append(self._extract(forms.get("Form-B"), ["structure", "formatting"]))

        # Scaffolded verbs (Form-A)
        parts.append("\n[Scaffolded Verbs]\n")
        parts.append(self._extract(forms.get("Form-A")))

        # Letter-specific info (Form-F, Form-G)
        if target_letters:
            parts.append("\n[Letter Cues and Gestures]\n")
            parts.append(self._get_letter_data(target_letters, forms.get("Form-F"), forms.get("Form-G")))

        # Scripted template (Form-C) and Activity options (Form-D), filtered
        parts.append("\n[Scripted Template]\n")
        parts.append(self._filter_sections(forms.get("Form-C"), sections))

        if "Form-D" in forms:
            parts.append("\n[Activity Options]\n")
            parts.append(self._filter_sections(forms.get("Form-D"), sections, top_k=3))

        # Example lesson (if provided)
        example = forms.get("Example_Handwriting_Spelling") or forms.get("Example_Handwriting&Spelling")
        if example:
            parts.append("\n[Example Lesson (Reference)]\n")
            parts.append(self._truncate(self._stringify(example), max_chars=3000, tag="example"))

        parts.append("\n[Instructions]\nOutput a complete, coherent lesson following the structure and formatting.")

        prompt = "\n".join(p for p in parts if p)
        self.metadata["token_estimate"] = len(prompt)
        return prompt

    def _build_vocabulary_prompt(self, forms: Dict[str, Dict[str, Any]]) -> str:
        grade = self.params.get("target_grade", "")
        query_type = self.params.get("query_type", "")
        vocab = self.params.get("target_vocabulary", "")
        genre = self.params.get("target_genre", "")

        sections = ["review_connect", "model_explain_engage", "guided_practice", "application"]
        self.metadata["sections_included"] = sections

        parts: List[str] = []
        parts.append("You are an expert early literacy teacher. Generate a vocabulary-focused lesson.")
        parts.append(f"Grade: {grade}\nFocus: {query_type}\nTarget vocabulary: {vocab}\nGenre: {genre}")
        parts.append("\n[Structure & Formatting]\n")
        parts.append(self._extract(forms.get("Form-A")))
        parts.append(self._extract(forms.get("Form-K")))
        parts.append(self._extract(forms.get("Form-L")))
        parts.append("\n[Instructions]\nOutput a complete, coherent lesson following the structure.")
        prompt = "\n".join(p for p in parts if p)
        self.metadata["token_estimate"] = len(prompt)
        return prompt

    def _build_idea_generation_prompt(self, forms: Dict[str, Dict[str, Any]]) -> str:
        grade = self.params.get("target_grade", "")
        query_type = self.params.get("query_type", "")
        genre = self.params.get("target_genre", "")
        topic = self.params.get("target_topic", "")

        sections = ["review_connect", "model_explain_engage", "guided_practice", "application"]
        self.metadata["sections_included"] = sections

        parts: List[str] = []
        parts.append("You are an expert early literacy teacher. Generate an idea-generation lesson.")
        parts.append(f"Grade: {grade}\nFocus: {query_type}\nGenre: {genre}\nTopic: {topic}")
        parts.append("\n[Structure & Formatting]\n")
        parts.append(self._extract(forms.get("Form-A")))
        parts.append(self._extract(forms.get("FORM-P")))
        parts.append("\n[Instructions]\nOutput a complete, coherent lesson following the structure.")
        prompt = "\n".join(p for p in parts if p)
        self.metadata["token_estimate"] = len(prompt)
        return prompt

    def get_metadata(self) -> Dict[str, Any]:
        return self.metadata

    @staticmethod
    def _get_handwriting_sections(query_type: str) -> List[str]:
        if query_type == "letter formation":
            return [
                "review_connect",
                "model_explain_engage",
                "guided_practice",
                "application",
                "wrap_up",
            ]
        if query_type in {"fine motor", "spelling"}:
            return ["review_connect", "model_explain_engage", "guided_practice", "application"]
        return ["review_connect", "model_explain_engage", "guided_practice", "application", "wrap_up"]

    @staticmethod
    def _extract(data: Optional[Dict[str, Any]], keys: Optional[List[str]] = None) -> str:
        if not data:
            return ""
        if not keys:
            return PromptBuilder._truncate(PromptBuilder._stringify(data), 3000, tag="generic")
        selected = {k: data.get(k) for k in keys if k in data}
        return PromptBuilder._truncate(PromptBuilder._stringify(selected), 3000, tag="selected")

    @staticmethod
    def _filter_sections(data: Optional[Dict[str, Any]], sections: List[str], top_k: int = 0) -> str:
        if not data:
            return ""
        collected: Dict[str, Any] = {}
        for s in sections:
            val = data.get(s)
            if val is None:
                continue
            if isinstance(val, list) and top_k > 0:
                collected[s] = val[:top_k]
            else:
                collected[s] = val
        return PromptBuilder._truncate(PromptBuilder._stringify(collected), 4000, tag="sections")

    @staticmethod
    def _get_letter_data(target_letters: str, form_f: Optional[Dict[str, Any]], form_g: Optional[Dict[str, Any]]) -> str:
        letters = [l.strip() for l in target_letters.split(",") if l.strip()]
        result: Dict[str, Any] = {}
        for letter in letters:
            cues = (form_f or {}).get(letter) or (form_f or {}).get(letter.lower())
            gestures = (form_g or {}).get(letter) or (form_g or {}).get(letter.lower())
            bundle = {}
            if cues:
                bundle["sequence_verbal_cues"] = cues
            if gestures:
                bundle["phoneme_gestures"] = gestures
            if bundle:
                result[letter] = bundle
        return PromptBuilder._truncate(PromptBuilder._stringify(result), 2000, tag="letters")

    @staticmethod
    def _truncate(text: str, max_chars: int, tag: str) -> str:
        if len(text) <= max_chars:
            return text
        return text[: max(0, max_chars - 100)] + f"\n... [truncated {tag}]"

    @staticmethod
    def _stringify(obj: Any) -> str:
        try:
            import json as _json

            return _json.dumps(obj, ensure_ascii=False, indent=2)
        except Exception:
            return str(obj)


