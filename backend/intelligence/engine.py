"""
engine.py — Generic Safe Query Execution Engine for Academic Datasets.

Performs all analytical operations in deterministic Python/Pandas:
  - Retrieval
  - Filtering
  - Aggregation
  - Grouping
  - Ranking (with tie preservation)
  - Group & Subject Comparisons
  - Conditional Analysis
  - Distribution & Bins
  - Semester / Arrear Tracking
"""

from typing import Any
from dataclasses import dataclass, field
import statistics
import time
import pandas as pd
from .schema import AcademicSchema, roman_to_int


@dataclass
class FilterCondition:
    field: str
    op: str
    val: Any


@dataclass
class AggregationSpec:
    field: str
    func: str  # count, sum, mean, median, min, max, pass_percentage, fail_percentage
    alias: str = ""


@dataclass
class QueryPlan:
    operation: str  # retrieval, filter, aggregation, group_by, ranking, comparison, conditional, distribution, semester_comparison
    target: str = "class"  # student, subject, class, gender, community
    filters: list[FilterCondition] = field(default_factory=list)
    group_by: list[str] = field(default_factory=list)
    aggregations: list[AggregationSpec] = field(default_factory=list)
    order_by: str = ""
    order_dir: str = "desc"  # asc or desc
    limit: int = 10
    subject_code: str | None = None
    compare_groups: list[dict[str, Any]] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryResult:
    operation: str
    success: bool
    data: Any
    summary_markdown: str
    verified_facts: list[str]
    execution_time_ms: float
    error: str | None = None


