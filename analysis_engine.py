import json
from database import (
    get_student_attendance,
    get_student_marks,
    get_config,
    get_subject_by_code
)
from calculator import calculate_attendance_metrics, calculate_required_marks


def analyze_student_performance(student_reg_no: str):
    """
    Perform a complete, deterministic, real-data AI academic analysis for a student.
    Strictly uses actual records from the database.
    """
    attendance_records = get_student_attendance(student_reg_no)
    marks_records = get_student_marks(student_reg_no)

    attendance_threshold = float(get_config("attendance_threshold", 75.0))
    pass_pct = float(get_config("pass_percentage", 40.0))

    if not attendance_records and not marks_records:
        return {
            "has_data": False,
            "status": "Insufficient Data for Analysis",
            "message": "No attendance or marks records found for this student. Enter actual records to generate an academic analysis.",
            "risk_level": "Unknown",
            "risk_reasons": ["No academic records available in database."],
            "attendance_summary": {},
            "marks_summary": {},
            "subject_analyses": {},
            "weak_subjects": [],
            "strong_subjects": [],
            "attendance_shortages": []
        }

    # 1. Attendance Analysis
    total_conducted_all = 0
    total_attended_all = 0
    attendance_shortages = []
    subject_attendance_map = {}

    for rec in attendance_records:
        cond = rec["total_conducted"]
        att = rec["classes_attended"]
        subj_code = rec["subject_code"]
        subj_name = rec.get("subject_name", subj_code)
        planned = rec.get("total_planned_classes", 60)

        total_conducted_all += cond
        total_attended_all += att

        metrics = calculate_attendance_metrics(
            attended=att,
            total=cond,
            target_percent=attendance_threshold,
            planned_total=planned
        )
        metrics["subject_name"] = subj_name
        metrics["subject_code"] = subj_code
        subject_attendance_map[subj_code] = metrics

        if metrics["current_percentage"] < attendance_threshold and cond > 0:
            attendance_shortages.append({
                "subject_code": subj_code,
                "subject_name": subj_name,
                "current_percentage": metrics["current_percentage"],
                "shortage": metrics["shortage"],
                "consecutive_required": metrics["consecutive_required"],
                "achievable": metrics["achievable"],
                "explanation": metrics["explanation"]
            })

    overall_attendance_pct = round((total_attended_all / total_conducted_all * 100.0), 2) if total_conducted_all > 0 else 0.0

    # 2. Marks Analysis
    subject_marks_map = {}
    total_obtained_all = 0.0
    total_max_evaluated_all = 0.0
    weak_subjects = []
    strong_subjects = []

    for m in marks_records:
        subj_code = m["subject_code"]
        subj_name = m.get("subject_name", subj_code)
        subj_total_max = m.get("total_max", 100.0)
        subj_pass_mark = m.get("pass_mark", 40.0)

        # Break down internal and external marks
        # Evaluate what assessments have been entered
        evaluated_components = []
        comp_obtained = 0.0
        comp_max = 0.0

        if m["quiz"] is not None:
            evaluated_components.append(("Quiz", m["quiz"], m["quiz_max"]))
            comp_obtained += m["quiz"]
            comp_max += m["quiz_max"]
        if m["assignment"] is not None:
            evaluated_components.append(("Assignment", m["assignment"], m["assignment_max"]))
            comp_obtained += m["assignment"]
            comp_max += m["assignment_max"]
        if m["fa1"] is not None:
            evaluated_components.append(("FA1", m["fa1"], m["fa1_max"]))
            comp_obtained += m["fa1"]
            comp_max += m["fa1_max"]
        if m["fa2"] is not None:
            evaluated_components.append(("FA2", m["fa2"], m["fa2_max"]))
            comp_obtained += m["fa2"]
            comp_max += m["fa2_max"]
        if m["midterm1"] is not None:
            evaluated_components.append(("Midterm 1", m["midterm1"], m["midterm1_max"]))
            comp_obtained += m["midterm1"]
            comp_max += m["midterm1_max"]
        if m["midterm2"] is not None:
            evaluated_components.append(("Midterm 2", m["midterm2"], m["midterm2_max"]))
            comp_obtained += m["midterm2"]
            comp_max += m["midterm2_max"]
        if m["internal_exam"] is not None and not evaluated_components:
            # Direct internal entry
            evaluated_components.append(("Internal Exam", m["internal_exam"], m["internal_max"]))
            comp_obtained += m["internal_exam"]
            comp_max += m["internal_max"]

        if m["semester_exam"] is not None:
            evaluated_components.append(("Semester Exam", m["semester_exam"], m["semester_max"]))
            comp_obtained += m["semester_exam"]
            comp_max += m["semester_max"]

        current_obtained = comp_obtained
        current_max = comp_max if comp_max > 0 else subj_total_max
        current_pct = round((current_obtained / current_max * 100.0), 2) if current_max > 0 else 0.0

        total_obtained_all += current_obtained
        total_max_evaluated_all += current_max

        # Required marks calculations for this subject
        calc_pass = calculate_required_marks(current_obtained, current_max, subj_total_max, subj_pass_mark, pass_pct)
        calc_60 = calculate_required_marks(current_obtained, current_max, subj_total_max, subj_pass_mark, 60.0)
        calc_70 = calculate_required_marks(current_obtained, current_max, subj_total_max, subj_pass_mark, 70.0)
        calc_80 = calculate_required_marks(current_obtained, current_max, subj_total_max, subj_pass_mark, 80.0)

        subject_info = {
            "subject_code": subj_code,
            "subject_name": subj_name,
            "current_obtained": round(current_obtained, 2),
            "current_max": round(current_max, 2),
            "current_percentage": current_pct,
            "total_subject_max": subj_total_max,
            "pass_mark": subj_pass_mark,
            "components": evaluated_components,
            "required_to_pass": calc_pass["required_to_pass"],
            "pass_achievable": calc_pass["pass_achievable"],
            "targets": {
                "pass": calc_pass,
                "60": calc_60,
                "70": calc_70,
                "80": calc_80
            }
        }
        subject_marks_map[subj_code] = subject_info

        # Categorize strong vs weak subjects
        if current_pct < pass_pct or not calc_pass["pass_achievable"] or (current_max > 0 and current_pct < 50.0):
            weak_subjects.append({
                "subject_code": subj_code,
                "subject_name": subj_name,
                "current_percentage": current_pct,
                "current_obtained": current_obtained,
                "current_max": current_max,
                "required_to_pass": calc_pass["required_to_pass"],
                "reason": f"Scoring {current_pct}% ({current_obtained}/{current_max}), below pass/good standing threshold."
            })
        elif current_pct >= 75.0:
            strong_subjects.append({
                "subject_code": subj_code,
                "subject_name": subj_name,
                "current_percentage": current_pct,
                "current_obtained": current_obtained,
                "current_max": current_max
            })

    overall_marks_pct = round((total_obtained_all / total_max_evaluated_all * 100.0), 2) if total_max_evaluated_all > 0 else 0.0

    # 3. Academic Risk Assessment
    risk_level = "Low Risk"
    risk_reasons = []

    # Check for High Risk triggers
    high_risk_reasons = []
    for shortage in attendance_shortages:
        if shortage["current_percentage"] < 65.0:
            high_risk_reasons.append(f"Critical attendance shortage in {shortage['subject_name']}: {shortage['current_percentage']}% (requires {shortage['consecutive_required']} consecutive classes).")
        elif not shortage["achievable"]:
            high_risk_reasons.append(f"Attendance in {shortage['subject_name']} cannot mathematically reach {attendance_threshold}%.")

    for subj_code, s_info in subject_marks_map.items():
        if not s_info["pass_achievable"]:
            high_risk_reasons.append(f"Passing in {s_info['subject_name']} is mathematically unachievable.")
        elif s_info["targets"]["pass"]["required_pct_on_remaining"] > 75.0:
            high_risk_reasons.append(f"High risk in {s_info['subject_name']}: Needs {s_info['targets']['pass']['required_pct_on_remaining']}% on remaining assessments to pass.")
        elif s_info["current_max"] >= 30 and s_info["current_percentage"] < pass_pct:
            high_risk_reasons.append(f"Currently failing {s_info['subject_name']} with {s_info['current_percentage']}% (Passing threshold: {pass_pct}%).")

    if overall_marks_pct < 45.0 and total_max_evaluated_all >= 50:
        high_risk_reasons.append(f"Overall academic marks average is {overall_marks_pct}%, indicating severe academic distress.")

    if len(attendance_shortages) >= 3:
        high_risk_reasons.append(f"Widespread attendance shortage across {len(attendance_shortages)} subjects.")

    # Check for Medium Risk triggers
    medium_risk_reasons = []
    if not high_risk_reasons:
        for shortage in attendance_shortages:
            if 65.0 <= shortage["current_percentage"] < attendance_threshold:
                medium_risk_reasons.append(f"Attendance warning in {shortage['subject_name']}: {shortage['current_percentage']}% (Need {shortage['consecutive_required']} consecutive classes for {attendance_threshold}%).")

        for subj_code, s_info in subject_marks_map.items():
            if pass_pct <= s_info["current_percentage"] < 60.0:
                medium_risk_reasons.append(f"Borderline performance in {s_info['subject_name']} ({s_info['current_percentage']}%).")
            elif s_info["targets"]["pass"]["required_pct_on_remaining"] > 50.0:
                medium_risk_reasons.append(f"Moderate effort required in {s_info['subject_name']}: Needs {s_info['targets']['pass']['required_pct_on_remaining']}% on remaining exams to pass.")

        if 45.0 <= overall_marks_pct < 60.0 and total_max_evaluated_all > 0:
            medium_risk_reasons.append(f"Overall marks average ({overall_marks_pct}%) is below first-division standard (60%).")

    # Final Risk Assignment
    if high_risk_reasons:
        risk_level = "High Risk"
        risk_reasons = high_risk_reasons
    elif medium_risk_reasons:
        risk_level = "Medium Risk"
        risk_reasons = medium_risk_reasons
    else:
        risk_level = "Low Risk"
        reasons = []
        if overall_attendance_pct >= attendance_threshold and total_conducted_all > 0:
            reasons.append(f"Attendance is healthy at {overall_attendance_pct}% across all subjects.")
        if overall_marks_pct >= 60.0:
            reasons.append(f"Good academic performance with {overall_marks_pct}% overall marks average.")
        if not reasons:
            reasons.append("Academic records satisfy all institutional thresholds.")
        risk_reasons = reasons

    # Sort subjects to identify absolute strongest and weakest
    all_subj_codes = set(list(subject_attendance_map.keys()) + list(subject_marks_map.keys()))
    strongest_subject = None
    weakest_subject = None
    if subject_marks_map:
        sorted_by_marks = sorted(subject_marks_map.values(), key=lambda x: x["current_percentage"], reverse=True)
        strongest_subject = sorted_by_marks[0]["subject_name"]
        weakest_subject = sorted_by_marks[-1]["subject_name"]

    return {
        "has_data": True,
        "status": "Analysis Complete",
        "attendance_threshold": attendance_threshold,
        "pass_percentage": pass_pct,
        "overall_attendance_pct": overall_attendance_pct,
        "total_conducted_all": total_conducted_all,
        "total_attended_all": total_attended_all,
        "overall_marks_pct": overall_marks_pct,
        "total_obtained_all": round(total_obtained_all, 2),
        "total_max_evaluated_all": round(total_max_evaluated_all, 2),
        "risk_level": risk_level,
        "risk_reasons": risk_reasons,
        "subject_attendance": subject_attendance_map,
        "subject_marks": subject_marks_map,
        "weak_subjects": weak_subjects,
        "strong_subjects": strong_subjects,
        "attendance_shortages": attendance_shortages,
        "strongest_subject": strongest_subject or "N/A",
        "weakest_subject": weakest_subject or "N/A",
        "total_subjects_tracked": len(all_subj_codes)
    }
