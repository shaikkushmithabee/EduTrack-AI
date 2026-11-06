import os
import unittest
import tempfile
import sqlite3

# Point DB_PATH to a temporary test database
test_db_file = os.path.join(tempfile.gettempdir(), "test_edutrack.db")
os.environ["DB_PATH"] = test_db_file

if os.path.exists(test_db_file):
    os.remove(test_db_file)

import database
from database import (
    init_database,
    add_student,
    get_student_by_reg_no,
    get_student_by_email,
    search_student,
    update_student,
    add_subject,
    save_attendance,
    get_student_attendance,
    get_attendance_history,
    save_marks,
    get_student_marks,
    get_all_students
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


class TestEduTrackSystem(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_database()
        ensure_bootstrap_admin()

    def test_01_attendance_formula_prompt_example(self):
        """
        Verify the exact mathematical example given in Phase 5 prompt:
        Total classes = 40, Attended = 26, Current = 65%
        Required = 75%
        Additional consecutive classes required must be EXACTLY 16!
        """
        metrics = calculate_attendance_metrics(attended=26, total=40, target_percent=75.0)
        self.assertEqual(metrics["current_percentage"], 65.0)
        self.assertEqual(metrics["shortage"], 10.0)
        self.assertEqual(metrics["consecutive_required"], 16)
        # Verify formula: (26 + 16) / (40 + 16) = 42 / 56 = 0.75 (75.0%)
        attended_after = 26 + 16
        total_after = 40 + 16
        self.assertGreaterEqual((attended_after / total_after) * 100.0, 75.0)
        # 15 consecutive classes must NOT be enough
        self.assertLess(((26 + 15) / (40 + 15)) * 100.0, 75.0)
        self.assertIn("16 consecutive classes", metrics["explanation"])

    def test_02_attendance_already_met(self):
        """When attendance >= 75%, consecutive_required must be 0 and buffer classes computed."""
        metrics = calculate_attendance_metrics(attended=32, total=40, target_percent=75.0)
        self.assertEqual(metrics["current_percentage"], 80.0)
        self.assertEqual(metrics["consecutive_required"], 0)
        self.assertEqual(metrics["status"], "On Track")
        self.assertGreater(metrics["buffer_classes"], 0)

    def test_03_required_marks_calculator(self):
        """
        Verify required future marks:
        Total max = 100, pass = 40.
        Current obtained = 25 out of 40 (Internal assessment evaluated).
        Remaining exam max = 60.
        """
        # Pass requirement: Needs 40 total -> 40 - 25 = 15 marks needed out of 60
        res_pass = calculate_required_marks(current_obtained=25.0, current_max=40.0, total_max=100.0, pass_mark=40.0, target_percentage=40.0)
        self.assertEqual(res_pass["required_future_marks"], 15.0)
        self.assertTrue(res_pass["achievable"])
        self.assertEqual(res_pass["required_pct_on_remaining"], 25.0)

        # 80% target: Needs 80 total -> 80 - 25 = 55 marks needed out of 60
        res_80 = calculate_required_marks(current_obtained=25.0, current_max=40.0, total_max=100.0, pass_mark=40.0, target_percentage=80.0)
        self.assertEqual(res_80["required_future_marks"], 55.0)
        self.assertTrue(res_80["achievable"])
        self.assertEqual(res_80["required_pct_on_remaining"], round(55.0/60.0*100, 2))

        # Impossible target: 90% target -> Needs 90 total -> 90 - 25 = 65 needed out of 60!
        res_90 = calculate_required_marks(current_obtained=25.0, current_max=40.0, total_max=100.0, pass_mark=40.0, target_percentage=90.0)
        self.assertFalse(res_90["achievable"])
        self.assertIn("mathematically impossible", res_90["explanation"].lower())

    def test_04_student_registration_and_search(self):
        """Phase 2: Add student, unique reg_no, search by Reg No and Email ID."""
        ok, msg = add_student(
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
        self.assertTrue(ok)

        # Search by Reg No
        s1 = search_student("251fa23109")
        self.assertIsNotNone(s1)
        self.assertEqual(s1["full_name"], "SK Kushmitha Bee")

        # Search by registered Email
        s2 = search_student("kushmitha@edutrack.ac.in")
        self.assertIsNotNone(s2)
        self.assertEqual(s2["reg_no"], "251FA23109")

        # Duplicate Reg No rejection
        dup_ok, _ = add_student("251FA23109", "Duplicate", "other@edutrack.ac.in", "CSE", "B.Tech", "2025", "1", "1", "A")
        self.assertFalse(dup_ok)

        # Non-existent student search
        non_exist = search_student("NONEXISTENT999")
        self.assertIsNone(non_exist)

    def test_05_subject_management(self):
        """Phase 3: Add subjects."""
        ok, _ = add_subject("CS201", "Data Structures", "CSE", "Semester 1", 40.0, 60.0, 100.0, 40.0, 40.0, 60.0, 60)
        self.assertTrue(ok)
        ok2, _ = add_subject("MA201", "Applied Mathematics", "CSE", "Semester 1", 40.0, 60.0, 100.0, 40.0, 40.0, 60.0, 60)
        self.assertTrue(ok2)

    def test_06_attendance_and_history(self):
        """Phase 4: Save and update attendance, verify validation and history."""
        # Validation: attended > total
        bad_ok, _ = save_attendance("251FA23109", "MA201", 30, 35)
        self.assertFalse(bad_ok)

        # Valid entry matching prompt example (40 conducted, 26 attended)
        ok, _ = save_attendance("251FA23109", "MA201", 40, 26, "Aug-Sep", "Midterm Audit")
        self.assertTrue(ok)

        records = get_student_attendance("251FA23109")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["classes_attended"], 26)

        # Update attendance
        ok_upd, _ = save_attendance("251FA23109", "MA201", 42, 28, "Aug-Oct", "Updated")
        self.assertTrue(ok_upd)

        # Check history
        history = get_attendance_history("251FA23109", "MA201")
        self.assertGreaterEqual(len(history), 2)

    def test_07_marks_management_and_analysis(self):
        """Phase 6 & 8: Save marks, run AI academic analysis and risk classification."""
        # Save marks in CS201 (strong performance: FA1=18, FA2=19, Midterm1=28)
        ok, _ = save_marks("251FA23109", "CS201", fa1=18.0, fa2=19.0, midterm1=28.0)
        self.assertTrue(ok)

        # Reset MA201 attendance to 26/40 to trigger the warning
        save_attendance("251FA23109", "MA201", 40, 26)
        # Save marks in MA201 (weak performance: FA1=10, FA2=11)
        save_marks("251FA23109", "MA201", fa1=10.0, fa2=11.0)

        analysis = analyze_student_performance("251FA23109")
        self.assertTrue(analysis["has_data"])
        self.assertIn(analysis["risk_level"], ["Medium Risk", "High Risk"])
        self.assertGreaterEqual(len(analysis["attendance_shortages"]), 1)
        self.assertEqual(analysis["attendance_shortages"][0]["subject_code"], "MA201")
        self.assertEqual(analysis["attendance_shortages"][0]["consecutive_required"], 16)

    def test_08_personalized_recommendations(self):
        """Phase 9: Verify personalized recommendations contain real metrics."""
        student = get_student_by_reg_no("251FA23109")
        analysis = analyze_student_performance("251FA23109")
        recs = generate_deterministic_recommendations(analysis, student)

        alerts_joined = " ".join(recs["immediate_alerts"])
        self.assertIn("16 consecutive classes", alerts_joined)
        self.assertGreaterEqual(len(recs["weekly_study_schedule"]), 7)

    def test_09_pdf_report_generation(self):
        """Phase 11: PDF generation generates valid non-empty byte stream."""
        student = get_student_by_reg_no("251FA23109")
        analysis = analyze_student_performance("251FA23109")
        recs = generate_deterministic_recommendations(analysis, student)
        pdf_stream = generate_student_pdf_report(student, analysis, recs)
        self.assertIsNotNone(pdf_stream)
        pdf_bytes = pdf_stream.getvalue()
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertGreater(len(pdf_bytes), 1000)

    def test_10_authentication_and_student_isolation(self):
        """Phase 1: Roles, login, and authorization isolation."""
        # Bootstrap admin login
        admin, _ = authenticate_user("admin", "Admin@123")
        self.assertIsNotNone(admin)
        self.assertEqual(admin["role"], "Admin")

        # Create Faculty user
        f_ok, _ = create_user("faculty1", "faculty@edutrack.ac.in", "Faculty@123", "Faculty", "Prof. Sharma")
        self.assertTrue(f_ok)
        faculty, _ = authenticate_user("faculty1", "Faculty@123")
        self.assertIsNotNone(faculty)
        self.assertEqual(faculty["role"], "Faculty")

        # Create Student user linked to 251FA23109
        s_ok, _ = create_user("kushmitha", "kushmitha@edutrack.ac.in", "Student@123", "Student", "SK Kushmitha Bee", "251FA23109")
        self.assertTrue(s_ok)
        student_user, _ = authenticate_user("251FA23109", "Student@123")
        self.assertIsNotNone(student_user)
        self.assertEqual(student_user["role"], "Student")
        self.assertEqual(student_user["student_reg_no"], "251FA23109")


if __name__ == "__main__":
    unittest.main()