class AcademicQueryEngine:
    """
    Executes validated query plans deterministically against the student result dataset.
    Strictly forbids code execution; uses bounded analytical operations only.
    """

    def __init__(self, raw_results: list[dict]):
        self.raw_results = raw_results or []
        self.schema = AcademicSchema(self.raw_results)
        self.students: list[dict[str, Any]] = []
        self.subject_stats: dict[str, dict[str, Any]] = {}
        self.df: pd.DataFrame = pd.DataFrame()

        self._initialize_dataset()

    def _initialize_dataset(self):
        if not self.raw_results:
            return

        core_codes = sorted(list(self.schema.core_subjects.keys()))
        arrear_codes = sorted(list(self.schema.arrear_subjects.keys()))

        raw_subject_data = {
            code: {"attempted": 0, "passed": 0, "failed": 0, "absent": 0, "not_opted": 0, "marks": []}
            for code in core_codes + arrear_codes
        }

        processed_students = []

        for r in self.raw_results:
            name = str(r.get("name", "UNKNOWN")).strip()
            reg = str(r.get("register_no") or r.get("reg_no") or "UNKNOWN").strip()
            gender = str(r.get("gender", "UNKNOWN")).strip().capitalize()
            community = str(r.get("community", "UNKNOWN")).strip().upper()

            core_marks: dict[str, Any] = {code: "-" for code in core_codes}
            total = 0
            has_numeric_mark = False
            failed_core_subjects = []
            absent_core_subjects = []
            passed_core_subjects = []
            arrear_attempts = []

            for subj in r.get("subjects", []):
                code = str(subj.get("code", "")).strip()
                total_mark = str(subj.get("total", "-")).strip()
                res = str(subj.get("result", "")).strip().upper()

                if code in core_codes:
                    core_marks[code] = total_mark
                    if total_mark in ["-", ""]:
                        raw_subject_data[code]["not_opted"] += 1
                    elif total_mark.upper() in ["AA", "ABSENT", "AB"]:
                        absent_core_subjects.append({
                            "code": code,
                            "title": self.schema.core_subjects.get(code, code)
                        })
                        raw_subject_data[code]["absent"] += 1
                        raw_subject_data[code]["attempted"] += 1
                    else:
                        try:
                            m_val = int(total_mark)
                            total += m_val
                            has_numeric_mark = True
                            raw_subject_data[code]["attempted"] += 1
                            raw_subject_data[code]["marks"].append(m_val)

                            if res == "PASS":
                                passed_core_subjects.append({
                                    "code": code,
                                    "title": self.schema.core_subjects.get(code, code),
                                    "marks": m_val
                                })
                                raw_subject_data[code]["passed"] += 1
                            elif res in ["RA", "FAIL", "F", "U"]:
                                failed_core_subjects.append({
                                    "code": code,
                                    "title": self.schema.core_subjects.get(code, code),
                                    "marks": m_val,
                                    "result": res
                                })
                                raw_subject_data[code]["failed"] += 1
                            else:
                                if m_val >= 40:
                                    passed_core_subjects.append({
                                        "code": code,
                                        "title": self.schema.core_subjects.get(code, code),
                                        "marks": m_val
                                    })
                                    raw_subject_data[code]["passed"] += 1
                                else:
                                    failed_core_subjects.append({
                                        "code": code,
                                        "title": self.schema.core_subjects.get(code, code),
                                        "marks": m_val,
                                        "result": "RA"
                                    })
                                    raw_subject_data[code]["failed"] += 1
                        except ValueError:
                            pass

                elif code in arrear_codes:
                    arrear_attempts.append({
                        "code": code,
                        "title": self.schema.arrear_subjects.get(code, code),
                        "total": total_mark,
                        "result": res
                    })
                    if total_mark.upper() in ["AA", "ABSENT", "AB"]:
                        raw_subject_data[code]["absent"] += 1
                        raw_subject_data[code]["attempted"] += 1
                    elif total_mark not in ["-", ""]:
                        try:
                            m_val = int(total_mark)
                            raw_subject_data[code]["attempted"] += 1
                            raw_subject_data[code]["marks"].append(m_val)
                            if res == "PASS":
                                raw_subject_data[code]["passed"] += 1
                            else:
                                raw_subject_data[code]["failed"] += 1
                        except ValueError:
                            pass

            all_core_passed = (len(failed_core_subjects) == 0 and
                               len(absent_core_subjects) == 0 and
                               len(passed_core_subjects) > 0)

            student_record = {
                "name": name,
                "register_no": reg,
                "gender": gender,
                "community": community,
                "marks": core_marks,
                "total": total,
                "has_numeric_mark": has_numeric_mark,
                "passed_core_count": len(passed_core_subjects),
                "failed_core_subjects": failed_core_subjects,
                "failed_core_count": len(failed_core_subjects),
                "absent_core_subjects": absent_core_subjects,
                "absent_core_count": len(absent_core_subjects),
                "arrear_attempts": arrear_attempts,
                "all_core_passed": all_core_passed,
            }
            # Flatten marks for Pandas dataframe queries: marks.CODE
            for c, m in core_marks.items():
                student_record[f"marks.{c}"] = m

            processed_students.append(student_record)

        # Competition Ranking (Tie Preservation: 1, 1, 3...)
        processed_students.sort(key=lambda s: s["total"], reverse=True)
        for i, s in enumerate(processed_students):
            if i > 0 and s["total"] == processed_students[i - 1]["total"]:
                s["rank"] = processed_students[i - 1]["rank"]
            else:
                s["rank"] = i + 1

        self.students = processed_students
        self.df = pd.DataFrame(processed_students)

        # Compute Subject Statistics
        for code, stats in raw_subject_data.items():
            att = stats["attempted"]
            passed = stats["passed"]
            m_list = stats["marks"]
            avg_m = round(statistics.mean(m_list), 2) if m_list else 0.0
            med_m = round(statistics.median(m_list), 2) if m_list else 0.0
            pass_p = round((passed / att) * 100, 2) if att > 0 else 0.0

            title = self.schema.core_subjects.get(code) or self.schema.arrear_subjects.get(code, code)
            self.subject_stats[code] = {
                "title": title,
                "attempted": att,
                "passed": passed,
                "failed": stats["failed"],
                "absent": stats["absent"],
                "not_opted": stats["not_opted"],
                "pass_percentage": pass_p,
                "fail_percentage": round(100.0 - pass_p, 2) if att > 0 else 0.0,
                "avg_marks": avg_m,
                "median_marks": med_m,
                "max_marks": max(m_list) if m_list else 0,
                "min_marks": min(m_list) if m_list else 0,
            }

    # ── Safe Query Plan Validation ──────────────────────────────────────

    def validate_plan(self, plan: QueryPlan) -> tuple[bool, str]:
        """Verify that the QueryPlan references valid operations, fields, and operators."""
        if not self.students:
            return False, "No student examination records available."

        if plan.operation not in self.schema.to_metadata_dict()["allowed_operations"]:
            return False, f"Unsupported operation '{plan.operation}'."

        for f in plan.filters:
            if not self.schema.validate_field(f.field):
                return False, f"Invalid filter field '{f.field}'."
            if f.op not in self.schema.ALLOWED_OPERATORS:
                return False, f"Unsupported operator '{f.op}'."

        for g in plan.group_by:
            if not self.schema.validate_field(g):
                return False, f"Invalid group_by field '{g}'."

        for a in plan.aggregations:
            if a.func not in self.schema.ALLOWED_AGGREGATIONS:
                return False, f"Unsupported aggregation function '{a.func}'."
            if a.field != "*" and not self.schema.validate_field(a.field):
                return False, f"Invalid aggregation field '{a.field}'."

        if plan.order_by and not self.schema.validate_field(plan.order_by):
            return False, f"Invalid order_by field '{plan.order_by}'."

        if plan.limit <= 0 or plan.limit > 50:
            plan.limit = 10  # Enforce safety ceiling

        return True, "Valid"

    # ── Query Dispatcher ───────────────────────────────────────────────

    def execute(self, plan: QueryPlan) -> QueryResult:
        """Safely executes a query plan and returns structured, verified results."""
        start_t = time.perf_counter()
        valid, err_msg = self.validate_plan(plan)
        if not valid:
            return QueryResult(
                operation=plan.operation,
                success=False,
                data=None,
                summary_markdown=f"⚠️ Query validation error: {err_msg}",
                verified_facts=[f"Error: {err_msg}"],
                execution_time_ms=round((time.perf_counter() - start_t) * 1000, 2),
                error=err_msg
            )

        try:
            if plan.operation == "ranking":
                res = self._execute_ranking(plan)
            elif plan.operation == "retrieval":
                res = self._execute_retrieval(plan)
            elif plan.operation == "aggregation":
                res = self._execute_aggregation(plan)
            elif plan.operation == "group_by":
                res = self._execute_group_by(plan)
            elif plan.operation == "comparison":
                res = self._execute_comparison(plan)
            elif plan.operation == "conditional":
                res = self._execute_conditional(plan)
            elif plan.operation == "distribution":
                res = self._execute_distribution(plan)
            elif plan.operation == "semester_comparison":
                res = self._execute_semester_comparison(plan)
            else:
                res = self._execute_filtering(plan)

            res.execution_time_ms = round((time.perf_counter() - start_t) * 1000, 2)
            return res

        except Exception as e:
            return QueryResult(
                operation=plan.operation,
                success=False,
                data=None,
                summary_markdown=f"⚠️ Failed to execute analytical query: {str(e)}",
                verified_facts=[f"Execution exception: {str(e)}"],
                execution_time_ms=round((time.perf_counter() - start_t) * 1000, 2),
                error=str(e)
            )

    # ── Helper Filtering ────────────────────────────────────────────────

    def _apply_filters(self, students: list[dict], filters: list[FilterCondition]) -> list[dict]:
        """Apply safe filter conditions to student records."""
        results = students
        for f in filters:
            filtered = []
            for s in results:
                val = s.get(f.field)
                if val is None:
                    continue

                if f.op == "==":
                    if str(val).lower() == str(f.val).lower():
                        filtered.append(s)
                elif f.op == "!=":
                    if str(val).lower() != str(f.val).lower():
                        filtered.append(s)
                elif f.op == ">":
                    if isinstance(val, (int, float)) and val > f.val:
                        filtered.append(s)
                elif f.op == ">=":
                    if isinstance(val, (int, float)) and val >= f.val:
                        filtered.append(s)
                elif f.op == "<":
                    if isinstance(val, (int, float)) and val < f.val:
                        filtered.append(s)
                elif f.op == "<=":
                    if isinstance(val, (int, float)) and val <= f.val:
                        filtered.append(s)
                elif f.op == "in":
                    if isinstance(f.val, (list, set)) and val in f.val:
                        filtered.append(s)
                elif f.op == "contains":
                    if str(f.val).lower() in str(val).lower():
                        filtered.append(s)
                elif f.op == "between":
                    if isinstance(f.val, (list, tuple)) and len(f.val) == 2:
                        if f.val[0] <= val <= f.val[1]:
                            filtered.append(s)
            results = filtered
        return results

    # ── Execution Handlers ──────────────────────────────────────────────

    def _execute_ranking(self, plan: QueryPlan) -> QueryResult:
        """Executes student ranking queries (Class toppers, Top N, Bottom N, Subject toppers)."""
        data_pool = self._apply_filters(self.students, plan.filters)
        if not data_pool:
            return QueryResult(
                operation="ranking",
                success=True,
                data=[],
                summary_markdown="No students match the specified criteria.",
                verified_facts=["No matching student records found."],
                execution_time_ms=0.0
            )

        # Subject topper query
        if plan.subject_code:
            code = plan.subject_code
            title = self.schema.core_subjects.get(code) or self.schema.arrear_subjects.get(code, code)
            valid_students = []
            for s in data_pool:
                m_str = s.get(f"marks.{code}") or s.get("marks", {}).get(code, "-")
                try:
                    m_val = int(m_str)
                    valid_students.append({**s, "subject_score": m_val})
                except (ValueError, TypeError):
                    pass

            if not valid_students:
                return QueryResult(
                    operation="ranking",
                    success=True,
                    data=[],
                    summary_markdown=f"No students appeared or scored marks in **{code} ({title})**.",
                    verified_facts=[f"No marks recorded for subject {code}."],
                    execution_time_ms=0.0
                )

            valid_students.sort(key=lambda s: s["subject_score"], reverse=True)
            max_score = valid_students[0]["subject_score"]
            toppers = [s for s in valid_students if s["subject_score"] == max_score]

            facts = [
                f"Subject: {code} ({title})",
                f"Highest Mark: {max_score}",
                f"Topper Count: {len(toppers)}",
                f"Toppers: {', '.join(s['name'] + ' (' + s['register_no'] + ')' for s in toppers)}"
            ]

            lines = [f"The top scorer in **{code} ({title})** is **{toppers[0]['name']}** with **{max_score} marks**."]
            if len(toppers) > 1:
                lines[0] = f"There is a tie for the highest score in **{code} ({title})** with **{max_score} marks**:"
            lines.append("")
            for t in toppers:
                lines.append(f"* **Name**: {t['name']}")
                lines.append(f"* **Register No**: {t['register_no']}")
                lines.append(f"* **Subject Mark**: {t['subject_score']}")
                lines.append(f"* **Overall Total**: {t['total']} (Rank {t['rank']})")

            return QueryResult(
                operation="ranking",
                success=True,
                data=toppers,
                summary_markdown="\n".join(lines),
                verified_facts=facts,
                execution_time_ms=0.0
            )

        # Overall Class Topper or Filtered Topper (e.g. Female Topper)
        reverse = (plan.order_dir.lower() == "desc")
        order_field = plan.order_by or "total"
        data_pool.sort(key=lambda s: s.get(order_field, 0), reverse=reverse)

        # If requesting topper(s) (limit=1 or top rank)
        if plan.limit == 1 or plan.meta.get("topper_only"):
            best_val = data_pool[0][order_field]
            toppers = [s for s in data_pool if s[order_field] == best_val]

            gender_label = ""
            for f in plan.filters:
                if f.field == "gender":
                    gender_label = f"{f.val} "

            facts = [
                f"{gender_label}Class Topper(s): {', '.join(t['name'] + ' (' + str(t['total']) + ')' for t in toppers)}",
                f"Total Marks: {best_val}",
                f"Rank: {toppers[0]['rank']}",
                f"Tied Count: {len(toppers)}"
            ]

            if len(toppers) == 1:
                t = toppers[0]
                lines = [
                    f"The {gender_label.lower()}class topper is **{t['name']}**.",
                    "",
                    f"* **Name**: {t['name']}",
                    f"* **Register No**: {t['register_no']}",
                    f"* **Total Marks**: {t['total']}",
                    f"* **Rank**: {t['rank']}"
                ]
            else:
                names = ", ".join(f"**{t['name']}** (`{t['register_no']}`)" for t in toppers)
                lines = [
                    f"There is a tie for {gender_label.lower()}class topper with **{best_val} marks**:",
                    f"* Tied Students: {names}",
                    f"* Rank: {toppers[0]['rank']}"
                ]
                for t in toppers:
                    lines.append(f"* **{t['name']}** (`{t['register_no']}`): Total {t['total']} marks")

            return QueryResult(
                operation="ranking",
                success=True,
                data=toppers,
                summary_markdown="\n".join(lines),
                verified_facts=facts,
                execution_time_ms=0.0
            )

        # Top N or Bottom N
        items = data_pool[:plan.limit]
        direction_text = "Top" if reverse else "Lowest"
        lines = [f"### Verified {direction_text} {len(items)} Students:"]
        facts = []
        for s in items:
            lines.append(f"* **Rank {s['rank']}**: **{s['name']}** (`{s['register_no']}`) — **{s['total']} marks**")
            facts.append(f"Rank {s['rank']}: {s['name']} ({s['register_no']}) - Total: {s['total']}")

        return QueryResult(
            operation="ranking",
            success=True,
            data=items,
            summary_markdown="\n".join(lines),
            verified_facts=facts,
            execution_time_ms=0.0
        )

    def _execute_retrieval(self, plan: QueryPlan) -> QueryResult:
        """Retrieves individual student records or subject profiles."""
        query_str = str(plan.meta.get("query_string", "")).strip().lower()

        # Subject details query
        if plan.target == "subject" and plan.subject_code:
            code = plan.subject_code
            st = self.subject_stats.get(code)
            if not st:
                return QueryResult(
                    operation="retrieval",
                    success=False,
                    data=None,
                    summary_markdown=f"No subject data found for code '{code}'.",
                    verified_facts=[],
                    execution_time_ms=0.0
                )
            lines = [
                f"### Course Details: **{code} ({st['title']})**",
                "",
                f"* **Appeared Students**: {st['attempted']}",
                f"* **Passed Students**: {st['passed']}",
                f"* **Failed Students**: {st['failed']}",
                f"* **Absent Students**: {st['absent']}",
                f"* **Pass Percentage**: **{st['pass_percentage']}%**",
                f"* **Average Marks**: {st['avg_marks']}",
                f"* **Highest Mark**: {st['max_marks']}",
                f"* **Lowest Mark**: {st['min_marks']}"
            ]
            facts = [
                f"Subject: {code} ({st['title']})",
                f"Pass Rate: {st['pass_percentage']}%",
                f"Appeared: {st['attempted']}, Passed: {st['passed']}, Failed: {st['failed']}, Absent: {st['absent']}",
                f"Average: {st['avg_marks']}, Max: {st['max_marks']}, Min: {st['min_marks']}"
            ]
            return QueryResult(
                operation="retrieval",
                success=True,
                data=st,
                summary_markdown="\n".join(lines),
                verified_facts=facts,
                execution_time_ms=0.0
            )

        # Student lookup by reg_no or name
        matches = []
        for s in self.students:
            if (query_str and (query_str == s["register_no"].lower() or query_str in s["name"].lower())) or \
               any(f.field == "register_no" and str(f.val).lower() == s["register_no"].lower() for f in plan.filters):
                matches.append(s)

        if not matches:
            return QueryResult(
                operation="retrieval",
                success=True,
                data=[],
                summary_markdown=f"No student record found matching '{query_str}'.",
                verified_facts=[f"No record matching '{query_str}'."],
                execution_time_ms=0.0
            )

        s = matches[0]
        status_text = "Passed all core subjects" if s["all_core_passed"] else f"Failed in {s['failed_core_count']} core subject(s)"
        lines = [
            f"### Verified Student Profile: **{s['name']}**",
            "",
            f"* **Register No**: `{s['register_no']}`",
            f"* **Rank**: **{s['rank']}** of {len(self.students)}",
            f"* **Total Marks**: **{s['total']}**",
            f"* **Academic Status**: {status_text}",
            f"* **Gender**: {s['gender']}, Community: {s['community']}",
            "",
            "**Subject-wise Marks:**"
        ]
        facts = [
            f"Student: {s['name']} ({s['register_no']})",
            f"Rank: {s['rank']}, Total: {s['total']}",
            f"Status: {status_text}"
        ]
        for c, m in s["marks"].items():
            title = self.schema.core_subjects.get(c, c)
            lines.append(f"* {c} ({title}): **{m}**")
            facts.append(f"{c}: {m}")

        if s["arrear_attempts"]:
            lines.append("")
            lines.append("**Arrear Papers Attempted:**")
            for arr in s["arrear_attempts"]:
                lines.append(f"* {arr['code']} ({arr['title']}): {arr['total']} ({arr['result']})")
                facts.append(f"Arrear {arr['code']}: {arr['total']} ({arr['result']})")

        return QueryResult(
            operation="retrieval",
            success=True,
            data=s,
            summary_markdown="\n".join(lines),
            verified_facts=facts,
            execution_time_ms=0.0
        )

    def _execute_aggregation(self, plan: QueryPlan) -> QueryResult:
        """Executes statistical aggregations (Overall pass %, Class average, Counts)."""
        data_pool = self._apply_filters(self.students, plan.filters)
        total_students = len(data_pool)

        if total_students == 0:
            return QueryResult(
                operation="aggregation",
                success=True,
                data={},
                summary_markdown="No student records match the given criteria.",
                verified_facts=["Count: 0"],
                execution_time_ms=0.0
            )

        appeared = [s for s in data_pool if s["has_numeric_mark"]]
        appeared_count = len(appeared)
        all_passed = [s for s in data_pool if s["all_core_passed"]]
        all_passed_count = len(all_passed)
        failed_count = len([s for s in data_pool if s["failed_core_count"] > 0])
        absent_count = total_students - appeared_count

        pass_pct = round((all_passed_count / appeared_count) * 100, 2) if appeared_count > 0 else 0.0

        numeric_totals = [s["total"] for s in data_pool if s["total"] > 0]
        avg_total = round(statistics.mean(numeric_totals), 2) if numeric_totals else 0.0
        med_total = round(statistics.median(numeric_totals), 2) if numeric_totals else 0.0

        filter_label = ""
        for f in plan.filters:
            filter_label += f" ({f.field}: {f.val})"

        lines = [
            f"### Verified Class Performance Overview{filter_label}:",
            "",
            f"* **Total Enrolled**: {total_students}",
            f"* **Appeared in Exams**: {appeared_count} (Fully absent: {absent_count})",
            f"* **Passed All Core Subjects**: **{all_passed_count}**",
            f"* **Students with Arrears/Fails**: {failed_count}",
            f"* **Overall Pass Percentage**: **{pass_pct}%**",
            f"* **Class Average Total**: **{avg_total} marks**",
            f"* **Class Median Total**: **{med_total} marks**"
        ]

        facts = [
            f"Enrolled: {total_students}, Appeared: {appeared_count}, Absent: {absent_count}",
            f"Passed All Subjects: {all_passed_count} ({pass_pct}%)",
            f"Failed / Arrears: {failed_count}",
            f"Average Total: {avg_total}, Median Total: {med_total}"
        ]

        return QueryResult(
            operation="aggregation",
            success=True,
            data={
                "total_students": total_students,
                "appeared_students": appeared_count,
                "passed_students": all_passed_count,
                "pass_percentage": pass_pct,
                "average_total": avg_total,
                "median_total": med_total,
            },
            summary_markdown="\n".join(lines),
            verified_facts=facts,
            execution_time_ms=0.0
        )

    def _execute_comparison(self, plan: QueryPlan) -> QueryResult:
        """Compares two or more cohorts (e.g. Male vs Female, Subject A vs Subject B)."""
        # Subject vs Subject Comparison
        if plan.target == "subject" and len(plan.compare_groups) >= 2:
            code1 = plan.compare_groups[0].get("code")
            code2 = plan.compare_groups[1].get("code")
            st1 = self.subject_stats.get(code1, {})
            st2 = self.subject_stats.get(code2, {})

            lines = [
                f"### Subject Comparison: **{code1}** vs **{code2}**",
                "",
                f"| Metric | {code1} ({st1.get('title', '')}) | {code2} ({st2.get('title', '')}) |",
                "| :--- | :--- | :--- |",
                f"| **Pass Percentage** | **{st1.get('pass_percentage')}%** | **{st2.get('pass_percentage')}%** |",
                f"| **Average Mark** | {st1.get('avg_marks')} | {st2.get('avg_marks')} |",
                f"| **Highest Mark** | {st1.get('max_marks')} | {st2.get('max_marks')} |",
                f"| **Failed Count** | {st1.get('failed')} | {st2.get('failed')} |",
                f"| **Absent Count** | {st1.get('absent')} | {st2.get('absent')} |"
            ]
            facts = [
                f"{code1} Pass Rate: {st1.get('pass_percentage')}%, Avg: {st1.get('avg_marks')}",
                f"{code2} Pass Rate: {st2.get('pass_percentage')}%, Avg: {st2.get('avg_marks')}"
            ]
            return QueryResult(
                operation="comparison",
                success=True,
                data={"group1": st1, "group2": st2},
                summary_markdown="\n".join(lines),
                verified_facts=facts,
                execution_time_ms=0.0
            )

        # Gender Comparison (Default Demographic Comparison)
        males = [s for s in self.students if s["gender"].lower() in ["male", "m"]]
        females = [s for s in self.students if s["gender"].lower() in ["female", "f"]]

        def get_cohort_stats(cohort):
            app = [s for s in cohort if s["has_numeric_mark"]]
            passed = [s for s in cohort if s["all_core_passed"]]
            pct = round((len(passed) / len(app)) * 100, 2) if app else 0.0
            tots = [s["total"] for s in cohort if s["total"] > 0]
            avg_t = round(statistics.mean(tots), 2) if tots else 0.0
            return {
                "total": len(cohort),
                "appeared": len(app),
                "passed": len(passed),
                "pass_percentage": pct,
                "average_total": avg_t
            }

        m_stats = get_cohort_stats(males)
        f_stats = get_cohort_stats(females)

        lines = [
            "### Verified Gender Performance Comparison:",
            "",
            "| Metric | Male Students | Female Students |",
            "| :--- | :--- | :--- |",
            f"| **Enrolled** | {m_stats['total']} | {f_stats['total']} |",
            f"| **Appeared** | {m_stats['appeared']} | {f_stats['appeared']} |",
            f"| **Passed All Subjects** | {m_stats['passed']} | {f_stats['passed']} |",
            f"| **Pass Percentage** | **{m_stats['pass_percentage']}%** | **{f_stats['pass_percentage']}%** |",
            f"| **Average Total Marks** | **{m_stats['average_total']}** | **{f_stats['average_total']}** |"
        ]

        facts = [
            f"Male Pass Rate: {m_stats['pass_percentage']}% ({m_stats['passed']}/{m_stats['appeared']}), Avg: {m_stats['average_total']}",
            f"Female Pass Rate: {f_stats['pass_percentage']}% ({f_stats['passed']}/{f_stats['appeared']}), Avg: {f_stats['average_total']}"
        ]

        return QueryResult(
            operation="comparison",
            success=True,
            data={"male": m_stats, "female": f_stats},
            summary_markdown="\n".join(lines),
            verified_facts=facts,
            execution_time_ms=0.0
        )

    def _execute_conditional(self, plan: QueryPlan) -> QueryResult:
        """Filters students failing in >N subjects or matching multi-condition criteria."""
        filtered_students = self._apply_filters(self.students, plan.filters)
        threshold = plan.meta.get("failed_threshold", 2)

        lines = [
            f"### Verified Query Results ({len(filtered_students)} student(s) matched):",
            ""
        ]
        facts = [f"Matched count: {len(filtered_students)}"]

        if not filtered_students:
            lines.append("No students matched the specified conditions.")
            return QueryResult(
                operation="conditional",
                success=True,
                data=[],
                summary_markdown="\n".join(lines),
                verified_facts=facts,
                execution_time_ms=0.0
            )

        for s in filtered_students[:plan.limit]:
            fail_names = ", ".join(f"{sub['code']}" for sub in s["failed_core_subjects"])
            lines.append(f"* **{s['name']}** (`{s['register_no']}`): Failed in **{s['failed_core_count']}** subject(s) [{fail_names}] — Total: {s['total']}")
            facts.append(f"{s['name']} ({s['register_no']}): {s['failed_core_count']} fails [{fail_names}]")

        if len(filtered_students) > plan.limit:
            lines.append(f"* *...and {len(filtered_students) - plan.limit} more student(s).*")

        return QueryResult(
            operation="conditional",
            success=True,
            data=filtered_students,
            summary_markdown="\n".join(lines),
            verified_facts=facts,
            execution_time_ms=0.0
        )

    def _execute_distribution(self, plan: QueryPlan) -> QueryResult:
        """Computes performance distributions (Distinction, First Class, Second Class, etc.)."""
        totals = [s["total"] for s in self.students if s["total"] > 0]
        max_possible = len(self.schema.core_subjects) * 100

        bands = {
            "Distinction (>= 75%)": 0,
            "First Class (60% - 74%)": 0,
            "Second Class (50% - 59%)": 0,
            "Third Class / Pass (40% - 49%)": 0,
            "Arrears / Fail (< 40%)": 0
        }

        for s in self.students:
            if not s["has_numeric_mark"]:
                continue
            if not s["all_core_passed"]:
                bands["Arrears / Fail (< 40%)"] += 1
                continue

            pct = (s["total"] / max_possible) * 100 if max_possible > 0 else 0
            if pct >= 75:
                bands["Distinction (>= 75%)"] += 1
            elif pct >= 60:
                bands["First Class (60% - 74%)"] += 1
            elif pct >= 50:
                bands["Second Class (50% - 59%)"] += 1
            else:
                bands["Third Class / Pass (40% - 49%)"] += 1

        lines = [
            "### Verified Academic Performance Distribution:",
            "",
            "| Performance Band | Student Count | Percentage |",
            "| :--- | :--- | :--- |"
        ]
        facts = []
        total_appeared = sum(bands.values())
        for b_name, count in bands.items():
            b_pct = round((count / total_appeared) * 100, 2) if total_appeared > 0 else 0.0
            lines.append(f"| **{b_name}** | {count} | {b_pct}% |")
            facts.append(f"{b_name}: {count} ({b_pct}%)")

        return QueryResult(
            operation="distribution",
            success=True,
            data=bands,
            summary_markdown="\n".join(lines),
            verified_facts=facts,
            execution_time_ms=0.0
        )

    def _execute_semester_comparison(self, plan: QueryPlan) -> QueryResult:
        """Compares core semester performance vs historical arrear paper attempts."""
        core_att = sum(self.subject_stats[c]["attempted"] for c in self.schema.core_subjects if c in self.subject_stats)
        core_pass = sum(self.subject_stats[c]["passed"] for c in self.schema.core_subjects if c in self.subject_stats)
        core_pct = round((core_pass / core_att) * 100, 2) if core_att > 0 else 0.0

        arr_att = sum(self.subject_stats[c]["attempted"] for c in self.schema.arrear_subjects if c in self.subject_stats)
        arr_pass = sum(self.subject_stats[c]["passed"] for c in self.schema.arrear_subjects if c in self.subject_stats)
        arr_pct = round((arr_pass / arr_att) * 100, 2) if arr_att > 0 else 0.0

        students_with_arr = len([s for s in self.students if s["arrear_attempts"]])

        lines = [
            "### Verified Semester & Backlog Comparison:",
            "",
            f"* **Current Semester**: {self.schema.current_semester_str} ({len(self.schema.core_subjects)} core courses)",
            f"* **Core Paper Pass Rate**: **{core_pct}%** ({core_pass}/{core_att} papers cleared)",
            f"* **Backlog/Arrear Papers Cleared**: **{arr_pct}%** ({arr_pass}/{arr_att} papers cleared)",
            f"* **Students Attempting Arrears**: {students_with_arr} student(s)"
        ]

        facts = [
            f"Core Pass Rate: {core_pct}% ({core_pass}/{core_att})",
            f"Arrear Pass Rate: {arr_pct}% ({arr_pass}/{arr_att})",
            f"Students with Arrears: {students_with_arr}"
        ]

        return QueryResult(
            operation="semester_comparison",
            success=True,
            data={
                "core_pass_rate": core_pct,
                "arrear_pass_rate": arr_pct,
                "students_with_arrears": students_with_arr
            },
            summary_markdown="\n".join(lines),
            verified_facts=facts,
            execution_time_ms=0.0
        )

    def _execute_group_by(self, plan: QueryPlan) -> QueryResult:
        """Executes group by operations across categories."""
        if not plan.group_by:
            return self._execute_aggregation(plan)

        grp_field = plan.group_by[0]
        grouped = {}
        for s in self.students:
            val = str(s.get(grp_field, "Unknown"))
            if val not in grouped:
                grouped[val] = []
            grouped[val].append(s)

        lines = [
            f"### Verified Breakdown by **{grp_field.capitalize()}**:",
            "",
            f"| {grp_field.capitalize()} | Count | Passed All | Pass % | Average Total |",
            "| :--- | :--- | :--- | :--- | :--- |"
        ]
        facts = []
        for val, items in sorted(grouped.items()):
            app = [s for s in items if s["has_numeric_mark"]]
            passed = [s for s in items if s["all_core_passed"]]
            pct = round((len(passed) / len(app)) * 100, 2) if app else 0.0
            tots = [s["total"] for s in items if s["total"] > 0]
            avg_t = round(statistics.mean(tots), 2) if tots else 0.0
            lines.append(f"| **{val}** | {len(items)} | {len(passed)} | **{pct}%** | {avg_t} |")
            facts.append(f"{val}: Count {len(items)}, Passed {len(passed)} ({pct}%), Avg {avg_t}")

        return QueryResult(
            operation="group_by",
            success=True,
            data=grouped,
            summary_markdown="\n".join(lines),
            verified_facts=facts,
            execution_time_ms=0.0
        )

    def _execute_filtering(self, plan: QueryPlan) -> QueryResult:
        """Default filter operation."""
        return self._execute_conditional(plan)
