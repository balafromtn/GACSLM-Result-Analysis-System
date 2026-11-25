"""
memory.py — Conversation context and entity reference resolution.

Maintains a lightweight, bounded conversation memory to support natural follow-up
questions without sending large chat history to the LLM.
"""

from collections import deque
from typing import Any
import re
from .schema import AcademicSchema


class ConversationMemory:
    """
    Tracks referenced entities, subjects, and analytical intents to resolve
    follow-up queries like "What about the girls?", "Compare their marks", or "Who topped in it?".
    """

    def __init__(self, max_history: int = 4):
        self.max_history = max_history
        self.history: deque[dict[str, str]] = deque(maxlen=max_history)
        self.last_query_type: str | None = None
        self.last_subject_code: str | None = None
        self.last_student_name: str | None = None
        self.last_student_reg: str | None = None
        self.last_gender: str | None = None
        self.last_verified_summary: str | None = None

    def record_turn(
        self,
        user_query: str,
        assistant_response: str,
        query_type: str | None = None,
        subject_code: str | None = None,
        student_name: str | None = None,
        student_reg: str | None = None,
        gender: str | None = None,
    ):
        """Record an interaction turn and update context references."""
        self.history.append({"role": "user", "content": user_query})
        self.history.append({"role": "assistant", "content": assistant_response})

        if query_type:
            self.last_query_type = query_type
        if subject_code:
            self.last_subject_code = subject_code
        if student_name:
            self.last_student_name = student_name
        if student_reg:
            self.last_student_reg = student_reg
        if gender:
            self.last_gender = gender

    def resolve_follow_up(self, query: str, schema: AcademicSchema) -> tuple[str, dict[str, Any]]:
        """
        Detects follow-up or pronoun-based queries and rewrites or augments them using active context.
        Returns: (resolved_query, context_hints)
        """
        q_lower = query.strip().lower()
        hints: dict[str, Any] = {}

        female_pattern = bool(re.search(r'\b(girls|female|women|girl)\b', q_lower))
        male_pattern = bool(re.search(r'\b(boys|male|men|boy)\b', q_lower))

        # 0. Comparison check: "Compare boys and girls", "Compare their marks", etc.
        is_comparison = any(k in q_lower for k in ["compare", "comparison", "difference", "vs", "versus", "between"])
        if is_comparison:
            if (female_pattern and male_pattern) or any(k in q_lower for k in ["both", "their", "gender"]):
                return "Compare male vs female performance", {"compare_target": "gender"}
            return query, hints

        # 1. Single Gender follow-up ("What about the girls?", "and boys?", "female students?")
        if (female_pattern ^ male_pattern) and ("what about" in q_lower or "how about" in q_lower or "and " in q_lower or len(q_lower.split()) <= 4):
            target_gender = "Female" if female_pattern else "Male"
            hints["gender"] = target_gender
            if self.last_query_type == "pass_percentage":
                resolved = f"What is the pass percentage for {target_gender.lower()} students?"
                return resolved, hints
            elif self.last_query_type == "failed_list":
                resolved = f"Which {target_gender.lower()} students failed in subjects?"
                return resolved, hints
            elif self.last_query_type == "ranking":
                resolved = f"Top {target_gender.lower()} students"
                return resolved, hints
            else:
                # Default to gender topper/performance (e.g. if last was topper, comparison, or general)
                resolved = f"Who is the {target_gender.lower()} class topper?"
                return resolved, hints

        # 2. Subject reference ("Who topped in it?", "What is its pass percentage?", "Average in it")
        if re.search(r'\b(in it|for it|in that subject|for that course)\b', q_lower):
            if self.last_subject_code:
                subj_title = schema.core_subjects.get(self.last_subject_code) or schema.arrear_subjects.get(self.last_subject_code, self.last_subject_code)
                resolved = q_lower.replace("in it", f"in {self.last_subject_code}").replace("for it", f"for {self.last_subject_code}")
                hints["subject_code"] = self.last_subject_code
                return resolved, hints

        # 3. Student pronoun reference ("What about his marks?", "Her rank?", "How did he perform?")
        if re.search(r'\b(his|her|he|she)\b', q_lower):
            if self.last_student_reg or self.last_student_name:
                ident = self.last_student_reg or self.last_student_name
                resolved = f"{query} for student {ident}"
                hints["student_reg"] = self.last_student_reg
                return resolved, hints

        # 4. Comparison follow-up ("Compare their marks", "Compare both", "Compare them")
        if any(k in q_lower for k in ["compare their", "compare them", "compare both"]):
            if self.last_gender:
                resolved = "Compare male vs female performance"
                hints["compare_target"] = "gender"
                return resolved, hints

        return query, hints

    def get_compact_history(self) -> list[dict[str, str]]:
        """Return a lightweight history for LLM context without bloating tokens."""
        return list(self.history)

    def clear(self):
        """Reset conversation state when a new dataset is uploaded or session resets."""
        self.history.clear()
        self.last_query_type = None
        self.last_subject_code = None
        self.last_student_name = None
        self.last_student_reg = None
        self.last_gender = None
        self.last_verified_summary = None
