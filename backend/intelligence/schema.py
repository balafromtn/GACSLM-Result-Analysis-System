"""
schema.py — Dynamic academic dataset schema discovery and validation.
"""

from typing import Any
import re


def roman_to_int(roman: str) -> int:
    """Convert a Roman numeral string (e.g. 'IV') to an integer (4)."""
    roman_values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    roman = str(roman).strip().upper()
    total = 0
    prev_value = 0
    for char in reversed(roman):
        if char not in roman_values:
            continue
        val = roman_values[char]
        if val < prev_value:
            total -= val
        else:
            total += val
        prev_value = val
    return total if total > 0 else 0


class AcademicSchema:
    """
    Dynamically inspects and represents the schema of the uploaded student exam dataset.
    Exposes validated metadata, column types, and subject aliases.
    """

    ALLOWED_OPERATORS = {"==", "!=", ">", ">=", "<", "<=", "in", "contains", "between"}
    ALLOWED_AGGREGATIONS = {"count", "sum", "mean", "median", "min", "max", "pass_percentage", "fail_percentage"}
    BASE_NUMERIC_FIELDS = {"total", "rank", "passed_core_count", "failed_core_count", "absent_core_count"}
    BASE_TEXT_FIELDS = {"name", "register_no", "gender", "community"}
    BASE_BOOLEAN_FIELDS = {"all_core_passed", "has_numeric_mark"}

    def __init__(self, raw_results: list[dict]):
        self.raw_results = raw_results or []
        self.degree_branch = "Unknown"
        self.exam_month_year = "Unknown"
        self.current_semester_str = ""
        self.current_semester_int = 0
        self.core_subjects: dict[str, str] = {}    # {code: title}
        self.arrear_subjects: dict[str, str] = {}  # {code: title}
        self.subject_aliases: dict[str, str] = {}  # {normalized_keyword: code}
        self.valid_fields: set[str] = set()
        self.student_count = len(self.raw_results)
        self.available_genders: set[str] = set()
        self.available_communities: set[str] = set()

        self._discover_schema()

    def _discover_schema(self):
        if not self.raw_results:
            return

        # 1. Discover current semester
        max_sem_val = 0
        for r in self.raw_results:
            if r.get("degree_branch") and r["degree_branch"] != "UNKNOWN":
                self.degree_branch = r["degree_branch"]
            if r.get("exam_month_year") and r["exam_month_year"] != "UNKNOWN":
                self.exam_month_year = r["exam_month_year"]

            gender = str(r.get("gender", "")).strip().capitalize()
            if gender and gender != "Unknown":
                self.available_genders.add(gender)

            comm = str(r.get("community", "")).strip().upper()
            if comm and comm != "UNKNOWN":
                self.available_communities.add(comm)

            for subj in r.get("subjects", []):
                sem_str = subj.get("semester", "")
                sem_val = roman_to_int(sem_str)
                if sem_val > max_sem_val:
                    max_sem_val = sem_val
                    self.current_semester_str = sem_str

        self.current_semester_int = max_sem_val

        # 2. Categorize Core vs Arrear subjects
        for r in self.raw_results:
            for subj in r.get("subjects", []):
                code = str(subj.get("code", "")).strip()
                title = str(subj.get("title", "")).strip()
                if not code:
                    continue

                sem_val = roman_to_int(subj.get("semester", ""))
                if sem_val == max_sem_val:
                    if code not in self.core_subjects:
                        self.core_subjects[code] = title
                elif sem_val > 0:
                    if code not in self.arrear_subjects:
                        self.arrear_subjects[code] = title

        # 3. Build Subject Aliases for Natural Language Recognition
        all_subjects = {**self.core_subjects, **self.arrear_subjects}
        for code, title in all_subjects.items():
            # Match exact code (case-insensitive)
            self.subject_aliases[code.lower()] = code

            # Match clean title words and keywords
            clean_title = re.sub(r'[^a-zA-Z0-9\s]', ' ', title).lower()
            words = [w for w in clean_title.split() if len(w) > 2 and w not in ["course", "core", "foundation", "allied", "practical", "skill", "enhancement"]]

            self.subject_aliases[clean_title] = code
            for word in words:
                if word not in self.subject_aliases:
                    self.subject_aliases[word] = code

            # Explicit common nicknames with theory vs lab differentiation
            is_lab = ("lab" in clean_title or "practical" in clean_title)

            if "java" in clean_title:
                if is_lab:
                    self.subject_aliases["java lab"] = code
                    self.subject_aliases["java practical"] = code
                else:
                    self.subject_aliases["java"] = code
                    self.subject_aliases["java programming"] = code

            if "statistics" in clean_title or "mathematical statistics" in clean_title:
                if is_lab:
                    self.subject_aliases["statistics practical"] = code
                    self.subject_aliases["stats practical"] = code
                    self.subject_aliases["statistics lab"] = code
                else:
                    self.subject_aliases["statistics"] = code
                    self.subject_aliases["stats"] = code
            if "excel" in clean_title:
                self.subject_aliases["excel"] = code
            if "human rights" in clean_title:
                self.subject_aliases["human rights"] = code
            if "ui" in clean_title or "ux" in clean_title or "design" in clean_title:
                self.subject_aliases["ui"] = code
                self.subject_aliases["ux"] = code
                self.subject_aliases["design"] = code

        # 4. Construct complete set of valid query fields
        self.valid_fields = set(self.BASE_NUMERIC_FIELDS) | set(self.BASE_TEXT_FIELDS) | set(self.BASE_BOOLEAN_FIELDS)
        for code in all_subjects:
            self.valid_fields.add(f"marks.{code}")

    def resolve_subject(self, text: str) -> str | None:
        """Resolve a subject code or name substring from user input to an exact course code."""
        if not text:
            return None
        clean = text.strip().lower()

        # Direct code match
        if clean in self.subject_aliases:
            return self.subject_aliases[clean]

        # Substring in subject aliases
        for alias, code in self.subject_aliases.items():
            if alias in clean or clean in alias:
                return code

        # Substring in title or code
        all_subjects = {**self.core_subjects, **self.arrear_subjects}
        for code, title in all_subjects.items():
            if clean in code.lower() or clean in title.lower():
                return code

        return None

    def validate_field(self, field: str) -> bool:
        """Verify if a field is permitted in the analytical query plan."""
        return field in self.valid_fields

    def to_metadata_dict(self) -> dict[str, Any]:
        """Return a compact JSON-serializable representation of the dataset schema."""
        return {
            "degree_branch": self.degree_branch,
            "exam_month_year": self.exam_month_year,
            "current_semester": self.current_semester_str,
            "total_students": self.student_count,
            "available_genders": sorted(list(self.available_genders)),
            "available_communities": sorted(list(self.available_communities)),
            "core_subjects": [{"code": c, "title": t} for c, t in self.core_subjects.items()],
            "arrear_subjects": [{"code": c, "title": t} for c, t in self.arrear_subjects.items()],
            "filterable_fields": sorted(list(self.valid_fields)),
            "allowed_operations": [
                "retrieval", "filter", "aggregation", "group_by",
                "ranking", "comparison", "conditional", "distribution", "semester_comparison"
            ]
        }
