import os
import json
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")


def generate_deterministic_recommendations(analysis: dict, student_info: dict) -> dict:
    """
    Generate highly structured, personalized recommendations directly from the calculated metrics.
    Ensures zero hallucination and 100% adherence to actual database values.
    """
    name = student_info.get("full_name", "Student")
    risk_level = analysis.get("risk_level", "Low Risk")
    shortages = analysis.get("attendance_shortages", [])
    weak_subjs = analysis.get("weak_subjects", [])
    strong_subjs = analysis.get("strong_subjects", [])
    subject_marks = analysis.get("subject_marks", {})
    subject_att = analysis.get("subject_attendance", {})

    immediate_alerts = []
    subject_suggestions = []
    attendance_plan = []
    exam_prep_recommendations = []
    weekly_study_schedule = []

    # 1. Immediate Action Alerts
    for s in shortages:
        if s["consecutive_required"] > 0:
            immediate_alerts.append(
                f"Your {s['subject_name']} attendance is {s['current_percentage']}%. You need to attend the next "
                f"{s['consecutive_required']} consecutive classes without missing any to reach {analysis.get('attendance_threshold', 75.0)}%."
            )
        elif not s["achievable"]:
            immediate_alerts.append(
                f"Alert: {s['subject_name']} attendance is {s['current_percentage']}% and cannot mathematically reach "
                f"{analysis.get('attendance_threshold', 75.0)}%. Contact your academic advisor immediately."
            )

    for w in weak_subjs:
        req = w.get("required_to_pass", 0)
        immediate_alerts.append(
            f"Focus more on {w['subject_name']} based on your current examination results ({w['current_percentage']}%). "
            f"You need at least {req} more marks to satisfy the passing requirement."
        )

    if not immediate_alerts:
        immediate_alerts.append(f"Excellent work, {name}! Your attendance and academic performance are on track across all enrolled subjects.")

    # 2. Subject-wise Suggestions
    for code, s_info in subject_marks.items():
        s_name = s_info["subject_name"]
        pct = s_info["current_percentage"]
        pass_calc = s_info["targets"]["pass"]
        t_60 = s_info["targets"]["60"]
        t_80 = s_info["targets"]["80"]

        if pct < analysis.get("pass_percentage", 40.0):
            suggestion = (
                f"Critical Focus: Scored {s_info['current_obtained']}/{s_info['current_max']} ({pct}%). "
                f"You need {pass_calc['required_future_marks']} marks in upcoming examinations ({pass_calc['required_pct_on_remaining']}%) to pass."
            )
        elif pct >= 75.0:
            suggestion = (
                f"Mastery: Strong performance at {pct}%. To achieve distinction (80%+), aim for "
                f"{t_80['required_future_marks']} marks in remaining tests."
            )
        else:
            suggestion = (
                f"Moderate Progress: Currently at {pct}%. To achieve first division (60%+), "
                f"you need {t_60['required_future_marks']} marks on remaining assessments ({t_60['required_pct_on_remaining']}%)."
            )
        subject_suggestions.append({"subject": s_name, "suggestion": suggestion})

    # 3. Attendance Improvement Plan
    if shortages:
        for s in shortages:
            attendance_plan.append({
                "subject": s["subject_name"],
                "current": f"{s['current_percentage']}%",
                "target": f"{analysis.get('attendance_threshold', 75.0)}%",
                "action": f"Attend the next {s['consecutive_required']} classes consecutively without absence."
            })
    else:
        attendance_plan.append({
            "subject": "All Subjects",
            "current": f"{analysis.get('overall_attendance_pct', 0.0)}%",
            "target": f"{analysis.get('attendance_threshold', 75.0)}%",
            "action": "Maintain your regular class attendance pattern. All subjects meet institutional requirements."
        })

    # 4. Exam Preparation Recommendations
    if weak_subjs:
        for w in weak_subjs:
            exam_prep_recommendations.append(
                f"Prioritize {w['subject_name']}: Solve past question papers, clarify difficult core concepts with course faculty, and take weekly self-assessments."
            )
    else:
        exam_prep_recommendations.append("Continue standard revision cycles: Review notes at the end of each module and practice timed answer drafting.")

    # 5. Weekly Study Plan (Allocating hours proportionally to weak subjects)
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    subjects_to_schedule = [w["subject_name"] for w in weak_subjs]
    if not subjects_to_schedule:
        subjects_to_schedule = [s_info["subject_name"] for s_info in subject_marks.values()]
    if not subjects_to_schedule:
        subjects_to_schedule = ["General Coursework Revision"]

    for i, day in enumerate(days):
        assigned_subj = subjects_to_schedule[i % len(subjects_to_schedule)]
        is_weak = any(w["subject_name"] == assigned_subj for w in weak_subjs)
        hours = 2.5 if is_weak else 1.5
        task = f"Intensive problem solving and concept mastery in {assigned_subj}" if is_weak else f"Module review and practice exercises in {assigned_subj}"
        weekly_study_schedule.append({
            "day": day,
            "subject": assigned_subj,
            "hours": hours,
            "focus_task": task
        })

    return {
        "immediate_alerts": immediate_alerts,
        "subject_suggestions": subject_suggestions,
        "attendance_plan": attendance_plan,
        "exam_prep_recommendations": exam_prep_recommendations,
        "weekly_study_schedule": weekly_study_schedule,
        "generated_by": "EduTrack Deterministic Engine"
    }


