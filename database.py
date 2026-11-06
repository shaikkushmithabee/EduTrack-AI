import os
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "edutrack.db")


def get_connection():
    """Get a SQLite database connection with row factory configured."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_database():
    """Initialize database tables and default academic configuration if not exists."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('Admin', 'Faculty', 'Student')),
        student_reg_no TEXT,
        full_name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Students Table (NO DEMO DATA)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reg_no TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        department TEXT NOT NULL,
        course TEXT NOT NULL,
        academic_year TEXT NOT NULL,
        current_year TEXT NOT NULL,
        semester TEXT NOT NULL,
        section TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 3. Subjects Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        semester TEXT NOT NULL,
        max_internal REAL DEFAULT 40.0,
        max_external REAL DEFAULT 60.0,
        total_max REAL DEFAULT 100.0,
        pass_mark REAL DEFAULT 40.0,
        internal_weightage REAL DEFAULT 40.0,
        external_weightage REAL DEFAULT 60.0,
        total_planned_classes INTEGER DEFAULT 60,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 4. Attendance Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_reg_no TEXT NOT NULL,
        subject_code TEXT NOT NULL,
        total_conducted INTEGER NOT NULL CHECK(total_conducted >= 0),
        classes_attended INTEGER NOT NULL CHECK(classes_attended >= 0),
        period_or_date TEXT,
        notes TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(student_reg_no, subject_code),
        FOREIGN KEY(student_reg_no) REFERENCES students(reg_no) ON DELETE CASCADE,
        FOREIGN KEY(subject_code) REFERENCES subjects(code) ON DELETE CASCADE
    );
    """)

    # 5. Attendance History Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_reg_no TEXT NOT NULL,
        subject_code TEXT NOT NULL,
        total_conducted INTEGER NOT NULL,
        classes_attended INTEGER NOT NULL,
        changed_by TEXT,
        reason TEXT,
        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 6. Marks Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS marks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_reg_no TEXT NOT NULL,
        subject_code TEXT NOT NULL,
        quiz REAL,
        quiz_max REAL DEFAULT 10.0,
        assignment REAL,
        assignment_max REAL DEFAULT 10.0,
        fa1 REAL,
        fa1_max REAL DEFAULT 20.0,
        fa2 REAL,
        fa2_max REAL DEFAULT 20.0,
        midterm1 REAL,
        midterm1_max REAL DEFAULT 30.0,
        midterm2 REAL,
        midterm2_max REAL DEFAULT 30.0,
        internal_exam REAL,
        internal_max REAL DEFAULT 40.0,
        semester_exam REAL,
        semester_max REAL DEFAULT 60.0,
        total_obtained REAL,
        total_max REAL DEFAULT 100.0,
        pass_mark REAL DEFAULT 40.0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(student_reg_no, subject_code),
        FOREIGN KEY(student_reg_no) REFERENCES students(reg_no) ON DELETE CASCADE,
        FOREIGN KEY(subject_code) REFERENCES subjects(code) ON DELETE CASCADE
    );
    """)

    # 7. Marks History Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS marks_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_reg_no TEXT NOT NULL,
        subject_code TEXT NOT NULL,
        assessment_name TEXT NOT NULL,
        previous_mark REAL,
        new_mark REAL,
        changed_by TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 8. Academic Configuration Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS academic_config (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        config_key TEXT UNIQUE NOT NULL,
        config_value TEXT NOT NULL,
        description TEXT
    );
    """)

    # 9. AI Analysis Cache Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ai_analysis_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_reg_no TEXT UNIQUE NOT NULL,
        analysis_json TEXT NOT NULL,
        recommendations_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(student_reg_no) REFERENCES students(reg_no) ON DELETE CASCADE
    );
    """)

    # Seed initial institutional default configuration if empty
    default_configs = [
        ("attendance_threshold", "75.0", "Minimum required attendance percentage"),
        ("pass_percentage", "40.0", "Minimum overall pass percentage"),
        ("internal_weightage", "40.0", "Standard internal assessment weightage %"),
        ("external_weightage", "60.0", "Standard semester end examination weightage %"),
        ("min_external_pass", "35.0", "Minimum percentage required specifically in semester exam"),
    ]

    for key, val, desc in default_configs:
        cursor.execute("""
            INSERT OR IGNORE INTO academic_config (config_key, config_value, description)
            VALUES (?, ?, ?)
        """, (key, val, desc))

    conn.commit()
    conn.close()


