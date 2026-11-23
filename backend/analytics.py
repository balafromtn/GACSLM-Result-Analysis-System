"""
analytics.py — Deterministic academic data analysis module.

Performs all academic calculations in Python using deterministic logic:
  - Class toppers and top ranks (with proper tie handling)
  - Class average and aggregate totals
  - Subject-wise pass percentage, fail count, absent count, average, min, max
  - Overall class pass percentage and pass/fail/arrear counts
  - Identification of students failing in specific subjects or >N subjects
  - Semester comparisons (core semester vs arrear papers)
  - Individual student lookups by register number or name
  - Absence and missing marks handling (missing marks are '-' and not treated as 0)
"""

import statistics
import re
from typing import Any


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


class AcademicAnalytics:
    """Engine for computing verified academic metrics over student examination results."""

    def __init__(self, scraped_results: list[dict]):
        self.raw_results = scraped_results or []
        self.degree_branch = "Unknown"
        self.exam_month_year = "Unknown"
        self.current_semester_int = 0
        self.current_semester_str = ""
        self.core_codes: list[str] = []
        self.arrear_codes: list[str] = []
        self.code_to_title: dict[str, str] = {}
        self.students: list[dict] = []
        self.subject_stats: dict[str, dict] = {}

        self._process()

    def _process(self):
        if not self.raw_results:
            return

        # 1. Determine current semester & header metadata
        max_sem_val = 0
        for r in self.raw_results:
            if r.get("degree_branch") and r["degree_branch"] != "UNKNOWN":
                self.degree_branch = r["degree_branch"]
            if r.get("exam_month_year") and r["exam_month_year"] != "UNKNOWN":
                self.exam_month_year = r["exam_month_year"]

            for subj in r.get("subjects", []):
                sem_str = subj.get("semester", "")
                sem_val = roman_to_int(sem_str)
                if sem_val > max_sem_val:
                    max_sem_val = sem_val
                    self.current_semester_str = sem_str

        self.current_semester_int = max_sem_val

        # 2. Categorize Core vs Arrear subjects
        core_set = set()
        arrear_set = set()
        for r in self.raw_results:
            for subj in r.get("subjects", []):
                code = subj.get("code")
                title = subj.get("title", "")
                if code and title and code not in self.code_to_title:
                    self.code_to_title[code] = title

                sem_val = roman_to_int(subj.get("semester", ""))
                if sem_val == max_sem_val:
                    core_set.add(code)
                elif sem_val > 0:
                    arrear_set.add(code)

        self.core_codes = sorted(list(core_set))
        self.arrear_codes = sorted(list(arrear_set))

        # 3. Process student records
        processed_students = []
        raw_subject_data = {code: {"attempted": 0, "passed": 0, "failed": 0, "absent": 0, "not_opted": 0, "marks": []}
                            for code in self.core_codes + self.arrear_codes}

        for r in self.raw_results:
            name = r.get("name", "UNKNOWN").strip()
            reg = (r.get("register_no") or r.get("reg_no") or "UNKNOWN").strip()
            gender = r.get("gender", "UNKNOWN").strip()
            community = r.get("community", "UNKNOWN").strip()

            core_marks = {}
            total = 0
            has_numeric_mark = False
            failed_core_subjects = []
            absent_core_subjects = []
            passed_core_subjects = []
            arrear_attempts = []

            for code in self.core_codes:
                core_marks[code] = "-"

            for subj in r.get("subjects", []):
                code = subj.get("code")
                total_mark = str(subj.get("total", "-")).strip()
                res = str(subj.get("result", "")).strip().upper()
                sem_val = roman_to_int(subj.get("semester", ""))

                if code in self.core_codes:
                    core_marks[code] = total_mark
                    if total_mark == "-" or not total_mark:
                        raw_subject_data[code]["not_opted"] += 1
                    elif total_mark.upper() in ["AA", "ABSENT", "AB"]:
                        absent_core_subjects.append({"code": code, "title": self.code_to_title.get(code, code)})
                        raw_subject_data[code]["absent"] += 1
                        raw_subject_data[code]["attempted"] += 1
                    else:
                        # Numeric mark
                        try:
                            m_val = int(total_mark)
                            total += m_val
                            has_numeric_mark = True
                            raw_subject_data[code]["attempted"] += 1
                            raw_subject_data[code]["marks"].append(m_val)
                            
                            # Check pass / fail according to result column
                            if res == "PASS":
                                passed_core_subjects.append({"code": code, "title": self.code_to_title.get(code, code), "marks": m_val})
                                raw_subject_data[code]["passed"] += 1
                            elif res in ["RA", "FAIL", "F", "U"]:
                                failed_core_subjects.append({"code": code, "title": self.code_to_title.get(code, code), "marks": m_val, "result": res})
                                raw_subject_data[code]["failed"] += 1
                            else:
                                if m_val >= 40:  # Academic default threshold
                                    passed_core_subjects.append({"code": code, "title": self.code_to_title.get(code, code), "marks": m_val})
                                    raw_subject_data[code]["passed"] += 1
                                else:
                                    failed_core_subjects.append({"code": code, "title": self.code_to_title.get(code, code), "marks": m_val, "result": "RA"})
                                    raw_subject_data[code]["failed"] += 1
                        except ValueError:
                            # Non-numeric mark
                            pass

                elif code in self.arrear_codes:
                    arrear_attempts.append({
                        "code": code,
                        "title": self.code_to_title.get(code, code),
                        "total": total_mark,
                        "result": res
                    })
                    if total_mark.upper() in ["AA", "ABSENT", "AB"]:
                        raw_subject_data[code]["absent"] += 1
                        raw_subject_data[code]["attempted"] += 1
                    elif total_mark != "-":
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

            all_core_passed = len(failed_core_subjects) == 0 and len(absent_core_subjects) == 0 and len(passed_core_subjects) > 0

            processed_students.append({
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
            })

        # 4. Rank students by total marks descending (proper tie handling)
        processed_students.sort(key=lambda s: s["total"], reverse=True)
        for i, s in enumerate(processed_students):
            if i > 0 and s["total"] == processed_students[i - 1]["total"]:
                s["rank"] = processed_students[i - 1]["rank"]
            else:
                s["rank"] = i + 1

        self.students = processed_students

        # 5. Compute Subject Statistics
        for code, stats in raw_subject_data.items():
            att = stats["attempted"]
            passed = stats["passed"]
            marks_list = stats["marks"]
            avg_mark = round(statistics.mean(marks_list), 2) if marks_list else 0.0
            pass_pct = round((passed / att) * 100, 2) if att > 0 else 0.0

            self.subject_stats[code] = {
                "title": self.code_to_title.get(code, code),
                "attempted": att,
                "passed": passed,
                "failed": stats["failed"],
                "absent": stats["absent"],
                "pass_percentage": pass_pct,
                "avg_marks": avg_mark,
                "max_marks": max(marks_list) if marks_list else 0,
                "min_marks": min(marks_list) if marks_list else 0,
            }

    # ── Deterministic Query Functions ──────────────────────────────────

    def get_toppers(self) -> list[dict]:
        """Return the class topper(s). Handles ties: multiple students can be rank 1."""
        if not self.students:
            return []
        top_rank = self.students[0]["rank"]
        return [s for s in self.students if s["rank"] == top_rank]

    def get_top_students(self, n: int = 5) -> list[dict]:
        """Return the top N students."""
        return self.students[:n]

    def get_gender_toppers(self) -> dict[str, list[dict]]:
        """Return male topper(s) and female topper(s), handling ties."""
        males = [s for s in self.students if s["gender"].lower() in ["male", "m"]]
        females = [s for s in self.students if s["gender"].lower() in ["female", "f"]]

        def find_top(group):
            if not group:
                return []
            max_tot = max(s["total"] for s in group)
            return [s for s in group if s["total"] == max_tot]

        return {
            "male": find_top(males),
            "female": find_top(females),
        }

    def get_overall_pass_stats(self) -> dict:
        """Calculate overall class pass rate and breakdown."""
        total = len(self.students)
        if total == 0:
            return {"total_students": 0, "all_passed_count": 0, "pass_percentage": 0.0}

        all_passed = [s for s in self.students if s["all_core_passed"]]
        with_arrears = [s for s in self.students if s["failed_core_count"] > 0 or len(s["arrear_attempts"]) > 0]
        fully_absent = [s for s in self.students if not s["has_numeric_mark"]]
        appeared = total - len(fully_absent)

        pass_pct = round((len(all_passed) / appeared) * 100, 2) if appeared > 0 else 0.0

        totals = [s["total"] for s in self.students if s["total"] > 0]
        avg_total = round(statistics.mean(totals), 2) if totals else 0.0

        return {
            "total_students": total,
            "appeared_students": appeared,
            "fully_absent_count": len(fully_absent),
            "all_passed_count": len(all_passed),
            "pass_percentage": pass_pct,
            "with_arrears_or_fails": len(with_arrears),
            "average_total": avg_total,
        }

    def get_failed_students(self, min_fails: int = 1) -> list[dict]:
        """
        Return students who failed in at least `min_fails` core subjects.
        e.g., min_fails=1 (any fail), min_fails=3 (more than 2 fails).
        """
        return [s for s in self.students if s["failed_core_count"] >= min_fails]

    def get_students_failing_more_than(self, count: int) -> list[dict]:
        """Return students failing in strictly more than `count` core subjects."""
        return [s for s in self.students if s["failed_core_count"] > count]

    def get_subject_analysis(self) -> list[dict]:
        """Return subject statistics sorted by pass percentage descending."""
        stats_list = []
        for code in self.core_codes:
            st = self.subject_stats.get(code, {})
            stats_list.append({"code": code, **st})
        stats_list.sort(key=lambda s: s["pass_percentage"], reverse=True)
        return stats_list

    def get_semester_comparison(self) -> dict:
        """Compare current semester results vs arrear paper results."""
        core_attempted = sum(self.subject_stats[c]["attempted"] for c in self.core_codes if c in self.subject_stats)
        core_passed = sum(self.subject_stats[c]["passed"] for c in self.core_codes if c in self.subject_stats)
        core_pct = round((core_passed / core_attempted) * 100, 2) if core_attempted > 0 else 0.0

        arrear_attempted = sum(self.subject_stats[c]["attempted"] for c in self.arrear_codes if c in self.subject_stats)
        arrear_passed = sum(self.subject_stats[c]["passed"] for c in self.arrear_codes if c in self.subject_stats)
        arrear_pct = round((arrear_passed / arrear_attempted) * 100, 2) if arrear_attempted > 0 else 0.0

        students_with_arrears = len([s for s in self.students if s["arrear_attempts"]])

        return {
            "current_semester": self.current_semester_str,
            "core_subjects_count": len(self.core_codes),
            "core_papers_attempted": core_attempted,
            "core_papers_passed": core_passed,
            "core_pass_rate": core_pct,
            "arrear_subjects_count": len(self.arrear_codes),
            "arrear_papers_attempted": arrear_attempted,
            "arrear_papers_passed": arrear_passed,
            "arrear_pass_rate": arrear_pct,
            "students_attempting_arrears": students_with_arrears,
        }

    def search_student(self, query: str) -> list[dict]:
        """Search student by register number or name substring."""
        q = query.strip().lower()
        matches = []
        for s in self.students:
            if q == s["register_no"].lower() or q in s["name"].lower():
                matches.append(s)
        return matches


