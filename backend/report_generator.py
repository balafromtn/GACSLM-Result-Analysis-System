import json
import statistics
from jinja2 import Environment, FileSystemLoader

def roman_to_int(roman: str) -> int:
    roman_values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    roman = str(roman).strip().upper()
    total = 0
    prev_value = 0
    for char in reversed(roman):
        if char not in roman_values:
            continue
        value = roman_values[char]
        if value < prev_value:
            total -= value
        else:
            total += value
        prev_value = value
    return total if total > 0 else 0

def generate_report_html(scraped_results: list[dict]) -> str:
    if not scraped_results:
        return "<h1>No data available</h1>"

    # Step 1: Find the max/current semester across the batch
    max_sem_val = 0
    degree_branch = "Unknown"
    exam_month_year = "Unknown"
    
    for result in scraped_results:
        if result.get("degree_branch") and result["degree_branch"] != "UNKNOWN":
            degree_branch = result["degree_branch"]
        if result.get("exam_month_year") and result["exam_month_year"] != "UNKNOWN":
            exam_month_year = result["exam_month_year"]
            
        for subj in result.get("subjects", []):
            sem_val = roman_to_int(subj.get("semester", ""))
            if sem_val > max_sem_val:
                max_sem_val = sem_val

    # Step 2: Categorize subjects
    core_codes = set()
    arrear_codes = set()
    for result in scraped_results:
        for subj in result.get("subjects", []):
            code = subj.get("code")
            sem_val = roman_to_int(subj.get("semester", ""))
            if sem_val == max_sem_val:
                core_codes.add(code)
            else:
                arrear_codes.add(code)

    core_codes = sorted(list(core_codes))
    arrear_codes = sorted(list(arrear_codes))

    # Step 3: Compute student-level data
    students = []
    subject_stats = {}
    for code in core_codes + arrear_codes:
        subject_stats[code] = {"attempted": 0, "absent": 0, "not_opted": 0, "marks": []}

    for result in scraped_results:
        name = result.get("name", "UNKNOWN")
        reg = result.get("register_no", "UNKNOWN")
        gender = result.get("gender", "UNKNOWN")
        
        marks_dict = {}
        total = 0
        core_attempted = 0
        core_absent = 0
        core_not_opted = 0
        arrear_attempts = []
        
        # Populate all marks with "-" first
        for code in core_codes:
            marks_dict[code] = "-"
            
        # Parse student's subjects
        for subj in result.get("subjects", []):
            code = subj.get("code")
            total_mark = subj.get("total", "-")
            sem_val = roman_to_int(subj.get("semester", ""))
            
            if code in core_codes:
                marks_dict[code] = total_mark
                if total_mark == "-":
                    core_not_opted += 1
                    subject_stats[code]["not_opted"] += 1
                elif total_mark.upper() in ["AA", "ABSENT", "AB"]:
                    core_absent += 1
                    subject_stats[code]["absent"] += 1
                    subject_stats[code]["attempted"] += 1
                else:
                    try:
                        mark_val = int(total_mark)
                        total += mark_val
                        core_attempted += 1
                        subject_stats[code]["attempted"] += 1
                        subject_stats[code]["marks"].append(mark_val)
                    except:
                        pass
            elif code in arrear_codes:
                arrear_attempts.append([code, total_mark])
                if total_mark.upper() in ["AA", "ABSENT", "AB"]:
                    subject_stats[code]["absent"] += 1
                    subject_stats[code]["attempted"] += 1
                elif total_mark != "-":
                    try:
                        subject_stats[code]["attempted"] += 1
                        subject_stats[code]["marks"].append(int(total_mark))
                    except:
                        pass
                        
        students.append({
            "name": name,
            "reg": reg,
            "gender": gender,
            "marks": marks_dict,
            "total": total,
            "core_attempted": core_attempted,
            "core_absent": core_absent,
            "core_not_opted": core_not_opted,
            "arrear_attempts": arrear_attempts
        })

    # Sort students by rank (descending total)
    students.sort(key=lambda x: x["total"], reverse=True)
    for i, s in enumerate(students):
        # Handle ties
        if i > 0 and s["total"] == students[i-1]["total"]:
            s["rank"] = students[i-1]["rank"]
        else:
            s["rank"] = i + 1

    # Finalize Subject Stats
    core_avg_list = []
    for code, stats in subject_stats.items():
        if stats["marks"]:
            stats["avg"] = round(statistics.mean(stats["marks"]), 2)
            stats["max"] = max(stats["marks"])
            stats["min"] = min(stats["marks"])
        else:
            stats["avg"] = 0
            stats["max"] = 0
            stats["min"] = 0
        del stats["marks"] # Remove raw marks array for JSON output
        
        if code in core_codes and stats["avg"] > 0:
            core_avg_list.append([code, stats["avg"]])
            
    core_avg_sorted = sorted(core_avg_list, key=lambda x: x[1], reverse=True)

    # Batch Stats
    totals = [s["total"] for s in students if s["total"] > 0]
    avg_all = round(statistics.mean([s["total"] for s in students]), 2) if students else 0
    avg_nonzero = round(statistics.mean(totals), 2) if totals else 0
    
    fully_absent = [s["name"] for s in students if s["core_absent"] > 0 and s["total"] == 0]
    partial_absent = [s["name"] for s in students if s["core_absent"] > 0 and s["total"] > 0]
    n_with_arrear = len([s for s in students if len(s["arrear_attempts"]) > 0])

    DATA = {
        "students": [{k: v for k, v in s.items() if k != "gender"} for s in students],
        "core_codes": core_codes,
        "arrear_codes": arrear_codes,
        "subject_stats": subject_stats,
        "avg_nonzero": avg_nonzero,
        "avg_all": avg_all,
        "fully_absent": fully_absent,
        "partial_absent": partial_absent,
        "n_with_arrear": n_with_arrear,
        "core_avg_sorted": core_avg_sorted
    }

    # Gender Stats
    males = [s for s in students if s["gender"].lower() in ["male", "m"]]
    females = [s for s in students if s["gender"].lower() in ["female", "f"]]
    
    def calc_gender_stats(g_students):
        count = len(g_students)
        if count == 0:
            return {"count": 0, "avg_all": 0, "avg_nonzero": 0, "fully_absent": 0, "topper": "-", "topper_total": 0}, {}
        
        totals_all = [s["total"] for s in g_students]
        totals_nz = [s["total"] for s in g_students if s["total"] > 0]
        f_absent = len([s for s in g_students if s["core_absent"] > 0 and s["total"] == 0])
        topper = max(g_students, key=lambda x: x["total"])
        
        stats = {
            "count": count,
            "avg_all": round(statistics.mean(totals_all), 2),
            "avg_nonzero": round(statistics.mean(totals_nz), 2) if totals_nz else 0,
            "fully_absent": f_absent,
            "topper": topper["name"],
            "topper_total": topper["total"]
        }
        
        core_avg = {}
        for code in core_codes:
            marks = []
            for s in g_students:
                m = s["marks"].get(code, "-")
                if m != "-" and m.upper() not in ["AA", "ABSENT", "AB"]:
                    try:
                        marks.append(int(m))
                    except:
                        pass
            core_avg[code] = round(statistics.mean(marks), 2) if marks else 0
            
        return stats, core_avg

    male_stats, male_core_avg = calc_gender_stats(males)
    female_stats, female_core_avg = calc_gender_stats(females)
    
    GENDER_DATA = {
        "male_stats": male_stats,
        "female_stats": female_stats,
        "male_core_avg": male_core_avg,
        "female_core_avg": female_core_avg
    }

    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("report.html")
    
    html_out = template.render(
        degree_branch=degree_branch,
        exam_month_year=exam_month_year,
        data_json=json.dumps(DATA),
        gender_json=json.dumps(GENDER_DATA)
    )
    
    return html_out