# Configuration Helpers
def get_config(key, default=None):
    conn = get_connection()
    row = conn.execute("SELECT config_value FROM academic_config WHERE config_key = ?", (key,)).fetchone()
    conn.close()
    if row:
        return row["config_value"]
    return default


def set_config(key, value, description=None):
    conn = get_connection()
    if description:
        conn.execute("""
            INSERT INTO academic_config (config_key, config_value, description)
            VALUES (?, ?, ?)
            ON CONFLICT(config_key) DO UPDATE SET config_value = excluded.config_value, description = excluded.description
        """, (key, str(value), description))
    else:
        conn.execute("""
            INSERT INTO academic_config (config_key, config_value)
            VALUES (?, ?)
            ON CONFLICT(config_key) DO UPDATE SET config_value = excluded.config_value
        """, (key, str(value)))
    conn.commit()
    conn.close()


def get_all_configs():
    conn = get_connection()
    rows = conn.execute("SELECT config_key, config_value, description FROM academic_config").fetchall()
    conn.close()
    return {row["config_key"]: row["config_value"] for row in rows}


# Student Operations
def add_student(reg_no, full_name, email, department, course, academic_year, current_year, semester, section):
    """Add a new student record. Returns (success: bool, message: str)"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        reg_no = reg_no.strip().upper()
        email = email.strip().lower()
        full_name = full_name.strip()
        cursor.execute("""
            INSERT INTO students (reg_no, full_name, email, department, course, academic_year, current_year, semester, section)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (reg_no, full_name, email, department, course, academic_year, current_year, semester, section))
        conn.commit()
        return True, f"Student {full_name} ({reg_no}) registered successfully."
    except sqlite3.IntegrityError as e:
        if "reg_no" in str(e).lower():
            return False, f"A student with Registration Number '{reg_no}' already exists."
        elif "email" in str(e).lower():
            return False, f"A student with Email '{email}' already exists."
        return False, f"Database Integrity Error: {e}"
    except Exception as e:
        return False, f"Error: {e}"
    finally:
        conn.close()


def update_student(reg_no, full_name, email, department, course, academic_year, current_year, semester, section):
    """Update existing student details."""
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE students
            SET full_name = ?, email = ?, department = ?, course = ?,
                academic_year = ?, current_year = ?, semester = ?, section = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE reg_no = ?
        """, (full_name.strip(), email.strip().lower(), department, course,
              academic_year, current_year, semester, section, reg_no.strip().upper()))
        conn.commit()
        return True, "Student updated successfully."
    except sqlite3.IntegrityError as e:
        return False, f"Update failed: {e}"
    finally:
        conn.close()


def delete_student(reg_no):
    """Delete a student and associated records."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM students WHERE reg_no = ?", (reg_no.strip().upper(),))
        conn.commit()
        return True, f"Student {reg_no} and related records removed."
    except Exception as e:
        return False, f"Error deleting student: {e}"
    finally:
        conn.close()


def get_student_by_reg_no(reg_no):
    """Search student strictly by Registration Number."""
    if not reg_no:
        return None
    conn = get_connection()
    student = conn.execute("SELECT * FROM students WHERE reg_no = ?", (reg_no.strip().upper(),)).fetchone()
    conn.close()
    return dict(student) if student else None


def get_student_by_email(email):
    """Search student strictly by registered Email."""
    if not email:
        return None
    conn = get_connection()
    student = conn.execute("SELECT * FROM students WHERE LOWER(email) = ?", (email.strip().lower(),)).fetchone()
    conn.close()
    return dict(student) if student else None


def search_student(query):
    """Search student by Reg No or Email ID strictly."""
    if not query:
        return None
    query = query.strip()
    # Check Reg No
    s = get_student_by_reg_no(query)
    if s:
        return s
    # Check Email
    return get_student_by_email(query)


def get_all_students(department=None, semester=None):
    """Get all student records without dummy data."""
    conn = get_connection()
    query = "SELECT * FROM students WHERE 1=1"
    params = []
    if department:
        query += " AND department = ?"
        params.append(department)
    if semester:
        query += " AND semester = ?"
        params.append(semester)
    query += " ORDER BY reg_no ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# Subject Operations
