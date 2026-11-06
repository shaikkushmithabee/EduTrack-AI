# EduTrack AI — Complete AI-Powered Academic Analysis & Early Warning System

EduTrack AI is an institutional-grade academic monitoring and early warning system that turns raw attendance and assessment records into timely, predictive, and actionable student interventions.

---

## 🌟 Key Features

### 1. Multi-Tier Role-Based Access Control
- **Admin**:
  - Full student profile registration and management
  - Faculty account provisioning and role assignments
  - Curriculum and subject configuration
  - Institutional policies (attendance thresholds, pass mark rules)
  - Bulk CSV/Excel data import and academic reporting
- **Faculty**:
  - Student record search (strictly by Registration Number or Email ID)
  - Subject-wise attendance recording with audit logs
  - Multi-component marks entry (Quiz, Assignment, FA1, FA2, Midterms, Final Exam)
  - Real-time early warning diagnostics
  - Student report generation
- **Student**:
  - Secure personal login
  - Strict data isolation (can only access their own profile and records)
  - Live attendance health tracker with consecutive class recovery alerts
  - Required Future Marks Calculator for pass and target grades (60%, 70%, 80%)
  - Personalized AI recommendations and weekly study schedules
  - One-click official PDF Academic Report download

### 2. Strict Data Integrity — Zero Demo Data
- **No fake student names, dummy registration numbers, or randomized performance.**
- Clean empty states display guidance when the database has no records.
- Searches strictly query the database; if a student does not exist, an explicit **"Student Record Not Found"** notification is shown.

### 3. Attendance Intelligence & Recovery Mathematics
- Automatically calculates:
  $$\text{Attendance Percentage} = \left(\frac{\text{Classes Attended}}{\text{Total Classes Conducted}}\right) \times 100$$
- **Consecutive Recovery Classes Formula**:
  $$\frac{A + X}{T + X} \ge R \implies X = \left\lceil \frac{R \cdot T - A}{1 - R} \right\rceil$$
  - *Example*: For $T = 40$, $A = 26$, Current Attendance = $65.0\%$, Target $R = 75.0\%$:
    $$X = \left\lceil \frac{0.75 \times 40 - 26}{1 - 0.75} \right\rceil = \frac{30 - 26}{0.25} = 16 \text{ consecutive classes}$$
- Validates that attended classes cannot exceed conducted classes ($A \le T$).
- Computes buffer classes when attendance is above requirement.
- Verifies mathematical achievability with remaining semester classes.

### 4. Required Future Marks Calculator
- Calculates exact marks needed on remaining assessments to:
  - Pass the course (default 40%)
  - Achieve First Class (60%)
  - Achieve Distinction (70%)
  - Achieve High Distinction (80%)
  - Achieve any custom target percentage
- Mathematical formulation:
  $$\text{Required Future Marks} = \max(0, \text{Target Overall Marks} - \text{Existing Weighted Marks})$$
- Detects and explains **mathematically impossible** targets when required marks exceed remaining assessment maximums.

### 5. Multi-Factor Academic Risk Classification
- **High Risk**:
  - Any subject attendance $< 65\%$
  - Attendance or pass criteria mathematically unachievable
  - Currently failing with $< 40\%$
  - High effort needed ($> 75\%$ on remaining assessments)
- **Medium Risk**:
  - Attendance between $65\%$ and $74.9\%$
  - Marks between $45\%$ and $59.9\%$
  - Moderate effort needed on remaining assessments
- **Low Risk**:
  - Attendance $\ge 75\%$ across all subjects
  - Good academic standing ($\ge 60\%$) with steady progress

### 6. AI Recommendations & Weekly Study Schedules
- Integrated with Groq LLM (`llama-3.3-70b-versatile`) with automatic fallback to a deterministic expert rule engine.
- Generates priority alerts, subject-wise suggestions, and day-by-day weekly study allocations prioritized by weak subjects.

### 7. Official PDF Academic Report
- Built with ReportLab to generate publication-grade PDF reports containing institutional headers, student profile, attendance recovery tables, marks breakdown, risk diagnostics, and weekly study plans.

### 8. Excel / CSV Bulk Data Import
- Pre-import data validation, format verification, and duplicate registration detection.
- Preview tables with error flags before committing to the database.

---

## 🚀 Running the Application

### Option A: Using the Launcher (Windows)
Double-click `run_app.bat` or run:
```powershell
.\run_app.bat
```

### Option B: Terminal Command
```powershell
& "C:\Users\shaik\anaconda3\python.exe" -m streamlit run app.py
```

### Running Test Suites
```powershell
# Unit Test Suite
& "C:\Users\shaik\anaconda3\python.exe" test_system.py

# End-to-End System Test Suite
& "C:\Users\shaik\anaconda3\python.exe" test_end_to_end.py
```

---

## 🔑 Default Credentials

- **Admin Account**:
  - Username / Identifier: `admin`
  - Password: `Admin@123`
- *New Faculty and Student accounts can be provisioned through the Admin portal or Student Setup screen.*