def generate_ai_recommendations(analysis: dict, student_info: dict) -> dict:
    """
    Generate dynamic recommendations using Groq LLM if available, falling back to
    deterministic engine for speed, resilience, and offline capability.
    """
    if not analysis.get("has_data", False):
        return {
            "immediate_alerts": ["No academic data available yet."],
            "subject_suggestions": [],
            "attendance_plan": [],
            "exam_prep_recommendations": ["Enter attendance and marks to receive personalized recommendations."],
            "weekly_study_schedule": [],
            "generated_by": "System Notice"
        }

    # Attempt Groq LLM generation
    if GROQ_API_KEY and not GROQ_API_KEY.startswith("YOUR_"):
        try:
            from groq import Groq
            client = Groq(api_key=GROQ_API_KEY)

            prompt_payload = {
                "student_name": student_info.get("full_name", "Student"),
                "reg_no": student_info.get("reg_no", ""),
                "department": student_info.get("department", ""),
                "semester": student_info.get("semester", ""),
                "risk_level": analysis.get("risk_level"),
                "risk_reasons": analysis.get("risk_reasons"),
                "overall_attendance": analysis.get("overall_attendance_pct"),
                "overall_marks": analysis.get("overall_marks_pct"),
                "attendance_shortages": analysis.get("attendance_shortages"),
                "weak_subjects": analysis.get("weak_subjects"),
                "strong_subjects": analysis.get("strong_subjects"),
                "subject_marks": {
                    k: {
                        "name": v["subject_name"],
                        "pct": v["current_percentage"],
                        "required_to_pass": v["required_to_pass"]
                    } for k, v in analysis.get("subject_marks", {}).items()
                }
            }

            system_instruction = """
You are EduTrack AI, an expert academic counselor and early warning intelligence advisor.
Analyze the student's actual performance data and provide precise, actionable, empathetic recommendations.
Do NOT hallucinate or make up any course numbers or attendance figures. Strictly use the provided metrics.
Output valid JSON ONLY matching this structure:
{
  "immediate_alerts": ["alert string 1", "alert string 2"],
  "subject_suggestions": [{"subject": "Subject Name", "suggestion": "Actionable recommendation"}],
  "attendance_plan": [{"subject": "Subject Name", "current": "XX%", "target": "75%", "action": "Specific classes to attend"}],
  "exam_prep_recommendations": ["tip 1", "tip 2"],
  "weekly_study_schedule": [
     {"day": "Monday", "subject": "Name", "hours": 2, "focus_task": "Task description"},
     {"day": "Tuesday", "subject": "Name", "hours": 2, "focus_task": "Task description"},
     {"day": "Wednesday", "subject": "Name", "hours": 2, "focus_task": "Task description"},
     {"day": "Thursday", "subject": "Name", "hours": 2, "focus_task": "Task description"},
     {"day": "Friday", "subject": "Name", "hours": 2, "focus_task": "Task description"},
     {"day": "Saturday", "subject": "Name", "hours": 3, "focus_task": "Task description"},
     {"day": "Sunday", "subject": "Name", "hours": 2, "focus_task": "Task description"}
  ]
}
"""

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": f"Student Academic Metrics:\n{json.dumps(prompt_payload, indent=2)}"}
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
                timeout=12.0
            )

            result_content = response.choices[0].message.content
            parsed = json.loads(result_content)
            parsed["generated_by"] = "EduTrack AI (Groq Llama-3.3)"
            return parsed

        except Exception as e:
            # Fallback seamlessly to deterministic calculations
            pass

    # High-reliability fallback
    return generate_deterministic_recommendations(analysis, student_info)