def add_subject(code, name, department, semester, max_internal=40.0, max_external=60.0,
                total_max=100.0, pass_mark=40.0, internal_weightage=40.0, external_weightage=60.0, total_planned_classes=60):
    conn = get_connection()
    try:
        code = code.strip().upper()
        conn.execute("""
            INSERT INTO subjects (code, name, department, semester, max_internal, max_external,
                                  total_max, pass_mark, internal_weightage, external_weightage, total_planned_classes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (code, name.strip(), department, semester, max_internal, max_external,
              total_max, pass_mark, internal_weightage, external_weightage, total_planned_classes))
        conn.commit()
        return True, f"Subject {name} ({code}) added."
    except sqlite3.IntegrityError:
        return False, f"Subject with code '{code}' already exists."
    except Exception as e:
        return False, f"Error: {e}"
    finally:
        conn.close()


def update_subject(code, name, department, semester, max_internal, max_external,
                   total_max, pass_mark, internal_weightage, external_weightage, total_planned_classes):
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE subjects
            SET name = ?, department = ?, semester = ?, max_internal = ?, max_external = ?,
                total_max = ?, pass_mark = ?, internal_weightage = ?, external_weightage = ?, total_planned_classes = ?
            WHERE code = ?
        """, (name.strip(), department, semester, max_internal, max_external,
              total_max, pass_mark, internal_weightage, external_weightage, total_planned_classes, code.strip().upper()))
        conn.commit()
        return True, "Subject updated successfully."
    except Exception as e:
        return False, f"Error: {e}"
    finally:
        conn.close()


def delete_subject(code):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM subjects WHERE code = ?", (code.strip().upper(),))
        conn.commit()
        return True, f"Subject {code} deleted."
    except Exception as e:
        return False, f"Error: {e}"
    finally:
        conn.close()


def get_all_subjects(department=None, semester=None):
    conn = get_connection()
    query = "SELECT * FROM subjects WHERE 1=1"
    params = []
    if department:
        query += " AND department = ?"
        params.append(department)
    if semester:
        query += " AND semester = ?"
        params.append(semester)
    query += " ORDER BY code ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_subject_by_code(code):
    if not code:
        return None
    conn = get_connection()
    row = conn.execute("SELECT * FROM subjects WHERE code = ?", (code.strip().upper(),)).fetchone()
    conn.close()
    return dict(row) if row else None


