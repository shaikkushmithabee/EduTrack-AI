import io
import re
import pandas as pd
from database import (
    get_connection,
    get_student_by_reg_no,
    get_student_by_email,
    get_subject_by_code,
    add_student,
    update_student,
    add_subject,
    save_attendance,
    save_marks
)


def validate_email_format(email: str) -> bool:
    """Validate RFC 5322 standard email address format."""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, str(email).strip()))


def generate_sample_csv(template_type: str) -> str:
    """Generate blank template CSV with header structure."""
    if template_type == "students":
        return "reg_no,full_name,email,department,course,academic_year,current_year,semester,section\n"
    elif template_type == "subjects":
        return "code,name,department,semester,max_internal,max_external,total_max,pass_mark,internal_weightage,external_weightage,total_planned_classes\n"
    elif template_type == "attendance":
        return "student_reg_no,subject_code,total_conducted,classes_attended,period_or_date,notes\n"
    elif template_type == "marks":
        return "student_reg_no,subject_code,quiz,assignment,fa1,fa2,midterm1,midterm2,internal_exam,semester_exam\n"
    return ""


def validate_and_preview_import(file_obj, import_type: str):
    """
    Parse uploaded CSV or Excel file, validate constraints, and return preview with issues.
    """
    try:
        if file_obj.name.endswith(".csv"):
            df = pd.read_csv(file_obj)
        elif file_obj.name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file_obj)
        else:
            return False, "Unsupported file format. Please upload CSV or Excel (.xlsx).", None, []
    except Exception as e:
        return False, f"Failed to parse file: {e}", None, []

    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    issues = []
    validated_rows = []

    if import_type == "students":
        required_cols = {"reg_no", "full_name", "email", "department", "course", "academic_year", "current_year", "semester", "section"}
        missing_cols = required_cols - set(df.columns)
        if missing_cols:
            return False, f"Missing required column headers: {', '.join(missing_cols)}", df, []

        seen_in_file = set()
        for idx, row in df.iterrows():
            row_idx = idx + 2
            row_issues = []

            reg = str(row.get("reg_no", "")).strip().upper()
            email = str(row.get("email", "")).strip().lower()
            name = str(row.get("full_name", "")).strip()

            if not reg or reg == "NAN":
                row_issues.append("Missing Registration Number.")
            elif reg in seen_in_file:
                row_issues.append(f"Duplicate Registration Number '{reg}' within uploaded file.")
            else:
                seen_in_file.add(reg)

            if not email or email == "nan":
                row_issues.append("Missing Email Address.")
            elif not validate_email_format(email):
                row_issues.append(f"Invalid email format: '{email}'.")

            if not name or name == "nan":
                row_issues.append("Missing Student Name.")

            # Check DB collision
            existing_s = get_student_by_reg_no(reg) if reg else None
            existing_email = get_student_by_email(email) if email else None
            status = "New"
            if existing_s:
                status = f"Update (Existing: {existing_s['full_name']})"
            elif existing_email:
                row_issues.append(f"Email '{email}' belongs to another registered student ({existing_email['reg_no']}).")

            if row_issues:
                issues.append({"row": row_idx, "reg_no": reg, "status": "Invalid", "errors": "; ".join(row_issues)})
            else:
                issues.append({"row": row_idx, "reg_no": reg, "status": status, "errors": "None"})

    elif import_type == "attendance":
        required_cols = {"student_reg_no", "subject_code", "total_conducted", "classes_attended"}
        missing_cols = required_cols - set(df.columns)
        if missing_cols:
            return False, f"Missing required column headers: {', '.join(missing_cols)}", df, []

        for idx, row in df.iterrows():
            row_idx = idx + 2
            row_issues = []

            reg = str(row.get("student_reg_no", "")).strip().upper()
            code = str(row.get("subject_code", "")).strip().upper()

            # Check if student and subject exist
            if not get_student_by_reg_no(reg):
                row_issues.append(f"Student '{reg}' does not exist in database.")
            if not get_subject_by_code(code):
                row_issues.append(f"Subject '{code}' does not exist in database.")

            try:
                tot = int(row.get("total_conducted", 0))
                att = int(row.get("classes_attended", 0))
                if tot < 0 or att < 0:
                    row_issues.append("Class count cannot be negative.")
                if att > tot:
                    row_issues.append(f"Attended classes ({att}) exceeds total conducted ({tot}).")
            except (ValueError, TypeError):
                row_issues.append("Total and Attended classes must be whole numbers.")

            if row_issues:
                issues.append({"row": row_idx, "student": reg, "subject": code, "status": "Invalid", "errors": "; ".join(row_issues)})
            else:
                issues.append({"row": row_idx, "student": reg, "subject": code, "status": "Valid", "errors": "None"})

    elif import_type == "marks":
        required_cols = {"student_reg_no", "subject_code"}
        missing_cols = required_cols - set(df.columns)
        if missing_cols:
            return False, f"Missing required column headers: {', '.join(missing_cols)}", df, []

        for idx, row in df.iterrows():
            row_idx = idx + 2
            row_issues = []

            reg = str(row.get("student_reg_no", "")).strip().upper()
            code = str(row.get("subject_code", "")).strip().upper()

            subj = get_subject_by_code(code)
            if not get_student_by_reg_no(reg):
                row_issues.append(f"Student '{reg}' not found.")
            if not subj:
                row_issues.append(f"Subject '{code}' not found.")

            # Validate marks values
            for m_col in ["quiz", "assignment", "fa1", "fa2", "midterm1", "midterm2", "internal_exam", "semester_exam"]:
                if m_col in df.columns:
                    val = row.get(m_col)
                    if pd.notna(val) and val != "":
                        try:
                            f_val = float(val)
                            if f_val < 0:
                                row_issues.append(f"{m_col} cannot be negative.")
                        except ValueError:
                            row_issues.append(f"{m_col} must be numeric.")

            if row_issues:
                issues.append({"row": row_idx, "student": reg, "subject": code, "status": "Invalid", "errors": "; ".join(row_issues)})
            else:
                issues.append({"row": row_idx, "student": reg, "subject": code, "status": "Valid", "errors": "None"})

    return True, "Validation complete.", df, issues


