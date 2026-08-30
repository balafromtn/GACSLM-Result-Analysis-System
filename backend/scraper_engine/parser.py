"""
parser.py — BeautifulSoup HTML parsing for student result tables.

Extracts student name, register number, and subject-wise marks dynamically.
Supports two table layouts:
  - Old (ecampus.cc): 8 cols, <br> in <strong>, table id="exam_datail"
  - New (SLMGACCOE): 7 cols, colon-separated text in <strong>, no table id
"""

import re
from bs4 import BeautifulSoup, Tag
import logging

logger = logging.getLogger(__name__)

TABLE_IDS = ["exam_datail", "exam_detail", "result_table"]

# Header labels (case-insensitive matching)
NAME_LABELS = ["name of the candidate", "name of the student"]
REGNO_LABELS = ["register number", "register no", "reg no"]
DEGREE_LABELS = ["degree", "programme", "branch"]
DOB_LABELS = ["dob", "date of birth"]
MONTH_YEAR_LABELS = ["month", "year", "exam"]
SEM_LABELS = ["semester", "sem"]
SUBJECT_HEADERS = ["course code", "subject code", "sub-code", "sub code"]

def _find_table(soup: BeautifulSoup) -> Tag | None:
    for tid in TABLE_IDS:
        t = soup.find("table", id=tid)
        if t:
            return t
    return soup.find("table")

def _extract_after_colon(text: str, label: str) -> str | None:
    lower = text.lower()
    idx = lower.find(label.lower() + ":")
    if idx == -1:
        idx = lower.find(label.lower() + " :")
        if idx == -1:
            return None
    val = text[idx + len(label) + 1:] if " :" not in text[idx:idx+len(label)+3] else text[idx + len(label) + 3:]
    val = val.strip().strip(":")
    return val if val else None

def _extract_after_br(html: str) -> str | None:
    if "<br" not in html:
        return None
    parts = html.split("<br", 1)
    if len(parts) < 2:
        return None
    after_br = parts[1]
    if ">" in after_br:
        after_br = after_br.split(">", 1)[1]
    val = after_br.split("</strong>")[0].strip()
    val = val.replace("</strong", "").strip()
    return val if val else None

def parse_result_html(html: str) -> dict | None:
    try:
        soup = BeautifulSoup(html, "html.parser")
        table = _find_table(soup)
        if not table:
            logger.error("No table found in HTML")
            return None

        name = "UNKNOWN"
        register_no = "UNKNOWN"
        degree_branch = "UNKNOWN"
        dob = "UNKNOWN"
        exam_month_year = "UNKNOWN"
        semester_roman = "UNKNOWN"
        
        sub_code_idx = 0
        sub_name_idx = 1
        int_idx = -1
        ext_idx = -1
        tot_idx = -1
        res_idx = -1

        thead = table.find("thead")
        rows = thead.find_all("tr") if thead else table.find_all("tr")

        for row in rows:
            for strong in row.find_all("strong"):
                text = strong.get_text(separator=" ").strip()
                text_lower = text.lower()

                for label in NAME_LABELS:
                    if label in text_lower:
                        val = _extract_after_colon(text, label) or _extract_after_br(str(strong))
                        if val: name = val
                        break

                for label in REGNO_LABELS:
                    if label in text_lower:
                        val = _extract_after_colon(text, label) or _extract_after_br(str(strong))
                        if val: register_no = val
                        break
                        
                for label in DEGREE_LABELS:
                    if label in text_lower:
                        val = _extract_after_colon(text, label) or _extract_after_br(str(strong))
                        if val: degree_branch = val
                        break
                        
                for label in DOB_LABELS:
                    if label in text_lower:
                        val = _extract_after_colon(text, label) or _extract_after_br(str(strong))
                        if val: dob = val
                        break
                        
                for label in MONTH_YEAR_LABELS:
                    if label in text_lower and ("month" in text_lower or "year" in text_lower):
                        val = _extract_after_colon(text, label) or _extract_after_br(str(strong))
                        if val: exam_month_year = val
                        break
                        
                for label in SEM_LABELS:
                    if label in text_lower:
                        val = _extract_after_colon(text, label) or _extract_after_br(str(strong))
                        if val: semester_roman = val
                        break

            # Find column indices dynamically
            all_ths = row.find_all(["th", "td"])
            for i, th in enumerate(all_ths):
                th_text = th.get_text(strip=True).lower()
                if "course code" in th_text or "subject code" in th_text or "sub code" in th_text: sub_code_idx = i
                elif "course title" in th_text or "subject name" in th_text or "title" in th_text: sub_name_idx = i
                elif "internal" in th_text or "int" in th_text: int_idx = i
                elif "external" in th_text or "ext" in th_text: ext_idx = i
                elif "total" in th_text or "tot" in th_text: tot_idx = i
                elif "result" in th_text or "status" in th_text: res_idx = i

        # Fallback for indices if not found in headers
        if tot_idx == -1: tot_idx = -2
        if res_idx == -1: res_idx = -1

        subjects = {}
        tbody = table.find("tbody")
        data_rows = tbody.find_all("tr") if tbody else [r for r in table.find_all("tr") if r.find("td")]

        for row in data_rows:
            cols = row.find_all("td")
            if len(cols) < 5: continue # Need at least a few columns

            if sub_code_idx < len(cols):
                subject_code = cols[sub_code_idx].get_text(strip=True)
            else:
                continue
                
            if not subject_code or subject_code.lower() == "course code": continue

            subject_name = cols[sub_name_idx].get_text(strip=True) if sub_name_idx < len(cols) else "Unknown"
            internal = cols[int_idx].get_text(strip=True) if int_idx != -1 and int_idx < len(cols) else "0"
            external = cols[ext_idx].get_text(strip=True) if ext_idx != -1 and ext_idx < len(cols) else "0"
            total = cols[tot_idx].get_text(strip=True) if tot_idx < len(cols) else "0"
            result_str = cols[res_idx].get_text(strip=True) if res_idx < len(cols) else "Unknown"

            if not total or total == "-" or total.lower() in ("ab", "absent", "aaa"):
                total = "-"
                
            if "pass" in result_str.lower():
                status = "PASS"
            elif "ra" in result_str.lower() or "fail" in result_str.lower():
                status = "FAIL"
            elif "aaa" in result_str.lower() or "ab" in result_str.lower():
                status = "ABSENT"
            else:
                status = result_str

            subjects[subject_code] = {
                "name": subject_name,
                "internal": internal,
                "external": external,
                "total": total,
                "status": status
            }

        result = {
            "register_no": register_no,
            "name": name,
            "degree_branch": degree_branch,
            "dob": dob,
            "exam_month_year": exam_month_year,
            "semester_roman": semester_roman,
            "subjects": subjects,
        }

        logger.info(f"Parsed: {register_no} ({name}) — {len(subjects)} subjects")
        return result

    except Exception as e:
        logger.error(f"Failed to parse HTML: {e}")
        return None

