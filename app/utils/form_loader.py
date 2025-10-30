"""
Utility for loading and caching JSON form templates.
Resolves the forms directory from FORMS_DIR env var or defaults to backend/data/Forms_Json.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class FormLoader:
    """Singleton class for loading and caching JSON form templates."""

    _instance: Optional["FormLoader"] = None
    _forms_cache: Dict[str, Dict[str, Any]]

    def __new__(cls) -> "FormLoader":
        if cls._instance is None:
            cls._instance = super(FormLoader, cls).__new__(cls)
            cls._instance._forms_cache = {}
        return cls._instance

    @property
    def forms_dir(self) -> Path:
        """Resolve forms directory from env or default to backend/data/Forms_Json."""
        project_root = Path(__file__).resolve().parents[2]
        # project_root -> /.../edtech-chatbot
        default_dir = project_root / "backend" / "data" / "Forms_Json"
        env_dir = os.getenv("FORMS_DIR")
        return Path(env_dir).resolve() if env_dir else default_dir.resolve()

    def load_form(self, form_name: str) -> Dict[str, Any]:
        """Load a specific form by name with caching."""
        if form_name in self._forms_cache:
            return self._forms_cache[form_name]

        form_path = self.forms_dir / f"{form_name}.json"

        if not form_path.exists():
            raise FileNotFoundError(f"Form file not found: {form_path}")

        with open(form_path, "r", encoding="utf-8") as f:
            form_data = json.load(f)

        self._forms_cache[form_name] = form_data
        return form_data

    def load_multiple_forms(self, form_names: list[str]) -> Dict[str, Dict[str, Any]]:
        """Load multiple forms at once."""
        return {name: self.load_form(name) for name in form_names}

    def get_forms_for_task(self, task_type: str, query_type: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """Get all relevant forms for a specific task and query type."""
        if task_type == "Handwriting":
            return self._get_handwriting_forms(query_type)
        if task_type == "Vocabulary":
            return self._get_vocabulary_forms(query_type)
        if task_type == "Idea Generation":
            return self._get_idea_generation_forms(query_type)
        raise ValueError(f"Unknown task type: {task_type}")

    def _get_handwriting_forms(self, query_type: Optional[str]) -> Dict[str, Dict[str, Any]]:
        """Get forms specific to handwriting lessons."""
        base_forms = ["Form-A", "Form-B", "Form-C", "Form-F", "Form-G", "Form-H"]

        if query_type == "letter formation":
            forms = base_forms + ["Form-D", "Example_Handwriting_Spelling"]
        elif query_type == "fine motor":
            forms = base_forms + ["Form-D"]
        elif query_type == "spelling":
            forms = base_forms + ["Form-D"]
        elif query_type == "assessment":
            forms = base_forms + ["Example_Handwriting_Spelling"]
        else:
            # general
            forms = base_forms + ["Form-D", "Example_Handwriting_Spelling"]

        return self.load_multiple_forms(forms)

    def _get_vocabulary_forms(self, query_type: Optional[str]) -> Dict[str, Dict[str, Any]]:
        """Get forms specific to vocabulary lessons."""
        return self.load_multiple_forms(["Form-A", "Form-K", "Form-L"])

    def _get_idea_generation_forms(self, query_type: Optional[str]) -> Dict[str, Dict[str, Any]]:
        """Get forms specific to idea generation lessons."""
        return self.load_multiple_forms(["Form-A", "FORM-P"])

    def clear_cache(self) -> None:
        """Clear the forms cache."""
        self._forms_cache.clear()


def get_form_loader() -> FormLoader:
    """Get the FormLoader singleton instance."""
    return FormLoader()


