import os
import json
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

load_dotenv()

from database import (
    init_database,
    get_connection,
    get_config,
    set_config,
    get_all_configs,
    add_student,
    update_student,
    delete_student,
    get_student_by_reg_no,
    get_student_by_email,
    search_student,
    get_all_students,
    add_subject,
    update_subject,
    delete_subject,
    get_all_subjects,
    get_subject_by_code,
    save_attendance,
    get_student_attendance,
    get_attendance_history,
    save_marks,
    get_student_marks,
    get_marks_history
)
from auth import (
    ensure_bootstrap_admin,
    create_user,
    authenticate_user,
    get_all_users,
    delete_user
)
from calculator import (
    calculate_attendance_metrics,
    calculate_required_marks,
    calculate_projected_attendance
)
from analysis_engine import analyze_student_performance
from ai_recommender import generate_ai_recommendations, generate_deterministic_recommendations
from pdf_generator import generate_student_pdf_report
from import_export import (
    validate_and_preview_import,
    execute_import,
    generate_sample_csv,
    validate_email_format
)

# Initialize application database and bootstrap admin on startup
init_database()
ensure_bootstrap_admin()

# Configure Streamlit page layout
st.set_page_config(
    page_title="EduTrack AI — Academic Analysis & Early Warning System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for modern corporate-grade academic design
st.markdown("""
<style>
    /* Global styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    
    /* Header Card */
    .edu-header {
        background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 50%, #3B82F6 100%);
        padding: 24px;
        border-radius: 12px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .edu-header h1 {
        color: white !important;
        font-size: 26px;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .edu-header p {
        color: #E0E7FF !important;
        font-size: 14px;
        margin-bottom: 0;
    }
    
    /* Metric Cards */
    .metric-card {
        background: white;
        padding: 16px 20px;
        border-radius: 10px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 12px;
    }
    .metric-card .label {
        font-size: 13px;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-card .value {
        font-size: 26px;
        font-weight: 700;
        color: #1E293B;
        margin-top: 4px;
    }
    .metric-card .caption {
        font-size: 12px;
        color: #94A3B8;
        margin-top: 2px;
    }

    /* Risk Badges */
    .risk-badge-low {
        background-color: #DEF7EC;
        color: #03543F;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 13px;
        display: inline-block;
        border: 1px solid #BCF0DA;
    }
    .risk-badge-medium {
        background-color: #FEF08A;
        color: #854D0E;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 13px;
        display: inline-block;
        border: 1px solid #FDE047;
    }
    .risk-badge-high {
        background-color: #FDE8E8;
        color: #9B1C1C;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 13px;
        display: inline-block;
        border: 1px solid #F8B4B4;
    }
    
    /* Empty State */
    .empty-state-box {
        text-align: center;
        padding: 40px 20px;
        background: #F8FAFC;
        border-radius: 12px;
        border: 2px dashed #CBD5E1;
        margin: 20px 0;
    }
    .empty-state-box h3 {
        color: #334155;
        font-size: 18px;
        margin-bottom: 8px;
    }
    .empty-state-box p {
        color: #64748B;
        font-size: 14px;
        max-width: 500px;
        margin: 0 auto;
    }
</style>
""", unsafe_allow_html=True)


# Session State Management
if "user" not in st.session_state:
    st.session_state.user = None

if "search_query" not in st.session_state:
    st.session_state.search_query = ""

if "selected_student_reg" not in st.session_state:
    st.session_state.selected_student_reg = None


# Authentication Forms
def render_login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 24px;">
            <h1 style="color: #1E3A8A; font-size: 32px; font-weight: 800; margin-bottom: 4px;">🎓 EduTrack AI</h1>
            <p style="color: #4B5563; font-size: 15px;">Complete Academic Analysis & Early Warning Intelligence System</p>
        </div>
        """, unsafe_allow_html=True)

        tab_login, tab_student_reg = st.tabs(["🔐 Sign In", "📝 Student First-Time Setup"])

        with tab_login:
            st.info("💡 **Institutional Access**: Sign in with your registered Username, Email, or Student Registration Number.")
            with st.form("login_form"):
                identifier = st.text_input("Username / Email / Registration Number", placeholder="e.g. admin or 251FA23109")
                password = st.text_input("Password", type="password", placeholder="Enter password")
                submitted = st.form_submit_button("Sign In to Portal", use_container_width=True, type="primary")

                if submitted:
                    user, msg = authenticate_user(identifier, password)
                    if user:
                        st.session_state.user = user
                        st.success(f"Welcome back, {user['full_name']}!")
                        st.rerun()
                    else:
                        st.error(msg)

            st.caption("Default Admin Credentials for initial setup: `admin` / `Admin@123`")

        with tab_student_reg:
            st.markdown("#### Activate Student Account")
            st.caption("If your student record is already in the database, you can initialize your secure login password here.")
            with st.form("student_activate_form"):
                reg_input = st.text_input("Student Registration Number", placeholder="e.g. 251FA23109")
                email_input = st.text_input("Registered Institutional Email", placeholder="e.g. student@edutrack.ac.in")
                new_pwd = st.text_input("Create Secure Password", type="password")
                confirm_pwd = st.text_input("Confirm Password", type="password")
                act_submit = st.form_submit_button("Activate Account", use_container_width=True)

                if act_submit:
                    if new_pwd != confirm_pwd:
                        st.error("Passwords do not match.")
                    elif len(new_pwd) < 6:
                        st.error("Password must be at least 6 characters.")
                    else:
                        student = get_student_by_reg_no(reg_input)
                        if not student or student["email"].lower() != email_input.strip().lower():
                            st.error("Student Record Not Found. Please verify your Registration Number and Email with the Department.")
                        else:
                            ok, msg = create_user(
                                username=student["reg_no"],
                                email=student["email"],
                                password=new_pwd,
                                role="Student",
                                full_name=student["full_name"],
                                student_reg_no=student["reg_no"]
                            )
                            if ok:
                                st.success("Account activated successfully! You may now sign in.")
                            else:
                                st.warning(msg)


# Top Banner Helper
def render_header(title, subtitle):
    st.markdown(f"""
    <div class="edu-header">
        <h1>{title}</h1>
        <p>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)