def execute_import(df: pd.DataFrame, import_type: str, update_existing: bool = True, recorded_by: str = "Admin"):
    """
    Commit validated records into the persistent SQLite database.
    """
    success_count = 0
    skipped_count = 0
    errors = []

    if import_type == "students":
        for _, row in df.iterrows():
            reg = str(row.get("reg_no", "")).strip().upper()
            name = str(row.get("full_name", "")).strip()
            email = str(row.get("email", "")).strip().lower()
            dept = str(row.get("department", "")).strip()
            course = str(row.get("course", "")).strip()
            ay = str(row.get("academic_year", "")).strip()
            cy = str(row.get("current_year", "")).strip()
            sem = str(row.get("semester", "")).strip()
            sec = str(row.get("section", "")).strip()

            if not reg or not name or not email:
                skipped_count += 1
                continue

            existing = get_student_by_reg_no(reg)
            if existing:
                if update_existing:
                    ok, msg = update_student(reg, name, email, dept, course, ay, cy, sem, sec)
                    if ok:
                        success_count += 1
                    else:
                        errors.append(f"Update failed for {reg}: {msg}")
                else:
                    skipped_count += 1
            else:
                ok, msg = add_student(reg, name, email, dept, course, ay, cy, sem, sec)
                if ok:
                    success_count += 1
                else:
                    errors.append(f"Insert failed for {reg}: {msg}")

    elif import_type == "attendance":
        for _, row in df.iterrows():
            reg = str(row.get("student_reg_no", "")).strip().upper()
            code = str(row.get("subject_code", "")).strip().upper()
            try:
                tot = int(row.get("total_conducted", 0))
                att = int(row.get("classes_attended", 0))
                period = str(row.get("period_or_date", "")) if pd.notna(row.get("period_or_date")) else "Batch Upload"
                notes = str(row.get("notes", "")) if pd.notna(row.get("notes")) else ""

                ok, msg = save_attendance(reg, code, tot, att, period, notes, recorded_by, "Bulk CSV Import")
                if ok:
                    success_count += 1
                else:
                    errors.append(f"{reg} - {code}: {msg}")
            except Exception as e:
                errors.append(f"Error on {reg}: {e}")

    elif import_type == "marks":
        for _, row in df.iterrows():
            reg = str(row.get("student_reg_no", "")).strip().upper()
            code = str(row.get("subject_code", "")).strip().upper()

            def clean_m(val):
                if pd.notna(val) and str(val).strip() != "":
                    try:
                        return float(val)
                    except ValueError:
                        return None
                return None

            quiz = clean_m(row.get("quiz"))
            assn = clean_m(row.get("assignment"))
            fa1 = clean_m(row.get("fa1"))
            fa2 = clean_m(row.get("fa2"))
            m1 = clean_m(row.get("midterm1"))
            m2 = clean_m(row.get("midterm2"))
            ie = clean_m(row.get("internal_exam"))
            se = clean_m(row.get("semester_exam"))

            ok, msg = save_marks(reg, code, quiz, assn, fa1, fa2, m1, m2, ie, se, recorded_by)
            if ok:
                success_count += 1
            else:
                errors.append(f"{reg} - {code}: {msg}")

    return {
        "success": len(errors) == 0,
        "success_count": success_count,
        "skipped_count": skipped_count,
        "errors": errors
    }