def get_grade(marks: int) -> str:
    if marks >= 90: return "O"
    if marks >= 80: return "A+"
    if marks >= 70: return "A"
    if marks >= 60: return "B+"
    if marks >= 50: return "B"
    if marks >= 40: return "C"
    return "U"

def get_gpa_points(marks: int) -> float:
    if marks >= 90: return 10.0
    if marks >= 80: return 9.0
    if marks >= 70: return 8.0
    if marks >= 60: return 7.0
    if marks >= 50: return 6.0
    if marks >= 40: return 5.0
    return 0.0

def parse_html_table(html_content: str) -> list[dict]:
    parsed_data = parse_result_html(html_content)
    
    if not parsed_data:
        return []
        
    subjects_list = []
    overall_status = "PASS"
    total_score = 0
    total_subjects = 0
    total_gpa_points = 0.0
    
    for code, details in parsed_data.get("subjects", {}).items():
        marks_str = details["total"]
        subject_name = details["name"]
        
        marks = int(marks_str) if str(marks_str).isdigit() else 0
        status = details["status"]
        grade = get_grade(marks) if marks_str != "-" else "U"
        
        if status != "PASS":
            overall_status = "FAIL"
            
        total_score += marks
        total_subjects += 1
        total_gpa_points += get_gpa_points(marks)
            
        subjects_list.append({
            "subject_code": code,
            "subject_name": subject_name,
            "internal_marks": int(details["internal"]) if str(details["internal"]).isdigit() else 0,
            "external_marks": int(details["external"]) if str(details["external"]).isdigit() else 0,
            "total_marks": marks,
            "grade": grade,
            "status": status
        })
        
    average_score = round(total_score / total_subjects, 2) if total_subjects > 0 else 0.0
    sgpa = round(total_gpa_points / total_subjects, 2) if total_subjects > 0 else 0.0
        
    return [{
        "semester_number": 1,
        "semester_roman": parsed_data.get("semester_roman"),
        "exam_month_year": parsed_data.get("exam_month_year"),
        "degree_branch": parsed_data.get("degree_branch"),
        "dob": parsed_data.get("dob"),
        "sgpa": sgpa,
        "cgpa": sgpa,
        "total_score": total_score,
        "average_score": average_score,
        "status": overall_status,
        "subjects": subjects_list
    }]