# Render Risk Badge
def render_risk_badge(risk_level):
    if risk_level == "Low Risk":
        return '<span class="risk-badge-low">🟢 Low Academic Risk</span>'
    elif risk_level == "Medium Risk":
        return '<span class="risk-badge-medium">🟡 Medium Academic Risk</span>'
    elif risk_level == "High Risk":
        return '<span class="risk-badge-high">🔴 High Academic Risk</span>'
    return '<span style="color: #6B7280;">⚪ Unknown Risk</span>'


# ==============================================================================
# VIEW 1: COMPLETE STUDENT ACADEMIC DASHBOARD (Phase 8, 9, 10)
# ==============================================================================
def render_student_dashboard(student_reg_no):
    student = get_student_by_reg_no(student_reg_no)
    if not student:
        st.error(f"Student Record Not Found for Registration Number '{student_reg_no}'.")
        return

    # Run analysis
    analysis = analyze_student_performance(student_reg_no)
    recs = generate_ai_recommendations(analysis, student)

    # A. Student Profile Banner
    st.markdown(f"""
    <div style="background: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 20px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
            <div>
                <h2 style="margin: 0; color: #1E293B; font-size: 22px;">{student['full_name']}</h2>
                <p style="margin: 4px 0 0 0; color: #64748B; font-size: 14px;">
                    <b>Reg No:</b> <code style="font-size: 15px; color: #1E3A8A;">{student['reg_no']}</code> | 
                    <b>Dept:</b> {student['department']} | 
                    <b>Course:</b> {student['course']} | 
                    <b>Semester:</b> {student['semester']} (Sec {student['section']}) | 
                    <b>Academic Year:</b> {student['academic_year']}
                </p>
            </div>
            <div style="margin-top: 10px;">
                {render_risk_badge(analysis.get('risk_level', 'Unknown'))}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not analysis.get("has_data", False):
        st.markdown("""
        <div class="empty-state-box">
            <h3>📭 Insufficient Data for Analysis</h3>
            <p>No attendance or examination marks records have been entered for this student yet. 
            Once faculty enters records, the real-time AI performance analysis and early warning indicators will appear here.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # B. Academic Summary KPIs
    k1, k2, k3, k4, k5 = st.columns(5)
    att_threshold = analysis.get("attendance_threshold", 75.0)
    att_val = analysis.get("overall_attendance_pct", 0.0)
    marks_val = analysis.get("overall_marks_pct", 0.0)

    with k1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">Overall Attendance</div>
            <div class="value" style="color: {'#059669' if att_val >= att_threshold else '#DC2626'}">{att_val}%</div>
            <div class="caption">Target: {att_threshold}%</div>
        </div>
        """, unsafe_allow_html=True)

    with k2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">Overall Marks Avg</div>
            <div class="value" style="color: {'#059669' if marks_val >= 60 else ('#D97706' if marks_val >= 40 else '#DC2626')}">{marks_val}%</div>
            <div class="caption">Total Marks Evaluated</div>
        </div>
        """, unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">Tracked Subjects</div>
            <div class="value">{analysis.get('total_subjects_tracked', 0)}</div>
            <div class="caption">Enrolled Modules</div>
        </div>
        """, unsafe_allow_html=True)

    with k4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">Strongest Subject</div>
            <div class="value" style="font-size: 18px; color: #059669;">{analysis.get('strongest_subject', 'N/A')[:18]}</div>
            <div class="caption">Top academic scoring</div>
        </div>
        """, unsafe_allow_html=True)

    with k5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">Weakest Subject</div>
            <div class="value" style="font-size: 18px; color: #DC2626;">{analysis.get('weakest_subject', 'N/A')[:18]}</div>
            <div class="caption">Priority attention area</div>
        </div>
        """, unsafe_allow_html=True)

    # C. Tabs for Deep-Dive Analysis
    t_overview, t_attendance, t_marks, t_req_marks, t_ai_insights, t_pdf = st.tabs([
        "📋 Academic Summary",
        "📅 Attendance Health",
        "📝 Subject Marks",
        "🎯 Required Marks Calculator",
        "🤖 AI Insights & Study Plan",
        "📄 Official PDF Report"
    ])

    with t_overview:
        c_left, c_right = st.columns([1, 1])
        with c_left:
            st.markdown("#### 📊 Subject Attendance Overview")
            att_map = analysis.get("subject_attendance", {})
            if att_map:
                df_att = pd.DataFrame([
                    {
                        "Subject": v["subject_name"],
                        "Attendance %": v["current_percentage"],
                        "Status": v["status"]
                    } for v in att_map.values()
                ])
                fig_att = px.bar(
                    df_att, x="Subject", y="Attendance %",
                    color="Attendance %",
                    color_continuous_scale=["#EF4444", "#F59E0B", "#10B981"],
                    range_y=[0, 100],
                    text="Attendance %"
                )
                fig_att.add_hline(y=att_threshold, line_dash="dash", line_color="red",
                                 annotation_text=f"Min Required ({att_threshold}%)")
                fig_att.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=320)
                st.plotly_chart(fig_att, use_container_width=True)
            else:
                st.caption("No subject attendance recorded yet.")

        with c_right:
            st.markdown("#### 📈 Subject Marks Performance")
            marks_map = analysis.get("subject_marks", {})
            if marks_map:
                df_marks = pd.DataFrame([
                    {
                        "Subject": v["subject_name"],
                        "Marks %": v["current_percentage"],
                        "Obtained": v["current_obtained"],
                        "Max": v["current_max"]
                    } for v in marks_map.values()
                ])
                fig_marks = px.bar(
                    df_marks, x="Subject", y="Marks %",
                    color="Marks %",
                    color_continuous_scale=["#EF4444", "#F59E0B", "#3B82F6"],
                    range_y=[0, 100],
                    text="Marks %"
                )
                fig_marks.add_hline(y=analysis.get("pass_percentage", 40.0), line_dash="dash", line_color="orange",
                                   annotation_text="Pass Mark (40%)")
                fig_marks.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=320)
                st.plotly_chart(fig_marks, use_container_width=True)
            else:
                st.caption("No subject marks evaluated yet.")

        st.markdown("#### 🛡️ Academic Risk Classification Diagnostic")
        for reason in analysis.get("risk_reasons", []):
            st.warning(f"• {reason}") if analysis.get("risk_level") != "Low Risk" else st.success(f"• {reason}")

    with t_attendance:
        st.markdown(f"### 📅 Subject-Wise Attendance Tracker & Recovery Paths")
        st.caption(f"Institutional Standard Requirement: **{att_threshold}%**. Calculated strictly from registered class sessions.")

        att_records = analysis.get("subject_attendance", {})
        if att_records:
            att_display = []
            for code, m in att_records.items():
                att_display.append({
                    "Subject Code": code,
                    "Subject Name": m["subject_name"],
                    "Total Conducted": m["total_conducted"],
                    "Attended": m["attended"],
                    "Missed": m["missed"],
                    "Current Attendance": f"{m['current_percentage']}%",
                    "Shortage": f"{m['shortage']}%",
                    "Consecutive Classes Needed to 75%": f"{m['consecutive_required']} classes" if m['consecutive_required'] > 0 else "None (Met)",
                    "Status": m["status"]
                })
            st.dataframe(pd.DataFrame(att_display), use_container_width=True, hide_index=True)

            st.markdown("#### 💡 Attendance Recovery Explanations")
            for code, m in att_records.items():
                if m["status"] != "On Track":
                    st.error(f"**{m['subject_name']} ({code}):** {m['explanation']}")
                else:
                    st.success(f"**{m['subject_name']} ({code}):** {m['explanation']}")

            # Interactive attendance projection tool
            st.markdown("---")
            st.markdown("#### 🔮 What-If Attendance Simulator")
            proj_col1, proj_col2, proj_col3 = st.columns(3)
            with proj_col1:
                sel_subj_code = st.selectbox("Select Subject", list(att_records.keys()), format_func=lambda c: f"{att_records[c]['subject_name']} ({c})")
            with proj_col2:
                upcoming_total = st.number_input("Upcoming Classes Conducted", min_value=1, max_value=40, value=10, step=1)
            with proj_col3:
                upcoming_attend = st.number_input("Classes You Will Attend", min_value=0, max_value=upcoming_total, value=upcoming_total, step=1)

            cur_m = att_records[sel_subj_code]
            proj_pct = calculate_projected_attendance(cur_m["attended"], cur_m["total_conducted"], upcoming_attend, upcoming_total)
            st.info(f"If you attend **{upcoming_attend} out of {upcoming_total}** upcoming classes in **{cur_m['subject_name']}**, your attendance will shift from **{cur_m['current_percentage']}%** to **{proj_pct}%**.")
        else:
            st.info("No attendance records found.")

    with t_marks:
        st.markdown("### 📝 Subject Examination Marks & Assessment Breakdown")
        raw_marks = get_student_marks(student_reg_no)
        if raw_marks:
            marks_table = []
            for r in raw_marks:
                marks_table.append({
                    "Subject": f"{r['subject_name']} ({r['subject_code']})",
                    "Quiz": r["quiz"] if r["quiz"] is not None else "-",
                    "Assignment": r["assignment"] if r["assignment"] is not None else "-",
                    "FA1": r["fa1"] if r["fa1"] is not None else "-",
                    "FA2": r["fa2"] if r["fa2"] is not None else "-",
                    "Midterm 1": r["midterm1"] if r["midterm1"] is not None else "-",
                    "Midterm 2": r["midterm2"] if r["midterm2"] is not None else "-",
                    "Semester Exam": r["semester_exam"] if r["semester_exam"] is not None else "-",
                    "Total Obtained": r["total_obtained"] if r["total_obtained"] is not None else "-",
                    "Total Max": r["total_max"],
                    "Pass Mark": r["pass_mark"]
                })
            st.dataframe(pd.DataFrame(marks_table), use_container_width=True, hide_index=True)
        else:
            st.info("No marks evaluated yet.")

    with t_req_marks:
        st.markdown("### 🎯 Required Future Marks Calculator")
        st.markdown("Calculate how many marks you need on remaining assessments to pass or hit desired target percentages.")

        subj_marks_dict = analysis.get("subject_marks", {})
        if subj_marks_dict:
            sel_calc_subj = st.selectbox("Select Course for Analysis", list(subj_marks_dict.keys()),
                                          format_func=lambda c: f"{subj_marks_dict[c]['subject_name']} ({c})")
            cur_subj_data = subj_marks_dict[sel_calc_subj]

            st.write(f"**Current Status:** Scored **{cur_subj_data['current_obtained']}** out of **{cur_subj_data['current_max']}** evaluated marks ({cur_subj_data['current_percentage']}%). Total subject maximum: **{cur_subj_data['total_subject_max']}**.")

            target_mode = st.radio("Choose Target Grade / Percentage", ["Pass (40%)", "First Class (60%)", "Distinction (70%)", "High Distinction (80%)", "Custom Target %"], horizontal=True)

            if target_mode == "Pass (40%)":
                calc_res = cur_subj_data["targets"]["pass"]
            elif target_mode == "First Class (60%)":
                calc_res = cur_subj_data["targets"]["60"]
            elif target_mode == "Distinction (70%)":
                calc_res = cur_subj_data["targets"]["70"]
            elif target_mode == "High Distinction (80%)":
                calc_res = cur_subj_data["targets"]["80"]
            else:
                cust_pct = st.slider("Select Custom Target Percentage", min_value=1.0, max_value=100.0, value=75.0, step=0.5)
                calc_res = calculate_required_marks(
                    current_obtained=cur_subj_data["current_obtained"],
                    current_max=cur_subj_data["current_max"],
                    total_max=cur_subj_data["total_subject_max"],
                    pass_mark=cur_subj_data["pass_mark"],
                    target_percentage=cust_pct
                )

            rc1, rc2, rc3, rc4 = st.columns(4)
            with rc1:
                st.metric("Target Required Total", f"{calc_res['target_marks_needed']} marks")
            with rc2:
                st.metric("Marks Needed in Future", f"{calc_res['required_future_marks']} marks",
                          delta=f"{calc_res['required_pct_on_remaining']}% on remaining" if calc_res['achievable'] else "Unachievable")
            with rc3:
                st.metric("Remaining Exam Max", f"{calc_res['remaining_max']} marks")
            with rc4:
                st.metric("Max Possible Score", f"{calc_res['max_possible_total']} ({calc_res['max_possible_percentage']}%)")

            if calc_res["achievable"]:
                st.success(f"✅ **Achievable:** {calc_res['explanation']}")
            else:
                st.error(f"❌ **Mathematically Impossible:** {calc_res['explanation']}")

            # Comparison bar
            fig_req = go.Figure()
            fig_req.add_trace(go.Bar(
                name="Already Obtained",
                x=[cur_subj_data["subject_name"]],
                y=[calc_res["current_obtained"]],
                marker_color="#3B82F6"
            ))
            fig_req.add_trace(go.Bar(
                name="Required to Hit Target",
                x=[cur_subj_data["subject_name"]],
                y=[min(calc_res["required_future_marks"], calc_res["remaining_max"])],
                marker_color="#10B981" if calc_res["achievable"] else "#EF4444"
            ))
            fig_req.update_layout(barmode='stack', title="Current Marks vs Required Future Marks", height=280)
            st.plotly_chart(fig_req, use_container_width=True)

        else:
            st.info("No marks data entered to compute required marks.")

    with t_ai_insights:
        st.markdown("### 🤖 Personalized AI Academic Recommendations & Study Plan")
        st.caption(f"Generated via: **{recs.get('generated_by', 'EduTrack Engine')}** using real database records.")

        st.markdown("#### 🚨 Priority Action Alerts")
        for alert in recs.get("immediate_alerts", []):
            st.warning(f"• {alert}")

        st.markdown("#### 📚 Subject-Specific Recommendations")
        for item in recs.get("subject_suggestions", []):
            st.info(f"**{item.get('subject')}:** {item.get('suggestion')}")

        st.markdown("#### 📅 Personalized Weekly Study Schedule")
        schedule_list = recs.get("weekly_study_schedule", [])
        if schedule_list:
            df_sched = pd.DataFrame(schedule_list)
            st.table(df_sched)

        st.markdown("#### 📝 Exam Preparation Strategies")
        for tip in recs.get("exam_prep_recommendations", []):
            st.write(f"• {tip}")

    with t_pdf:
        st.markdown("### 📄 Official Student Academic Report")
        st.write("Generate and download the comprehensive academic assessment report including attendance recovery calculations, required marks breakdown, and AI study schedules.")

        pdf_stream = generate_student_pdf_report(student, analysis, recs)
        filename = f"EduTrack_Report_{student['reg_no']}.pdf"

        st.download_button(
            label="📥 Download Official PDF Academic Report",
            data=pdf_stream,
            file_name=filename,
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )


# ==============================================================================
# VIEW 2: STUDENT REGISTRATION (Admin) (Phase 2)
# ==============================================================================
def render_student_registration():
    render_header("🎓 Student Registration & Profile Management", "Register new authorized students or update existing institutional student profiles.")

    tab_add, tab_list = st.tabs(["➕ Add New Student", "📋 Student Directory & Management"])

    with tab_add:
        st.markdown("#### Register Authorized Student")
        with st.form("add_student_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("Student Full Name *", placeholder="e.g. SK Kushmitha Bee")
                reg_no = st.text_input("Unique Registration Number *", placeholder="e.g. 251FA23109")
                email = st.text_input("Registered Institutional Email *", placeholder="e.g. kushmitha@edutrack.ac.in")
                dept = st.selectbox("Department *", ["Computer Science & Engineering", "Information Technology", "Electronics & Communication", "Mechanical Engineering", "Civil Engineering"])
                course = st.selectbox("Course *", ["B.Tech CSE (Data Science)", "B.Tech CSE (AI & ML)", "B.Tech CSE", "B.Tech IT", "M.Tech CSE"])

            with c2:
                ay = st.selectbox("Academic Year *", ["2025-2026", "2026-2027", "2024-2025"])
                cy = st.selectbox("Current Year *", ["1st Year", "2nd Year", "3rd Year", "4th Year"])
                sem = st.selectbox("Semester *", ["Semester 1", "Semester 2", "Semester 3", "Semester 4", "Semester 5", "Semester 6", "Semester 7", "Semester 8"])
                sec = st.selectbox("Section *", ["A", "B", "C", "D"])

            submit_student = st.form_submit_button("Register Student Permanently", type="primary", use_container_width=True)

            if submit_student:
                if not name or not reg_no or not email:
                    st.error("Please fill in all required fields (Name, Registration Number, Email).")
                elif not validate_email_format(email):
                    st.error("Invalid email address format.")
                else:
                    ok, msg = add_student(
                        reg_no=reg_no,
                        full_name=name,
                        email=email,
                        department=dept,
                        course=course,
                        academic_year=ay,
                        current_year=cy,
                        semester=sem,
                        section=sec
                    )
                    if ok:
                        st.success(msg)
                        st.session_state.selected_student_reg = reg_no.strip().upper()
                    else:
                        st.error(msg)

    with tab_list:
        students = get_all_students()
        if not students:
            st.markdown("""
            <div class="empty-state-box">
                <h3>No Registered Students</h3>
                <p>No student records exist in the database. Add a student using the form above or use the Bulk CSV Import feature.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"**Total Registered Students:** {len(students)}")
            df_st = pd.DataFrame(students)[["reg_no", "full_name", "email", "department", "semester", "section", "academic_year"]]
            st.dataframe(df_st, use_container_width=True, hide_index=True)

            # Edit or Delete Section
            st.markdown("#### Edit / Manage Student")
            edit_reg = st.selectbox("Select Student to Manage", [s["reg_no"] for s in students],
                                    format_func=lambda r: f"{r} — {get_student_by_reg_no(r)['full_name']}")
            target_st = get_student_by_reg_no(edit_reg)

            if target_st:
                with st.expander(f"Edit Profile: {target_st['full_name']} ({target_st['reg_no']})"):
                    with st.form("edit_st_form"):
                        e_name = st.text_input("Full Name", value=target_st["full_name"])
                        e_email = st.text_input("Email", value=target_st["email"])
                        e_dept = st.text_input("Department", value=target_st["department"])
                        e_course = st.text_input("Course", value=target_st["course"])
                        e_ay = st.text_input("Academic Year", value=target_st["academic_year"])
                        e_cy = st.text_input("Current Year", value=target_st["current_year"])
                        e_sem = st.text_input("Semester", value=target_st["semester"])
                        e_sec = st.text_input("Section", value=target_st["section"])

                        col_u, col_d = st.columns([1, 1])
                        with col_u:
                            save_ed = st.form_submit_button("Save Changes", type="primary")
                        with col_d:
                            del_st = st.form_submit_button("Delete Student", type="secondary")

                        if save_ed:
                            ok, msg = update_student(edit_reg, e_name, e_email, e_dept, e_course, e_ay, e_cy, e_sem, e_sec)
                            if ok:
                                st.success("Student updated.")
                                st.rerun()
                            else:
                                st.error(msg)
                        elif del_st:
                            ok, msg = delete_student(edit_reg)
                            if ok:
                                st.warning("Student deleted.")
                                st.rerun()
                            else:
                                st.error(msg)


