"""
parser.py — BeautifulSoup HTML parsing for student result tables.

Extracts student name, register number, and subject-wise marks dynamically.
Supports handling multiple semester tables to track historical backlogs.
"""

import re
from bs4 import BeautifulSoup, Tag
import logging

logger = logging.getLogger(__name__)

# Header labels (case-insensitive matching)
NAME_LABELS = ["name of the candidate", "name of the student", "name"]
REGNO_LABELS = ["register number", "register no", "reg no"]
DEGREE_LABELS = ["degree", "programme", "branch"]
DOB_LABELS = ["dob", "date of birth"]
MONTH_YEAR_LABELS = ["month", "year", "exam"]
SEM_LABELS = ["semester", "sem"]

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

roman_to_int = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8}

def parse_html_table(html_content: str) -> list[dict]:
    """
    Parses the full page HTML, finds all result tables, and returns a list of semester results.
    """
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        tables = soup.find_all("table")
        
        if not tables:
            logger.error("No tables found in HTML")
            return []

        all_semesters = []
        global_name = "UNKNOWN"
        global_reg = "UNKNOWN"
        global_degree = "UNKNOWN"
        global_dob = "UNKNOWN"
        exam_month_year = "UNKNOWN"
        semester_roman_global = "UNKNOWN"

        for table in tables:
            header_text = table.get_text(separator=" ").lower()
            if "course code" not in header_text and "sub code" not in header_text and "subject code" not in header_text:
                continue

            sub_code_idx, sub_name_idx, int_idx, ext_idx, tot_idx, res_idx = 0, 1, -1, -1, -1, -1
            thead = table.find("thead")
            rows = thead.find_all("tr") if thead else table.find_all("tr")

            for row in rows:
                for strong in row.find_all("strong"):
                    text = strong.get_text(separator=" ").strip()
                    text_lower = text.lower()
                    for label in NAME_LABELS:
                        if label in text_lower:
                            val = _extract_after_colon(text, label) or _extract_after_br(str(strong))
                            if val: global_name = val
                    for label in REGNO_LABELS:
                        if label in text_lower:
                            val = _extract_after_colon(text, label) or _extract_after_br(str(strong))
                            if val: global_reg = val
                    for label in DEGREE_LABELS:
                        if label in text_lower:
                            val = _extract_after_colon(text, label) or _extract_after_br(str(strong))
                            if val: global_degree = val
                    for label in DOB_LABELS:
                        if label in text_lower:
                            val = _extract_after_colon(text, label) or _extract_after_br(str(strong))
                            if val: global_dob = val
                    for label in MONTH_YEAR_LABELS:
                        if label in text_lower and ("month" in text_lower or "year" in text_lower):
                            val = _extract_after_colon(text, label) or _extract_after_br(str(strong))
                            if val: exam_month_year = val
                    for label in SEM_LABELS:
                        if label in text_lower:
                            val = _extract_after_colon(text, label) or _extract_after_br(str(strong))
                            if val: semester_roman_global = val

                all_ths = row.find_all(["th", "td"])
                for i, th in enumerate(all_ths):
                    th_text = th.get_text(strip=True).lower()
                    if "course code" in th_text or "subject code" in th_text or "sub code" in th_text: sub_code_idx = i
                    elif "course title" in th_text or "subject name" in th_text or "title" in th_text: sub_name_idx = i
                    elif "internal" in th_text or "int" in th_text: int_idx = i
                    elif "external" in th_text or "ext" in th_text: ext_idx = i
                    elif "total" in th_text or "tot" in th_text: tot_idx = i
                    elif "result" in th_text or "status" in th_text: res_idx = i

            if tot_idx == -1: tot_idx = -2
            if res_idx == -1: res_idx = -1

            tbody = table.find("tbody")
            data_rows = tbody.find_all("tr") if tbody else [r for r in table.find_all("tr") if r.find("td")]
            
            # Group subjects by semester
            grouped_subjects = {}

            for row in data_rows:
                cols = row.find_all("td")
                if len(cols) < 5: continue

                if sub_code_idx < len(cols):
                    subject_code = cols[sub_code_idx].get_text(strip=True)
                else:
                    continue
                    
                if not subject_code or subject_code.lower() == "course code": continue

                subject_name = cols[sub_name_idx].get_text(strip=True) if sub_name_idx < len(cols) else "Unknown"
                internal = cols[int_idx].get_text(strip=True) if int_idx != -1 and int_idx < len(cols) else "0"
                external = cols[ext_idx].get_text(strip=True) if ext_idx != -1 and ext_idx < len(cols) else "0"
                total_str = cols[tot_idx].get_text(strip=True) if tot_idx < len(cols) else "0"
                result_str = cols[res_idx].get_text(strip=True) if res_idx < len(cols) else "Unknown"

                if not total_str or total_str == "-" or total_str.lower() in ("ab", "absent", "aaa"):
                    total_str = "-"
                    
                if "pass" in result_str.lower():
                    status = "PASS"
                elif "ra" in result_str.lower() or "fail" in result_str.lower():
                    status = "FAIL"
                elif "aaa" in result_str.lower() or "ab" in result_str.lower():
                    status = "ABSENT"
                else:
                    status = result_str.upper()

                marks = int(total_str) if str(total_str).isdigit() else 0
                grade = get_grade(marks) if total_str != "-" else "U"

                # Extract semester number from subject code (e.g., 21UCSC51 -> 5)
                # We find the first digit that appears after letters
                match = re.search(r'[A-Za-z]+(\d)', subject_code)
                sem_number = int(match.group(1)) if match else 1
                
                if sem_number not in grouped_subjects:
                    grouped_subjects[sem_number] = []
                    
                grouped_subjects[sem_number].append({
                    "subject_code": subject_code,
                    "subject_name": subject_name,
                    "internal_marks": int(internal) if str(internal).isdigit() else 0,
                    "external_marks": int(external) if str(external).isdigit() else 0,
                    "total_marks": marks,
                    "grade": grade,
                    "status": status
                })

            for sem_num, subjects_list in grouped_subjects.items():
                overall_status = "PASS"
                total_score = 0
                total_gpa_points = 0.0
                total_subjects = len(subjects_list)
                
                for subj in subjects_list:
                    if subj["status"] != "PASS":
                        overall_status = "FAIL"
                    total_score += subj["total_marks"]
                    total_gpa_points += get_gpa_points(subj["total_marks"])
                
                average_score = round(total_score / total_subjects, 2) if total_subjects > 0 else 0.0
                sgpa = round(total_gpa_points / total_subjects, 2) if total_subjects > 0 else 0.0
                
                # Roman numeral fallback if missing
                roman_numerals = {1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V', 6: 'VI', 7: 'VII', 8: 'VIII'}
                sem_roman = roman_numerals.get(sem_num, semester_roman_global)
                
                all_semesters.append({
                    "semester_number": sem_num,
                    "semester_roman": sem_roman,
                    "exam_month_year": exam_month_year,
                    "degree_branch": global_degree,
                    "dob": global_dob,
                    "sgpa": sgpa,
                    "cgpa": sgpa,
                    "total_score": total_score,
                    "average_score": average_score,
                    "status": overall_status,
                    "subjects": subjects_list
                })

        logger.info(f"Parsed {len(all_semesters)} semesters from table groups for {global_reg}")
        return all_semesters

    except Exception as e:
        logger.error(f"Failed to parse HTML: {e}")
        return []