# ── Query Router & Context Builder ─────────────────────────────────────

def build_academic_context_and_intent(query: str, analytics: AcademicAnalytics) -> tuple[str, str]:
    """
    Analyzes the user question and builds a targeted, verified context for the LLM.
    Returns: (verified_context_string, detected_intent)
    """
    if not analytics.students:
        return ("No student examination records are available. Please upload and scrape a batch first.", "empty")

    q_lower = query.lower().strip()

    # Intent 1: Topper / Rank 1
    if any(k in q_lower for k in ["topper", "rank 1", "first rank", "highest mark", "highest score", "top scorer"]):
        toppers = analytics.get_toppers()
        top5 = analytics.get_top_students(5)
        lines = ["### Verified Academic Calculations: Class Topper(s)"]
        if len(toppers) == 1:
            t = toppers[0]
            lines.append(f"- **Class Topper**: {t['name']} (Register No: `{t['register_no']}`) with a total of **{t['total']} marks** (Rank 1).")
        else:
            names = ", ".join(f"**{t['name']}** (`{t['register_no']}` - {t['total']} marks)" for t in toppers)
            lines.append(f"- **Tie for Class Topper**: Multiple students tied for Rank 1 with **{toppers[0]['total']} marks**: {names}.")

        lines.append("\n**Top 5 Students by Rank:**")
        for s in top5:
            lines.append(f"- Rank {s['rank']}: **{s['name']}** (`{s['register_no']}`) — Total: {s['total']}")

        gender_tops = analytics.get_gender_toppers()
        if gender_tops["male"]:
            m_names = ", ".join(f"{s['name']} ({s['total']})" for s in gender_tops["male"])
            lines.append(f"- Male Topper: {m_names}")
        if gender_tops["female"]:
            f_names = ", ".join(f"{s['name']} ({s['total']})" for s in gender_tops["female"])
            lines.append(f"- Female Topper: {f_names}")

        return ("\n".join(lines), "topper")

    # Intent 2: Failed students / Arrears / Backlogs
    # Matches: "failed in more than two subjects", "who failed", "failure list", "arrears"
    match_gt = re.search(r'(?:more than|greater than|>)\s*(\d+|one|two|three|four|five)\s*subject', q_lower)
    word_to_num = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}

    if match_gt or "failed in more than" in q_lower:
        if match_gt:
            val_str = match_gt.group(1)
            threshold = word_to_num.get(val_str, int(val_str) if val_str.isdigit() else 2)
        else:
            threshold = 2

        failed_students = analytics.get_students_failing_more_than(threshold)
        lines = [f"### Verified Academic Calculations: Students Failing in More Than {threshold} Subjects"]
        lines.append(f"- **Total count matching criteria**: {len(failed_students)} student(s).")
        if failed_students:
            lines.append("\n**List of Students:**")
            for s in failed_students:
                failed_subs = ", ".join(f"{item['code']} ({item['title']})" for item in s["failed_core_subjects"])
                lines.append(f"- **{s['name']}** (`{s['register_no']}`): Failed in **{s['failed_core_count']}** subjects [{failed_subs}]")
        else:
            lines.append(f"- No students failed in more than {threshold} subjects.")
        return ("\n".join(lines), "failed_filtered")

    if any(k in q_lower for k in ["who failed", "failed students", "how many failed", "failure list", "arrear list"]):
        failed_students = analytics.get_failed_students(min_fails=1)
        lines = ["### Verified Academic Calculations: Students with Arrears/Fails in Core Semester"]
        lines.append(f"- **Total students with fails**: {len(failed_students)} student(s).")
        if failed_students:
            for s in failed_students:
                failed_subs = ", ".join(f"{item['code']}" for item in s["failed_core_subjects"])
                lines.append(f"- **{s['name']}** (`{s['register_no']}`): {s['failed_core_count']} fail(s) [{failed_subs}]")
        else:
            lines.append("- All appeared students passed their core semester subjects.")
        return ("\n".join(lines), "failed_list")

    # Intent 3: Overall Performance / Pass Percentage / Class Summary
    if any(k in q_lower for k in ["pass percentage", "pass rate", "how is the class performing", "class performance", "summary", "overview"]):
        stats = analytics.get_overall_pass_stats()
        subj_stats = analytics.get_subject_analysis()
        toppers = analytics.get_toppers()

        top_names = ", ".join(f"{t['name']} ({t['total']} marks)" for t in toppers)
        lines = [
            "### Verified Academic Calculations: Class Performance Overview",
            f"- **Degree & Branch**: {analytics.degree_branch}",
            f"- **Exam Session**: {analytics.exam_month_year} (Semester {analytics.current_semester_str})",
            f"- **Total Enrolled Students**: {stats['total_students']}",
            f"- **Appeared Students**: {stats['appeared_students']} ({stats['fully_absent_count']} fully absent)",
            f"- **Passed All Core Subjects**: {stats['all_passed_count']} student(s)",
            f"- **Overall Class Pass Percentage**: **{stats['pass_percentage']}%**",
            f"- **Class Average Total Marks**: {stats['average_total']}",
            f"- **Class Topper**: {top_names}",
            "\n**Subject-wise Pass Rates:**"
        ]
        for st in subj_stats:
            lines.append(f"- {st['code']} ({st['title']}): **{st['pass_percentage']}% pass** (Avg: {st['avg_marks']}, Max: {st['max_marks']}, Fail: {st['failed']}, Absent: {st['absent']})")

        return ("\n".join(lines), "performance_summary")

    # Intent 4: Semester Comparison
    if any(k in q_lower for k in ["semester", "sem comparison", "arrear vs core", "backlog"]):
        sem_comp = analytics.get_semester_comparison()
        lines = [
            "### Verified Academic Calculations: Semester & Arrear Comparison",
            f"- **Current Semester**: {sem_comp['current_semester']} ({sem_comp['core_subjects_count']} core subjects)",
            f"- **Core Papers Pass Rate**: **{sem_comp['core_pass_rate']}%** ({sem_comp['core_papers_passed']}/{sem_comp['core_papers_attempted']} passed)",
            f"- **Arrear/Backlog Papers Pass Rate**: **{sem_comp['arrear_pass_rate']}%** ({sem_comp['arrear_papers_passed']}/{sem_comp['arrear_papers_attempted']} passed)",
            f"- **Students Attempting Backlog Papers**: {sem_comp['students_attempting_arrears']} student(s)"
        ]
        return ("\n".join(lines), "semester_comparison")

    # Intent 5: Specific Student Search (by reg number or name)
    # Check if any register number is mentioned in query
    for s in analytics.students:
        if s["register_no"].lower() in q_lower or (len(s["name"]) > 3 and s["name"].lower() in q_lower):
            status_str = "Passed all core subjects" if s["all_core_passed"] else f"Failed in {s['failed_core_count']} core subject(s)"
            lines = [
                f"### Verified Academic Record: {s['name']} (`{s['register_no']}`)",
                f"- **Rank**: {s['rank']} out of {len(analytics.students)}",
                f"- **Total Marks (Core Semester)**: {s['total']}",
                f"- **Status**: {status_str}",
                f"- **Gender**: {s['gender']}, Community: {s['community']}",
                "\n**Subject Marks:**"
            ]
            for code in analytics.core_codes:
                mark = s["marks"].get(code, "-")
                title = analytics.code_to_title.get(code, code)
                lines.append(f"- {code} ({title}): **{mark}**")
            if s["arrear_attempts"]:
                lines.append("\n**Arrear Papers Attempted:**")
                for arr in s["arrear_attempts"]:
                    lines.append(f"- {arr['code']} ({arr['title']}): {arr['total']} ({arr['result']})")
            return ("\n".join(lines), "student_lookup")

    # Default / General Query Context: Provide executive summary + leaderboard + subject stats
    stats = analytics.get_overall_pass_stats()
    toppers = analytics.get_toppers()
    top5 = analytics.get_top_students(5)
    topper_str = ", ".join(f"{t['name']} ({t['total']} marks)" for t in toppers)

    lines = [
        "### Verified Academic Dataset Summary",
        f"- Class Topper: {topper_str}",
        f"- Overall Pass Rate: {stats['pass_percentage']}% ({stats['all_passed_count']}/{stats['appeared_students']} students)",
        f"- Total Enrolled: {stats['total_students']}, Class Average Total: {stats['average_total']}",
        "\n**Top Ranked Students:**"
    ]
    for s in top5:
        lines.append(f"- Rank {s['rank']}: {s['name']} (`{s['register_no']}`) - Total: {s['total']}")

    lines.append("\n**Subject Performance:**")
    for st in analytics.get_subject_analysis():
        lines.append(f"- {st['code']} ({st['title']}): {st['pass_percentage']}% pass (Avg: {st['avg_marks']})")

    return ("\n".join(lines), "general")