# ==============================================================================
# VIEW 3: STUDENT SEARCH WORKFLOW (Phase 2 Search Workflow)
# ==============================================================================
def render_student_search_page():
    render_header("🔍 Student Academic Search & Profile Lookup", "Look up student academic profiles strictly by Registration Number or registered Email ID.")

    col1, col2 = st.columns([3, 1])
    with col1:
        search_input = st.text_input("Enter Student Registration Number or Email ID",
                                     value=st.session_state.search_query,
                                     placeholder="e.g. 251FA23109 or kushmitha@edutrack.ac.in")
    with col2:
        st.write("")
        st.write("")
        do_search = st.button("Search Database", type="primary", use_container_width=True)

    if do_search or search_input:
        st.session_state.search_query = search_input.strip()
        if not st.session_state.search_query:
            st.warning("Please enter a Registration Number or registered Email ID to search.")
            return

        student = search_student(st.session_state.search_query)
        if student:
            st.session_state.selected_student_reg = student["reg_no"]
            st.success(f"✅ Found Student Record: **{student['full_name']}** (`{student['reg_no']}`)")
            st.markdown("---")
            render_student_dashboard(student["reg_no"])
        else:
            st.error(f"❌ Student Record Not Found for '{st.session_state.search_query}'.")
            if st.session_state.user and st.session_state.user["role"] in ("Admin", "Faculty"):
                st.info("You are an authorized user. You can add this student record in the Student Registration page.")