# Attendance Operations
def save_attendance(student_reg_no, subject_code, total_conducted, classes_attended,
                    period_or_date=None, notes=None, recorded_by="Faculty", change_reason="Regular Entry"):
    """Save or update attendance for a student in a subject, logging change history."""
    if classes_attended > total_conducted:
        return False, "Attended classes cannot exceed total classes conducted."
    if total_conducted < 0 or classes_attended < 0:
        return False, "Class counts cannot be negative."

    student_reg_no = student_reg_no.strip().upper()
    subject_code = subject_code.strip().upper()

    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check existing
        existing = cursor.execute("""
            SELECT total_conducted, classes_attended FROM attendance
            WHERE student_reg_no = ? AND subject_code = ?
        """, (student_reg_no, subject_code)).fetchone()

        cursor.execute("""
            INSERT INTO attendance (student_reg_no, subject_code, total_conducted, classes_attended, period_or_date, notes, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(student_reg_no, subject_code) DO UPDATE SET
                total_conducted = excluded.total_conducted,
                classes_attended = excluded.classes_attended,
                period_or_date = excluded.period_or_date,
                notes = excluded.notes,
                updated_at = CURRENT_TIMESTAMP
        """, (student_reg_no, subject_code, total_conducted, classes_attended, period_or_date, notes))

        # Record in history
        cursor.execute("""
            INSERT INTO attendance_history (student_reg_no, subject_code, total_conducted, classes_attended, changed_by, reason)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (student_reg_no, subject_code, total_conducted, classes_attended, recorded_by,
              change_reason if not existing else f"Updated from {existing['classes_attended']}/{existing['total_conducted']}"))

        conn.commit()
        return True, "Attendance saved successfully."
    except Exception as e:
        return False, f"Failed to save attendance: {e}"
    finally:
        conn.close()


def get_student_attendance(student_reg_no):
    """Retrieve all attendance records for a student along with subject metadata."""
    conn = get_connection()
    cursor = conn.cursor()
    rows = cursor.execute("""
        SELECT a.*, s.name as subject_name, s.department, s.semester, s.total_planned_classes
        FROM attendance a
        JOIN subjects s ON a.subject_code = s.code
        WHERE a.student_reg_no = ?
        ORDER BY s.name ASC
    """, (student_reg_no.strip().upper(),)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_attendance_history(student_reg_no, subject_code=None):
    conn = get_connection()
    query = """
        SELECT h.*, s.name as subject_name
        FROM attendance_history h
        JOIN subjects s ON h.subject_code = s.code
        WHERE h.student_reg_no = ?
    """
    params = [student_reg_no.strip().upper()]
    if subject_code:
        query += " AND h.subject_code = ?"
        params.append(subject_code.strip().upper())
    query += " ORDER BY h.recorded_at DESC LIMIT 50"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# Marks Operations
def save_marks(student_reg_no, subject_code, quiz=None, assignment=None, fa1=None, fa2=None,
               midterm1=None, midterm2=None, internal_exam=None, semester_exam=None,
               recorded_by="Faculty"):
    """Save or update marks for a student in a subject, validating and logging history."""
    student_reg_no = student_reg_no.strip().upper()
    subject_code = subject_code.strip().upper()

    subj = get_subject_by_code(subject_code)
    if not subj:
        return False, f"Subject {subject_code} not found."

    # Validate non-negative marks
    for label, val in [("Quiz", quiz), ("Assignment", assignment), ("FA1", fa1), ("FA2", fa2),
                      ("Midterm 1", midterm1), ("Midterm 2", midterm2),
                      ("Internal Exam", internal_exam), ("Semester Exam", semester_exam)]:
        if val is not None and val < 0:
            return False, f"{label} marks cannot be negative."

    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Calculate total obtained based on entered fields or internal + semester
        # If internal_exam is not directly given, can compute from quiz + assignment + fa1 + fa2 + midterms
        # Or if internal_exam is provided, use internal_exam + semester_exam
        internal_sum = 0.0
        internal_count = 0
        if internal_exam is not None:
            calc_internal = internal_exam
        else:
            components = [c for c in [quiz, assignment, fa1, fa2, midterm1, midterm2] if c is not None]
            calc_internal = sum(components) if components else None

        total_obtained = None
        if calc_internal is not None or semester_exam is not None:
            total_obtained = (calc_internal or 0.0) + (semester_exam or 0.0)

        cursor.execute("""
            INSERT INTO marks (student_reg_no, subject_code, quiz, assignment, fa1, fa2,
                              midterm1, midterm2, internal_exam, semester_exam, total_obtained,
                              total_max, pass_mark, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(student_reg_no, subject_code) DO UPDATE SET
                quiz = excluded.quiz,
                assignment = excluded.assignment,
                fa1 = excluded.fa1,
                fa2 = excluded.fa2,
                midterm1 = excluded.midterm1,
                midterm2 = excluded.midterm2,
                internal_exam = excluded.internal_exam,
                semester_exam = excluded.semester_exam,
                total_obtained = excluded.total_obtained,
                total_max = excluded.total_max,
                pass_mark = excluded.pass_mark,
                updated_at = CURRENT_TIMESTAMP
        """, (student_reg_no, subject_code, quiz, assignment, fa1, fa2,
              midterm1, midterm2, internal_exam, semester_exam, total_obtained,
              subj["total_max"], subj["pass_mark"]))

        cursor.execute("""
            INSERT INTO marks_history (student_reg_no, subject_code, assessment_name, new_mark, changed_by)
            VALUES (?, ?, ?, ?, ?)
        """, (student_reg_no, subject_code, "Assessment Update", total_obtained, recorded_by))

        conn.commit()
        return True, "Marks recorded successfully."
    except Exception as e:
        return False, f"Failed to save marks: {e}"
    finally:
        conn.close()


def get_student_marks(student_reg_no):
    """Retrieve all marks records for a student along with subject metadata."""
    conn = get_connection()
    cursor = conn.cursor()
    rows = cursor.execute("""
        SELECT m.*, s.name as subject_name, s.department, s.semester,
               s.max_internal, s.max_external, s.internal_weightage, s.external_weightage
        FROM marks m
        JOIN subjects s ON m.subject_code = s.code
        WHERE m.student_reg_no = ?
        ORDER BY s.name ASC
    """, (student_reg_no.strip().upper(),)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_marks_history(student_reg_no, subject_code=None):
    conn = get_connection()
    query = """
        SELECT h.*, s.name as subject_name
        FROM marks_history h
        JOIN subjects s ON h.subject_code = s.code
        WHERE h.student_reg_no = ?
    """
    params = [student_reg_no.strip().upper()]
    if subject_code:
        query += " AND h.subject_code = ?"
        params.append(subject_code.strip().upper())
    query += " ORDER BY h.timestamp DESC LIMIT 50"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]