def sanitize_llm_response(text: str) -> str:
    """
    Remove any internal chain-of-thought, <think> tags, or 'Thinking Process:'
    sections from the response to protect frontend quality.
    """
    if not text:
        return ""

    # 1. Strip <think>...</think> blocks
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)

    # 2. Strip 'Thinking Process:' blocks
    if "Thinking Process:" in cleaned:
        for marker in ["**Final Response:**", "Final Response:", "**Answer:**", "Answer:", "Output:", "**Output:**"]:
            if marker in cleaned:
                cleaned = cleaned.split(marker)[-1].strip()
                break
        else:
            parts = cleaned.split("Thinking Process:")
            before_thinking = parts[0].strip()
            after_thinking = parts[1]

            paragraphs = after_thinking.split("\n\n")
            conclusion_paras = []
            for p in paragraphs:
                p_str = p.strip()
                if not p_str:
                    continue
                if re.match(r'^(\d+\.|\*|\-|\bAnalyze\b|\bScan\b|\bExamine\b|\bDetermine\b|\bFormulate\b|\bDraft\b|\bReview\b)', p_str, re.IGNORECASE):
                    continue
                conclusion_paras.append(p_str)

            if conclusion_paras:
                cleaned = "\n\n".join(conclusion_paras).strip()
            elif before_thinking:
                cleaned = before_thinking
            else:
                lines = [l.strip() for l in after_thinking.splitlines() if l.strip()]
                for l in reversed(lines):
                    if not re.match(r'^(\d+\.|\*|\-|\bAnalyze\b|\bReview\b|\bDraft\b)', l, re.IGNORECASE) and len(l) > 10:
                        cleaned = l.strip('"\'')
                        break

    # 3. Clean up trailing artifacts like 'cw'
    cleaned = re.sub(r'\s*cw\s*$', '', cleaned)

    # 4. Normalize inline bullet points if model bundled them onto one line
    # e.g., "... topper is **BALAJI M**. * **Name**: BALAJI M * **Rank**: 1"
    cleaned = re.sub(r'([.!?:\w\)])\s+([*•\-]\s+)', r'\1\n\n\2', cleaned, count=1)
    cleaned = re.sub(r'([.!?:\w\)])\s+([*•\-]\s+)', r'\1\n\2', cleaned)
    cleaned = re.sub(r'([.!?:\w\)])\s+(\d+\.\s+)', r'\1\n\2', cleaned)

    return cleaned.strip()