# ==============================================================================
# VIEW 4: SUBJECT MANAGEMENT (Phase 3)
# ==============================================================================
def render_subject_management():
    render_header("📚 Subject & Curriculum Management", "Define courses, examination weightages, pass criteria, and planned sessions.")

    tab_add_sub, tab_sub_list = st.tabs(["➕ Add New Subject", "📋 Subject Catalog & Rules"])

    with tab_add_sub:
        with st.form("add_subject_form", clear_on_submit=True):
            sc1, sc2 = st.columns(2)
            with sc1:
                code = st.text_input("Subject Code *", placeholder="e.g. CS201")
                name = st.text_input("Subject Name *", placeholder="e.g. Data Structures")
                dept = st.selectbox("Department", ["Computer Science & Engineering", "Information Technology", "Electronics & Communication", "Mechanical Engineering"])
                sem = st.selectbox("Semester", ["Semester 1", "Semester 2", "Semester 3", "Semester 4", "Semester 5", "Semester 6", "Semester 7", "Semester 8"])
                planned_classes = st.number_input("Total Planned Classes (Semester)", min_value=10, max_value=120, value=60)

            with sc2:
                total_max = st.number_input("Total Maximum Marks", min_value=50.0, max_value=200.0, value=100.0, step=10.0)
                pass_mark = st.number_input("Subject Pass Marks", min_value=10.0, max_value=100.0, value=40.0, step=5.0)
                internal_max = st.number_input("Internal Assessment Max Marks", min_value=10.0, max_value=100.0, value=40.0, step=5.0)
                external_max = st.number_input("Semester Exam Max Marks", min_value=10.0, max_value=100.0, value=60.0, step=5.0)
                internal_w = st.number_input("Internal Weightage %", min_value=0.0, max_value=100.0, value=40.0, step=5.0)
                external_w = st.number_input("Semester Exam Weightage %", min_value=0.0, max_value=100.0, value=60.0, step=5.0)

            sub_submit = st.form_submit_button("Register Subject", type="primary", use_container_width=True)
            if sub_submit:
                if not code or not name:
                    st.error("Please provide both Subject Code and Name.")
                else:
                    ok, msg = add_subject(code, name, dept, sem, internal_max, external_max, total_max, pass_mark, internal_w, external_w, planned_classes)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

    with tab_sub_list:
        subjects = get_all_subjects()
        if not subjects:
            st.markdown("""
            <div class="empty-state-box">
                <h3>No Subjects Configured</h3>
                <p>Register subjects above so attendance and assessment marks can be recorded.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.dataframe(pd.DataFrame(subjects), use_container_width=True, hide_index=True)

            del_code = st.selectbox("Select Subject to Remove", [s["code"] for s in subjects], format_func=lambda c: f"{c} - {get_subject_by_code(c)['name']}")
            if st.button("Delete Subject", type="secondary"):
                ok, msg = delete_subject(del_code)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)


# ==============================================================================
# VIEW 5: ATTENDANCE TRACKER (Phase 4 & 5)
# ==============================================================================
def render_attendance_tracker():
    render_header("📅 Attendance Tracker & Session Recorder", "Enter, validate, and audit student subject-wise attendance records.")

    students = get_all_students()
    subjects = get_all_subjects()

    if not students or not subjects:
        st.warning("Please ensure both students and subjects exist in the database before entering attendance.")
        return

    tab_record, tab_audit = st.tabs(["✍️ Record / Update Attendance", "📜 Attendance Audit Trail"])

    with tab_record:
        with st.form("record_attendance_form"):
            c1, c2 = st.columns(2)
            with c1:
                sel_student = st.selectbox("Select Student *", [s["reg_no"] for s in students],
                                           format_func=lambda r: f"{r} — {get_student_by_reg_no(r)['full_name']}")
                sel_subject = st.selectbox("Select Subject *", [sub["code"] for sub in subjects],
                                           format_func=lambda c: f"{c} — {get_subject_by_code(c)['name']}")
                period = st.text_input("Attendance Period / Date Range", value="Aug - Nov 2026")

            with c2:
                total_cond = st.number_input("Total Classes Conducted *", min_value=0, max_value=120, value=40, step=1)
                attended = st.number_input("Classes Attended *", min_value=0, max_value=total_cond if total_cond > 0 else 0, value=min(26, total_cond), step=1)
                notes = st.text_input("Notes / Remarks", placeholder="e.g. Regular assessment audit")

            sub_att = st.form_submit_button("Save Attendance Permanently", type="primary", use_container_width=True)

            if sub_att:
                if attended > total_cond:
                    st.error("Attended classes cannot exceed total classes conducted.")
                else:
                    ok, msg = save_attendance(
                        student_reg_no=sel_student,
                        subject_code=sel_subject,
                        total_conducted=total_cond,
                        classes_attended=attended,
                        period_or_date=period,
                        notes=notes,
                        recorded_by=st.session_state.user["full_name"] if st.session_state.user else "Faculty",
                        change_reason="Form Entry"
                    )
                    if ok:
                        st.success(f"{msg} Recorded: {attended}/{total_cond} classes ({round(attended/total_cond*100, 1)}%) for {sel_student} in {sel_subject}.")
                        st.session_state.selected_student_reg = sel_student
                    else:
                        st.error(msg)

    with tab_audit:
        sel_hist_st = st.selectbox("Filter History by Student", [s["reg_no"] for s in students], key="hist_st_sel",
                                   format_func=lambda r: f"{r} — {get_student_by_reg_no(r)['full_name']}")
        history = get_attendance_history(sel_hist_st)
        if history:
            st.dataframe(pd.DataFrame(history)[["subject_name", "subject_code", "total_conducted", "classes_attended", "changed_by", "reason", "recorded_at"]],
                         use_container_width=True, hide_index=True)
        else:
            st.info("No attendance history logs recorded for this student.")


# ==============================================================================
# VIEW 6: MARKS MANAGEMENT (Phase 6)
# ==============================================================================
def render_marks_management():
    render_header("📝 Marks Management & Grading", "Enter and update formative, internal, and summative examination marks.")

    students = get_all_students()
    subjects = get_all_subjects()

    if not students or not subjects:
        st.warning("Please ensure students and subjects are registered before entering marks.")
        return

    with st.form("marks_entry_form"):
        col1, col2 = st.columns(2)
        with col1:
            sel_student = st.selectbox("Student *", [s["reg_no"] for s in students],
                                       format_func=lambda r: f"{r} — {get_student_by_reg_no(r)['full_name']}")
            sel_subject = st.selectbox("Subject *", [sub["code"] for sub in subjects],
                                       format_func=lambda c: f"{c} — {get_subject_by_code(c)['name']}")

        with col2:
            st.caption("Enter marks for available assessment components. Leave unused components blank.")

        st.markdown("##### Assessment Breakdown")
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            quiz = st.number_input("Quiz Marks (Max 10)", min_value=0.0, max_value=10.0, value=0.0, step=0.5)
            fa1 = st.number_input("FA1 Marks (Max 20)", min_value=0.0, max_value=20.0, value=0.0, step=0.5)
        with m2:
            assignment = st.number_input("Assignment (Max 10)", min_value=0.0, max_value=10.0, value=0.0, step=0.5)
            fa2 = st.number_input("FA2 Marks (Max 20)", min_value=0.0, max_value=20.0, value=0.0, step=0.5)
        with m3:
            midterm1 = st.number_input("Midterm 1 (Max 30)", min_value=0.0, max_value=30.0, value=0.0, step=0.5)
            midterm2 = st.number_input("Midterm 2 (Max 30)", min_value=0.0, max_value=30.0, value=0.0, step=0.5)
        with m4:
            internal_exam = st.number_input("Internal Total (Max 40)", min_value=0.0, max_value=40.0, value=0.0, step=0.5)
            semester_exam = st.number_input("Semester Exam (Max 60)", min_value=0.0, max_value=60.0, value=0.0, step=0.5)

        submit_marks = st.form_submit_button("Save Marks Permanently", type="primary", use_container_width=True)

        if submit_marks:
            # Clean zero values to None if not entered, or treat > 0 as entered
            q_val = quiz if quiz > 0 else None
            a_val = assignment if assignment > 0 else None
            fa1_val = fa1 if fa1 > 0 else None
            fa2_val = fa2 if fa2 > 0 else None
            m1_val = midterm1 if midterm1 > 0 else None
            m2_val = midterm2 if midterm2 > 0 else None
            ie_val = internal_exam if internal_exam > 0 else None
            se_val = semester_exam if semester_exam > 0 else None

            ok, msg = save_marks(
                student_reg_no=sel_student,
                subject_code=sel_subject,
                quiz=q_val,
                assignment=a_val,
                fa1=fa1_val,
                fa2=fa2_val,
                midterm1=m1_val,
                midterm2=m2_val,
                internal_exam=ie_val,
                semester_exam=se_val,
                recorded_by=st.session_state.user["full_name"] if st.session_state.user else "Faculty"
            )
            if ok:
                st.success(f"{msg} Marks updated for {sel_student} in {sel_subject}.")
                st.session_state.selected_student_reg = sel_student
            else:
                st.error(msg)


# ==============================================================================
# VIEW 7: BULK CSV / EXCEL IMPORT (Phase 12)
# ==============================================================================
def render_bulk_import():
    render_header("📥 Excel / CSV Bulk Data Import", "Upload and validate institutional student rosters, attendance sheets, and examination marks.")

    import_type = st.selectbox("Select Dataset to Import", ["students", "attendance", "marks"],
                               format_func=lambda x: f"Import {x.capitalize()} Data")

    # Download template helper
    template_csv = generate_sample_csv(import_type)
    st.download_button(
        label=f"⬇️ Download Blank {import_type.capitalize()} CSV Template",
        data=template_csv,
        file_name=f"{import_type}_template.csv",
        mime="text/csv"
    )

    st.markdown("---")
    uploaded_file = st.file_uploader("Upload CSV or Excel File", type=["csv", "xlsx", "xls"])

    if uploaded_file is not None:
        valid_ok, valid_msg, preview_df, issues = validate_and_preview_import(uploaded_file, import_type)

        if not valid_ok:
            st.error(f"Validation Error: {valid_msg}")
        else:
            st.success(f"File parsed successfully. Found {len(preview_df)} records.")

            st.markdown("#### 🔍 Validation Preview")
            col_p1, col_p2 = st.columns([2, 1])
            with col_p1:
                st.write("**Data Preview:**")
                st.dataframe(preview_df.head(20), use_container_width=True)
            with col_p2:
                st.write("**Pre-Import Audit Status:**")
                df_issues = pd.DataFrame(issues)
                st.dataframe(df_issues, use_container_width=True)

            has_fatal_errors = any(i.get("status") == "Invalid" for i in issues)

            if has_fatal_errors:
                st.error("⚠️ File contains invalid records (shown in red above). Please fix these in your spreadsheet before importing.")
            else:
                st.info("✅ All records passed integrity checks.")
                update_existing = st.checkbox("Update existing records if found", value=True)

                if st.button("Confirm and Commit to Database", type="primary"):
                    res = execute_import(
                        df=preview_df,
                        import_type=import_type,
                        update_existing=update_existing,
                        recorded_by=st.session_state.user["full_name"] if st.session_state.user else "Admin"
                    )
                    if res["success"]:
                        st.success(f"🎉 Successfully imported {res['success_count']} records!")
                    else:
                        st.warning(f"Import completed with warnings: {res['success_count']} imported, {len(res['errors'])} failed.")
                        for err in res["errors"]:
                            st.write(f"• {err}")


# ==============================================================================
# VIEW 8: INSTITUTIONAL SETTINGS (Phase 13 & Admin)
# ==============================================================================
def render_settings():
    render_header("⚙️ Institutional Academic Configuration", "Configure pass-mark policies, attendance thresholds, and examination weightages.")

    configs = get_all_configs()

    with st.form("settings_form"):
        st.markdown("#### Core Academic Rules")
        cur_att = float(configs.get("attendance_threshold", 75.0))
        cur_pass = float(configs.get("pass_percentage", 40.0))
        cur_int_w = float(configs.get("internal_weightage", 40.0))
        cur_ext_w = float(configs.get("external_weightage", 60.0))
        cur_min_ext = float(configs.get("min_external_pass", 35.0))

        c1, c2 = st.columns(2)
        with c1:
            new_att = st.number_input("Minimum Attendance Requirement (%) *", min_value=50.0, max_value=100.0, value=cur_att, step=1.0)
            new_pass = st.number_input("Overall Minimum Pass Percentage (%) *", min_value=30.0, max_value=60.0, value=cur_pass, step=1.0)
        with c2:
            new_int_w = st.number_input("Internal Assessment Weightage (%)", min_value=0.0, max_value=100.0, value=cur_int_w, step=5.0)
            new_ext_w = st.number_input("Semester Exam Weightage (%)", min_value=0.0, max_value=100.0, value=cur_ext_w, step=5.0)
            new_min_ext = st.number_input("Minimum Semester Exam Pass Threshold (%)", min_value=0.0, max_value=100.0, value=cur_min_ext, step=1.0)

        save_cfg = st.form_submit_button("Save Institutional Rules", type="primary")
        if save_cfg:
            set_config("attendance_threshold", str(new_att), "Minimum required attendance percentage")
            set_config("pass_percentage", str(new_pass), "Minimum overall pass percentage")
            set_config("internal_weightage", str(new_int_w), "Standard internal assessment weightage %")
            set_config("external_weightage", str(new_ext_w), "Standard semester end examination weightage %")
            set_config("min_external_pass", str(new_min_ext), "Minimum percentage required specifically in semester exam")
            st.success("Institutional academic policies updated. All calculations will now use these thresholds.")
            st.rerun()


# ==============================================================================
# VIEW 9: USER ACCOUNTS & ACCESS CONTROL (Admin) (Phase 1)
# ==============================================================================
def render_user_management():
    render_header("👥 User Accounts & Access Control", "Manage Administrator, Faculty, and Student login credentials.")

    tab_create, tab_users = st.tabs(["➕ Create User Account", "📋 Existing Users"])

    with tab_create:
        with st.form("create_user_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                u_name = st.text_input("Username *", placeholder="e.g. prof_john")
                u_email = st.text_input("Email *", placeholder="e.g. john@edutrack.ac.in")
                u_fullname = st.text_input("Full Name *", placeholder="e.g. Dr. John Doe")
            with col2:
                u_role = st.selectbox("Role *", ["Faculty", "Admin", "Student"])
                u_pwd = st.text_input("Temporary Password *", type="password")
                students = get_all_students()
                u_reg = st.selectbox("Link to Student Registration Number (Student role only)",
                                     ["None"] + [s["reg_no"] for s in students])

            submit_u = st.form_submit_button("Create User", type="primary")
            if submit_u:
                if not u_name or not u_email or not u_pwd or not u_fullname:
                    st.error("Please fill in all required fields.")
                else:
                    reg_link = u_reg if (u_role == "Student" and u_reg != "None") else None
                    ok, msg = create_user(u_name, u_email, u_pwd, u_role, u_fullname, reg_link)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

    with tab_users:
        users = get_all_users()
        if users:
            st.dataframe(pd.DataFrame(users), use_container_width=True, hide_index=True)
            del_id = st.selectbox("Delete User Account by ID", [u["id"] for u in users],
                                  format_func=lambda i: f"ID {i} - {[u['username'] for u in users if u['id'] == i][0]}")
            if st.button("Delete User", type="secondary"):
                ok, msg = delete_user(del_id)
                if ok:
                    st.warning("User deleted.")
                    st.rerun()
                else:
                    st.error(msg)


# ==============================================================================
# MAIN ROUTER & APP ENTRY POINT
# ==============================================================================
def main():
    if not st.session_state.user:
        render_login_page()
        return

    user = st.session_state.user
    role = user["role"]

    # Sidebar Navigation
    with st.sidebar:
        st.markdown(f"""
        <div style="padding: 12px; background: #F1F5F9; border-radius: 8px; margin-bottom: 16px;">
            <div style="font-size: 11px; text-transform: uppercase; color: #64748B; font-weight: 700;">Active User</div>
            <div style="font-size: 16px; font-weight: 700; color: #1E293B;">{user['full_name']}</div>
            <div style="font-size: 12px; color: #3B82F6; font-weight: 600;">Role: {role}</div>
            {f'<div style="font-size: 11px; color: #475569;">Reg No: {user["student_reg_no"]}</div>' if user.get("student_reg_no") else ''}
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state.user = None
            st.session_state.search_query = ""
            st.session_state.selected_student_reg = None
            st.rerun()

        st.markdown("---")

        # Dynamic role-based menu options
        if role == "Admin":
            menu_choice = st.radio("Navigation", [
                "📊 Executive Dashboard",
                "🔍 Search Student Profile",
                "🎓 Student Registration",
                "📚 Subject Management",
                "📅 Attendance Tracker",
                "📝 Marks Management",
                "📥 Bulk CSV / Excel Import",
                "⚙️ Academic Configuration",
                "👥 User Accounts"
            ])
        elif role == "Faculty":
            menu_choice = st.radio("Navigation", [
                "🔍 Search Student Profile",
                "📅 Attendance Tracker",
                "📝 Marks Management",
                "📥 Bulk CSV / Excel Import"
            ])
        else:  # Student
            menu_choice = st.radio("Navigation", [
                "🎓 My Academic Dashboard",
                "🎯 Required Marks Calculator",
                "📅 My Attendance Status",
                "📝 My Marks Breakdown",
                "🤖 AI Study Plan & Recommendations",
                "📄 Download My Academic Report"
            ])

    # Route Views
    if role == "Student":
        # Students are locked strictly to their own registration number
        st_reg = user.get("student_reg_no")
        if not st_reg:
            st.error("This student account is not linked to a valid Registration Number. Contact Administrator.")
            return

        render_student_dashboard(st_reg)

    else:
        # Admin and Faculty Routing
        if menu_choice == "📊 Executive Dashboard":
            # Overview of all students
            render_header("📊 Institutional Academic Performance Dashboard", "Comprehensive overview of department-wide academic health, attendance risks, and early warning indicators.")
            students = get_all_students()
            if not students:
                st.markdown("""
                <div class="empty-state-box">
                    <h3>No Student Records in Database</h3>
                    <p>The academic database is currently empty. Use the Student Registration or Bulk CSV Import feature to add actual institutional student records.</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"**Total Registered Students:** {len(students)}")
                sel_st = st.selectbox("Select Student to Inspect Academic Analysis", [s["reg_no"] for s in students],
                                      format_func=lambda r: f"{r} — {get_student_by_reg_no(r)['full_name']} ({get_student_by_reg_no(r)['department']})")
                render_student_dashboard(sel_st)

        elif menu_choice == "🔍 Search Student Profile":
            render_student_search_page()

        elif menu_choice == "🎓 Student Registration":
            render_student_registration()

        elif menu_choice == "📚 Subject Management":
            render_subject_management()

        elif menu_choice == "📅 Attendance Tracker":
            render_attendance_tracker()

        elif menu_choice == "📝 Marks Management":
            render_marks_management()

        elif menu_choice == "📥 Bulk CSV / Excel Import":
            render_bulk_import()

        elif menu_choice == "⚙️ Academic Configuration":
            render_settings()

        elif menu_choice == "👥 User Accounts":
            render_user_management()


if __name__ == "__main__":
    main()
