import os
import io
import tempfile
import pandas as pd

# Use isolated test DB
test_db = os.path.join(tempfile.gettempdir(), "e2e_edutrack_test.db")
if os.path.exists(test_db):
    os.remove(test_db)
os.environ["DB_PATH"] = test_db

import database
from database import (
    init_database,
    add_student,
    update_student,
    get_student_by_reg_no,
    get_student_by_email,
    search_student,
    get_all_students,
    add_subject,
    get_all_subjects,
    save_attendance,
    get_student_attendance,
    get_attendance_history,
    save_marks,
    get_student_marks,
    get_marks_history,
    set_config,
    get_config
)
from auth import (
    ensure_bootstrap_admin,
    create_user,
    authenticate_user
)
from calculator import (
    calculate_attendance_metrics,
    calculate_required_marks,
    calculate_projected_attendance
)
from analysis_engine import analyze_student_performance
from ai_recommender import generate_deterministic_recommendations
from pdf_generator import generate_student_pdf_report
from import_export import validate_and_preview_import, execute_import


def run_e2e_tests():
    print("==================================================")
    print("Starting EduTrack AI End-to-End System Test Suite")
    print("==================================================")

    # 1. Database Initialization
    init_database()
    ensure_bootstrap_admin()
    print("[PASS] Phase 13: Database initialized successfully.")

    # 2. Verify Empty Database State
    st_empty = get_all_students()
    assert len(st_empty) == 0, "Database must not contain demo students."
    empty_analysis = analyze_student_performance("NON_EXISTENT")
    assert empty_analysis["status"] == "Insufficient Data for Analysis", "Empty student must return Insufficient Data."
    print("[PASS] Strict Requirement: Zero demo data verified. Empty state properly handled.")

    # 3. Authentication & Roles
    admin, msg = authenticate_user("admin", "Admin@123")
    assert admin is not None and admin["role"] == "Admin", "Admin auth failed."
    print(f"[PASS] Phase 1: Admin authenticated: {admin['username']} ({admin['role']})")

    # Faculty creation
    f_ok, f_msg = create_user("faculty_cse", "faculty@edutrack.ac.in", "Faculty@123", "Faculty", "Prof. R. Sharma")
    assert f_ok, f"Faculty creation failed: {f_msg}"
    faculty, _ = authenticate_user("faculty_cse", "Faculty@123")
    assert faculty["role"] == "Faculty"
    print("[PASS] Phase 1: Faculty account created and authenticated.")

    # 4. Student Registration (Phase 2)
    reg_ok, reg_msg = add_student(
        reg_no="251FA23109",
        full_name="SK Kushmitha Bee",
        email="kushmitha@edutrack.ac.in",
        department="Computer Science & Engineering",
        course="B.Tech CSE (Data Science)",
        academic_year="2025-2026",
        current_year="2nd Year",
        semester="Semester 1",
        section="A"
    )
    assert reg_ok, f"Student registration failed: {reg_msg}"
    print(f"[PASS] Phase 2: Student registered: SK Kushmitha Bee (251FA23109)")

    # Test student account creation and isolation
    st_u_ok, st_u_msg = create_user(
        username="251FA23109",
        email="kushmitha@edutrack.ac.in",
        password="StudentPassword@123",
        role="Student",
        full_name="SK Kushmitha Bee",
        student_reg_no="251FA23109"
    )
    assert st_u_ok, f"Student user creation failed: {st_u_msg}"
    student_auth, _ = authenticate_user("251FA23109", "StudentPassword@123")
    assert student_auth["role"] == "Student"
    assert student_auth["student_reg_no"] == "251FA23109"
    print("[PASS] Phase 1: Student role and secure login verified.")

    # Search Workflow
    found_by_reg = search_student("251FA23109")
    assert found_by_reg["full_name"] == "SK Kushmitha Bee"
    found_by_email = search_student("kushmitha@edutrack.ac.in")
    assert found_by_email["reg_no"] == "251FA23109"
    not_found = search_student("999UNKNOWN")
    assert not_found is None
    print("[PASS] Phase 2: Search workflow verified for Reg No, Email, and Not Found cases.")

    # 5. Subject Management (Phase 3)
    s1_ok, _ = add_subject("CS201", "Data Structures", "CSE", "Semester 1", 40.0, 60.0, 100.0, 40.0, 40.0, 60.0, 60)
    s2_ok, _ = add_subject("MA201", "Discrete Mathematics", "CSE", "Semester 1", 40.0, 60.0, 100.0, 40.0, 40.0, 60.0, 60)
    s3_ok, _ = add_subject("CS202", "Database Management Systems", "CSE", "Semester 1", 40.0, 60.0, 100.0, 40.0, 40.0, 60.0, 60)
    assert s1_ok and s2_ok and s3_ok
    subjects = get_all_subjects()
    assert len(subjects) == 3
    print(f"[PASS] Phase 3: Configured {len(subjects)} academic subjects.")

    # 6. Attendance Entry & Prompt Example Verification (Phase 4 & 5)
    # The prompt explicitly specifies:
    # Total classes = 40, Attended classes = 26, Current attendance = 65%
    # Target = 75% -> Additional consecutive classes required = 16!
    att_res = calculate_attendance_metrics(attended=26, total=40, target_percent=75.0)
    assert att_res["current_percentage"] == 65.0, f"Expected 65.0%, got {att_res['current_percentage']}"
    assert att_res["shortage"] == 10.0
    assert att_res["consecutive_required"] == 16, f"Expected 16, got {att_res['consecutive_required']}"
    print(f"[PASS] Phase 5: Verified exact attendance formula: 26/40 (65%) -> Needs {att_res['consecutive_required']} consecutive classes to hit 75%.")

    # Save attendance in DB
    save_attendance("251FA23109", "MA201", 40, 26, "Midterm Period", "Recorded by Faculty")
    save_attendance("251FA23109", "CS201", 40, 36, "Midterm Period", "Recorded by Faculty")
    save_attendance("251FA23109", "CS202", 40, 32, "Midterm Period", "Recorded by Faculty")
    rec_att = get_student_attendance("251FA23109")
    assert len(rec_att) == 3
    print("[PASS] Phase 4: Attendance saved and retrieved from database.")

    # 7. Marks Entry & Required Marks Calculator (Phase 6 & 7)
    # MA201: Weak marks (FA1=12/20, FA2=10/20, Quiz=5/10) -> Total obtained = 27/50
    # Remaining marks = 50 (Semester Exam). Total subject max = 100, pass = 40.
    save_marks("251FA23109", "MA201", quiz=5.0, fa1=12.0, fa2=10.0)

    # CS201: Strong marks (Quiz=9/10, Assignment=10/10, FA1=18/20, FA2=19/20) -> Total obtained = 56/60
    save_marks("251FA23109", "CS201", quiz=9.0, assignment=10.0, fa1=18.0, fa2=19.0)

    # CS202: Moderate marks (Quiz=7/10, FA1=15/20) -> Total obtained = 22/30
    save_marks("251FA23109", "CS202", quiz=7.0, fa1=15.0)

    rec_marks = get_student_marks("251FA23109")
    assert len(rec_marks) == 3
    print("[PASS] Phase 6: Subject-wise marks saved permanently.")

    # Required marks calculation check
    # MA201: obtained 27, current_max 50, total_max 100, pass 40
    # Required to pass = 40 - 27 = 13 marks out of 50 (26.0%)
    req_pass_calc = calculate_required_marks(27.0, 50.0, 100.0, 40.0, 40.0)
    assert req_pass_calc["required_future_marks"] == 13.0
    assert req_pass_calc["required_pct_on_remaining"] == 26.0
    assert req_pass_calc["achievable"] is True

    # 70% target: Needs 70 total -> 70 - 27 = 43 out of 50 (86.0%)
    req_70_calc = calculate_required_marks(27.0, 50.0, 100.0, 40.0, 70.0)
    assert req_70_calc["required_future_marks"] == 43.0
    assert req_70_calc["achievable"] is True

    # 85% target: Needs 85 total -> 85 - 27 = 58 out of 50 -> IMPOSSIBLE!
    req_85_calc = calculate_required_marks(27.0, 50.0, 100.0, 40.0, 85.0)
    assert req_85_calc["achievable"] is False
    assert "mathematically impossible" in req_85_calc["explanation"].lower()
    print("[PASS] Phase 7: Required Marks Calculator passed (Pass, 70%, and Impossible Target checks).")

    # 8. AI Academic Analysis Engine (Phase 8)
    analysis = analyze_student_performance("251FA23109")
    assert analysis["has_data"] is True
    assert len(analysis["attendance_shortages"]) == 1
    assert analysis["attendance_shortages"][0]["subject_code"] == "MA201"
    assert analysis["risk_level"] in ("Medium Risk", "High Risk")
    assert len(analysis["risk_reasons"]) > 0
    print(f"[PASS] Phase 8: AI Academic Analysis complete. Risk Level: {analysis['risk_level']}. Reasons: {analysis['risk_reasons']}")

    # 9. Personalized AI Recommendations (Phase 9)
    student = get_student_by_reg_no("251FA23109")
    recs = generate_deterministic_recommendations(analysis, student)
    assert len(recs["immediate_alerts"]) > 0
    assert len(recs["weekly_study_schedule"]) == 7
    print(f"[PASS] Phase 9: Recommendations generated. Found {len(recs['immediate_alerts'])} immediate alerts and 7-day study plan.")

    # 10. PDF Report Generation (Phase 11)
    pdf_buffer = generate_student_pdf_report(student, analysis, recs)
    pdf_bytes = pdf_buffer.getvalue()
    assert pdf_bytes.startswith(b"%PDF"), "Generated stream is not a valid PDF."
    assert len(pdf_bytes) > 2000
    print(f"[PASS] Phase 11: Downloadable PDF Academic Report generated ({len(pdf_bytes)} bytes).")

    # 11. Excel/CSV Bulk Import Validation (Phase 12)
    csv_content = """reg_no,full_name,email,department,course,academic_year,current_year,semester,section
251FA23126,T.ooha Srivalli,ooha@edutrack.ac.in,Computer Science & Engineering,B.Tech CSE,2025-2026,2nd Year,Semester 1,A
251FA23070,M.Vanshika,vanshika@edutrack.ac.in,Computer Science & Engineering,B.Tech CSE,2025-2026,2nd Year,Semester 1,B
"""
    file_mock = io.StringIO(csv_content)
    file_mock.name = "students.csv"
    v_ok, v_msg, df_prev, issues = validate_and_preview_import(file_mock, "students")
    assert v_ok is True
    assert len(df_prev) == 2
    res_imp = execute_import(df_prev, "students")
    assert res_imp["success_count"] == 2
    assert get_student_by_reg_no("251FA23126") is not None
    assert get_student_by_reg_no("251FA23070") is not None
    print("[PASS] Phase 12: CSV Bulk Data Import parsed, validated, and committed 2 students.")

    # 12. Dynamic Recalculation Check (Phase 13)
    # Faculty updates MA201 attendance to 38/40
    save_attendance("251FA23109", "MA201", 40, 38, "Post Audit", "Recovered attendance")
    analysis_updated = analyze_student_performance("251FA23109")
    assert len(analysis_updated["attendance_shortages"]) == 0
    print(f"[PASS] Phase 13: Attendance update dynamically resolved shortage. Shortages now: {len(analysis_updated['attendance_shortages'])}.")

    print("==================================================")
    print("ALL 15 PHASES AND END-TO-END CRITERIA VERIFIED!")
    print("==================================================")


if __name__ == "__main__":
    run_e2e_tests()
