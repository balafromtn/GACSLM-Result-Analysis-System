"""
planner.py — Schema-aware Query Planner and Intent Classifier.

Maps natural language questions to typed, validated QueryPlan instances using:
  1. Fast deterministic recognition for high-frequency academic questions (< 1ms).
  2. Bounded contextual resolution with conversation memory.
  3. Safe fallback to general analytical aggregation.
"""

from typing import Any
import re
from .schema import AcademicSchema
from .engine import QueryPlan, FilterCondition, AggregationSpec
from .memory import ConversationMemory


class QueryPlanner:
    """Plans academic analysis queries into safe, structured QueryPlans."""

    WORD_TO_NUM = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
    }

    def plan_query(
        self,
        query: str,
        schema: AcademicSchema,
        memory: ConversationMemory | None = None
    ) -> tuple[QueryPlan, bool, str]:
        """
        Parses a query into a (QueryPlan, is_direct_path, intent_name).
        is_direct_path indicates if Path A (deterministic instant answer) can be used.
        """
        # 1. Follow-up resolution if memory exists
        resolved_query = query
        hints: dict[str, Any] = {}
        if memory:
            resolved_query, hints = memory.resolve_follow_up(query, schema)

        q_lower = resolved_query.strip().lower()

        # Check for open-ended requests that REQUIRE LLM pedagogical explanation (Path B)
        requires_llm = any(k in q_lower for k in [
            "recommend", "suggestion", "improve", "advice", "pedagogical",
            "why", "how to help", "weakness", "observation", "insight", "analyze and suggest"
        ])

        # ── Intent 1: Topper / Top Scorer Queries ──────────────────────────
        if any(k in q_lower for k in ["topper", "rank 1", "first rank", "highest mark", "highest score", "top scorer"]):
            # Check if for a specific subject
            subj_code = schema.resolve_subject(q_lower)
            # Check gender filter
            gender_filter = None
            if re.search(r'\b(female|girl|women)\b', q_lower) or hints.get("gender") == "Female":
                gender_filter = FilterCondition(field="gender", op="==", val="Female")
            elif re.search(r'\b(male|boy|men)\b', q_lower) or hints.get("gender") == "Male":
                gender_filter = FilterCondition(field="gender", op="==", val="Male")

            filters = [gender_filter] if gender_filter else []

            plan = QueryPlan(
                operation="ranking",
                target="subject" if subj_code else "student",
                filters=filters,
                order_by="total",
                order_dir="desc",
                limit=1,
                subject_code=subj_code,
                meta={"topper_only": True, "query_string": resolved_query}
            )
            return plan, not requires_llm, "topper"

        # ── Intent 2: Top N or Bottom N Ranking ─────────────────────────────
        top_n_match = re.search(r'\b(top|first|best)\s*(\d+|one|two|three|four|five|ten)\b', q_lower)
        bottom_n_match = re.search(r'\b(bottom|last|lowest)\s*(\d+|one|two|three|four|five|ten)\b', q_lower)

        if top_n_match or bottom_n_match or "rank" in q_lower or "leaderboard" in q_lower:
            reverse = True
            n_val = 5
            if top_n_match:
                raw_n = top_n_match.group(2)
                n_val = self.WORD_TO_NUM.get(raw_n, int(raw_n) if raw_n.isdigit() else 5)
            elif bottom_n_match:
                raw_n = bottom_n_match.group(2)
                n_val = self.WORD_TO_NUM.get(raw_n, int(raw_n) if raw_n.isdigit() else 5)
                reverse = False

            subj_code = schema.resolve_subject(q_lower)
            gender_filter = None
            if re.search(r'\b(female|girls)\b', q_lower):
                gender_filter = FilterCondition(field="gender", op="==", val="Female")
            elif re.search(r'\b(male|boys)\b', q_lower):
                gender_filter = FilterCondition(field="gender", op="==", val="Male")

            filters = [gender_filter] if gender_filter else []

            plan = QueryPlan(
                operation="ranking",
                target="student",
                filters=filters,
                order_by="total",
                order_dir="desc" if reverse else "asc",
                limit=min(n_val, 25),
                subject_code=subj_code,
                meta={"query_string": resolved_query}
            )
            return plan, not requires_llm, "ranking"

        # ── Intent 3: Failed Students / Arrears Filtering ───────────────────
        if any(k in q_lower for k in ["failed", "fail", "arrear", "backlog", "arrears", "ra"]):
            # Check for threshold e.g. "more than 2 subjects"
            match_gt = re.search(r'(?:more than|greater than|>)\s*(\d+|one|two|three|four|five)\s*subject', q_lower)
            threshold = 1
            if match_gt:
                t_str = match_gt.group(1)
                threshold = self.WORD_TO_NUM.get(t_str, int(t_str) if t_str.isdigit() else 2) + 1
            elif "more than" in q_lower:
                threshold = 3

            # Check if specific subject failure e.g. "who failed in java"
            subj_code = schema.resolve_subject(q_lower)
            filters = []
            if subj_code:
                # Student who did not pass this subject
                filters.append(FilterCondition(field=f"marks.{subj_code}", op="!=", val="-"))
                plan = QueryPlan(
                    operation="retrieval",
                    target="subject",
                    subject_code=subj_code,
                    meta={"query_string": resolved_query}
                )
                return plan, not requires_llm, "subject_fail"

            plan = QueryPlan(
                operation="conditional",
                target="student",
                filters=[FilterCondition(field="failed_core_count", op=">=", val=threshold)],
                limit=15,
                meta={"failed_threshold": threshold, "query_string": resolved_query}
            )
            return plan, not requires_llm, "failed_list"

        # ── Intent 4: Comparisons (Gender, Subjects, Cohorts) ───────────────
        if any(k in q_lower for k in ["compare", "comparison", "difference between", "versus", "vs"]):
            # Check if comparing two subjects
            found_subjects = []
            for token in q_lower.split():
                res_code = schema.resolve_subject(token)
                if res_code and res_code not in found_subjects:
                    found_subjects.append(res_code)

            if len(found_subjects) >= 2:
                plan = QueryPlan(
                    operation="comparison",
                    target="subject",
                    compare_groups=[{"code": found_subjects[0]}, {"code": found_subjects[1]}],
                    meta={"query_string": resolved_query}
                )
                return plan, not requires_llm, "subject_comparison"

            # Default demographic / gender comparison
            plan = QueryPlan(
                operation="comparison",
                target="gender",
                compare_groups=[{"gender": "Male"}, {"gender": "Female"}],
                meta={"query_string": resolved_query}
            )
            return plan, not requires_llm, "gender_comparison"

        # ── Intent 5: Specific Subject Statistics & Pass Rates ─────────────
        resolved_subj = schema.resolve_subject(q_lower)
        if resolved_subj and any(k in q_lower for k in ["subject", "course", "pass", "mark", "average", "stats", "score", "performance"]):
            plan = QueryPlan(
                operation="retrieval",
                target="subject",
                subject_code=resolved_subj,
                meta={"query_string": resolved_query}
            )
            return plan, not requires_llm, "subject_stats"

        # ── Intent 6: Semester / Backlog Analysis ───────────────────────────
        if any(k in q_lower for k in ["semester", "sem comparison", "arrear vs core", "core vs arrear", "backlog pass"]):
            plan = QueryPlan(
                operation="semester_comparison",
                target="class",
                meta={"query_string": resolved_query}
            )
            return plan, not requires_llm, "semester_comparison"

        # ── Intent 7: Performance Distribution / Grade Categories ──────────
        if any(k in q_lower for k in ["distribution", "distinction", "first class", "categories", "bands", "ranges"]):
            plan = QueryPlan(
                operation="distribution",
                target="class",
                meta={"query_string": resolved_query}
            )
            return plan, not requires_llm, "distribution"

        # ── Intent 8: Individual Student Lookup ─────────────────────────────
        # Check if query matches register number pattern (e.g. 24UCS... or digits) or student names
        reg_match = re.search(r'\b\d{2}[a-zA-Z]{3,4}\d{4,6}\b', resolved_query)
        target_name = None
        if not reg_match:
            for s in schema.raw_results:
                s_name = str(s.get("name", "")).strip().lower()
                if len(s_name) > 3 and s_name in q_lower:
                    target_name = s.get("name")
                    break

        if reg_match or target_name:
            search_val = reg_match.group(0) if reg_match else target_name
            plan = QueryPlan(
                operation="retrieval",
                target="student",
                filters=[],
                meta={"query_string": search_val}
            )
            return plan, not requires_llm, "student_lookup"

        # ── Intent 9: Pass Percentage & Overall Class Statistics ───────────
        if any(k in q_lower for k in ["pass percentage", "pass rate", "how many passed", "how is the class performing", "average marks", "summary", "overview"]):
            gender_filter = None
            if re.search(r'\b(female|girls)\b', q_lower):
                gender_filter = FilterCondition(field="gender", op="==", val="Female")
            elif re.search(r'\b(male|boys)\b', q_lower):
                gender_filter = FilterCondition(field="gender", op="==", val="Male")

            filters = [gender_filter] if gender_filter else []

            plan = QueryPlan(
                operation="aggregation",
                target="class",
                filters=filters,
                meta={"query_string": resolved_query}
            )
            return plan, not requires_llm, "pass_percentage"

        # ── Intent 10: General Fallback / Synthesis ────────────────────────
        # For open-ended or pedagogical questions, fetch class-wide aggregation and run Path B
        plan = QueryPlan(
            operation="aggregation",
            target="class",
            meta={"query_string": resolved_query, "open_ended": True}
        )
        return plan, False, "general_synthesis"
