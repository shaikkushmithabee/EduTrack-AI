import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


def generate_student_pdf_report(student: dict, analysis: dict, recommendations: dict) -> io.BytesIO:
    """
    Generate an official, beautifully styled PDF Academic Report for a student
    using actual records and calculated intelligence.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1E3A8A'),
        alignment=1  # Center
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#4B5563'),
        alignment=1
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1E3A8A'),
        spaceBefore=10,
        spaceAfter=6
    )

    cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#1F2937')
    )

    cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#1F2937')
    )

    story = []

    # 1. Header Banner
    story.append(Paragraph("EduTrack AI — Academic Early Warning & Performance System", title_style))
    story.append(Paragraph("OFFICIAL STUDENT ACADEMIC ANALYSIS & INTERVENTION REPORT", subtitle_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1E3A8A'), spaceBefore=2, spaceAfter=8))

    # 2. Student Profile Table
    profile_data = [
        [
            Paragraph("<b>Student Full Name:</b>", cell_style),
            Paragraph(student.get("full_name", "N/A"), cell_bold),
            Paragraph("<b>Registration Number:</b>", cell_style),
            Paragraph(student.get("reg_no", "N/A"), cell_bold)
        ],
        [
            Paragraph("<b>Department:</b>", cell_style),
            Paragraph(student.get("department", "N/A"), cell_style),
            Paragraph("<b>Course:</b>", cell_style),
            Paragraph(student.get("course", "N/A"), cell_style)
        ],
        [
            Paragraph("<b>Academic Year:</b>", cell_style),
            Paragraph(student.get("academic_year", "N/A"), cell_style),
            Paragraph("<b>Year & Semester:</b>", cell_style),
            Paragraph(f"{student.get('current_year', 'N/A')} - {student.get('semester', 'N/A')} (Sec: {student.get('section', 'N/A')})", cell_style)
        ],
        [
            Paragraph("<b>Registered Email:</b>", cell_style),
            Paragraph(student.get("email", "N/A"), cell_style),
            Paragraph("<b>Report Date:</b>", cell_style),
            Paragraph(datetime.now().strftime("%d %b %Y, %I:%M %p"), cell_style)
        ]
    ]

    profile_table = Table(profile_data, colWidths=[105, 165, 110, 160])
    profile_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(profile_table)
    story.append(Spacer(1, 10))

    # 3. Academic Summary & Risk Level KPI
    risk_level = analysis.get("risk_level", "Unknown")
    risk_color = colors.HexColor('#059669') if risk_level == "Low Risk" else (
        colors.HexColor('#D97706') if risk_level == "Medium Risk" else colors.HexColor('#DC2626')
    )

    kpi_data = [
        [
            Paragraph(f"<b>Overall Attendance</b><br/><font size=14 color='#1E3A8A'>{analysis.get('overall_attendance_pct', 0.0)}%</font>", cell_style),
            Paragraph(f"<b>Overall Marks Avg</b><br/><font size=14 color='#1E3A8A'>{analysis.get('overall_marks_pct', 0.0)}%</font>", cell_style),
            Paragraph(f"<b>Tracked Subjects</b><br/><font size=14 color='#1E3A8A'>{analysis.get('total_subjects_tracked', 0)}</font>", cell_style),
            Paragraph(f"<b>Academic Risk Status</b><br/><font size=12 color='{risk_color.hexval()}'><b>{risk_level}</b></font>", cell_style),
        ]
    ]
    kpi_table = Table(kpi_data, colWidths=[135, 135, 135, 135])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#EFF6FF')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#BFDBFE')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BFDBFE')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 10))

    # 4. Attendance Analysis & Consecutive Classes Table
    story.append(Paragraph("1. Subject-Wise Attendance & Recovery Analysis (Threshold: 75%)", section_heading))
    att_table_data = [
        [
            Paragraph("<b>Subject</b>", cell_bold),
            Paragraph("<b>Conducted</b>", cell_bold),
            Paragraph("<b>Attended</b>", cell_bold),
            Paragraph("<b>Current %</b>", cell_bold),
            Paragraph("<b>Shortage</b>", cell_bold),
            Paragraph("<b>Consecutive Classes to 75%</b>", cell_bold),
            Paragraph("<b>Status</b>", cell_bold),
        ]
    ]

    for subj_code, m in analysis.get("subject_attendance", {}).items():
        st_color = '#059669' if m['status'] == 'On Track' else '#DC2626'
        req_str = f"<b>{m['consecutive_required']} classes</b>" if m['consecutive_required'] > 0 else "Requirement Met"
        att_table_data.append([
            Paragraph(f"{m['subject_name']} ({subj_code})", cell_style),
            Paragraph(str(m['total_conducted']), cell_style),
            Paragraph(str(m['attended']), cell_style),
            Paragraph(f"{m['current_percentage']}%", cell_bold),
            Paragraph(f"{m['shortage']}%", cell_style),
            Paragraph(req_str, cell_style),
            Paragraph(f"<font color='{st_color}'><b>{m['status']}</b></font>", cell_style),
        ])

    if len(att_table_data) == 1:
        att_table_data.append([Paragraph("No attendance records registered yet.", cell_style), "", "", "", "", "", ""])

    att_table = Table(att_table_data, colWidths=[140, 60, 55, 60, 60, 105, 60])
    att_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E2E8F0')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(att_table)
    story.append(Spacer(1, 10))

    # 5. Marks & Required Future Marks Table
    story.append(Paragraph("2. Subject Marks & Required Future Examination Targets", section_heading))
    marks_table_data = [
        [
            Paragraph("<b>Subject</b>", cell_bold),
            Paragraph("<b>Scored / Max</b>", cell_bold),
            Paragraph("<b>Current %</b>", cell_bold),
            Paragraph("<b>Req to Pass</b>", cell_bold),
            Paragraph("<b>Req for 60%</b>", cell_bold),
            Paragraph("<b>Req for 70%</b>", cell_bold),
            Paragraph("<b>Req for 80%</b>", cell_bold),
        ]
    ]

    for subj_code, sm in analysis.get("subject_marks", {}).items():
        targets = sm.get("targets", {})
        pass_f = targets.get("pass", {})
        t_60 = targets.get("60", {})
        t_70 = targets.get("70", {})
        t_80 = targets.get("80", {})

        p_str = f"{pass_f.get('required_future_marks', 0)} ({pass_f.get('required_pct_on_remaining', 0)}%)" if pass_f.get('achievable') else "Impossible"
        r60_str = f"{t_60.get('required_future_marks', 0)} ({t_60.get('required_pct_on_remaining', 0)}%)" if t_60.get('achievable') else "Impossible"
        r70_str = f"{t_70.get('required_future_marks', 0)} ({t_70.get('required_pct_on_remaining', 0)}%)" if t_70.get('achievable') else "Impossible"
        r80_str = f"{t_80.get('required_future_marks', 0)} ({t_80.get('required_pct_on_remaining', 0)}%)" if t_80.get('achievable') else "Impossible"

        marks_table_data.append([
            Paragraph(f"{sm['subject_name']}", cell_style),
            Paragraph(f"{sm['current_obtained']}/{sm['current_max']}", cell_style),
            Paragraph(f"{sm['current_percentage']}%", cell_bold),
            Paragraph(p_str, cell_style),
            Paragraph(r60_str, cell_style),
            Paragraph(r70_str, cell_style),
            Paragraph(r80_str, cell_style),
        ])

    if len(marks_table_data) == 1:
        marks_table_data.append([Paragraph("No marks evaluated yet.", cell_style), "", "", "", "", "", ""])

    marks_table = Table(marks_table_data, colWidths=[140, 75, 60, 65, 65, 65, 70])
    marks_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E2E8F0')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(marks_table)
    story.append(Spacer(1, 10))

    # 6. Risk Evaluation & AI Insights
    story.append(Paragraph("3. Academic Risk Diagnostic & Explanation", section_heading))
    for reason in analysis.get("risk_reasons", []):
        story.append(Paragraph(f"• {reason}", cell_style))
    story.append(Spacer(1, 6))

    # 7. Actionable Recommendations
    story.append(Paragraph("4. Personalized Academic Interventions", section_heading))
    for alert in recommendations.get("immediate_alerts", []):
        story.append(Paragraph(f"• <b>Priority Action:</b> {alert}", cell_style))
    for sug in recommendations.get("subject_suggestions", []):
        story.append(Paragraph(f"• <b>{sug.get('subject')}:</b> {sug.get('suggestion')}", cell_style))
    story.append(Spacer(1, 6))

    # 8. Weekly Study Schedule Table
    story.append(Paragraph("5. Recommended Weekly Study Schedule", section_heading))
    sched_data = [
        [Paragraph("<b>Day</b>", cell_bold), Paragraph("<b>Target Subject</b>", cell_bold),
         Paragraph("<b>Allocated Study</b>", cell_bold), Paragraph("<b>Focus Objective</b>", cell_bold)]
    ]
    for row in recommendations.get("weekly_study_schedule", []):
        sched_data.append([
            Paragraph(row.get("day", ""), cell_style),
            Paragraph(row.get("subject", ""), cell_bold),
            Paragraph(f"{row.get('hours', 0)} Hours", cell_style),
            Paragraph(row.get("focus_task", ""), cell_style),
        ])

    if len(sched_data) > 1:
        sched_table = Table(sched_data, colWidths=[80, 130, 80, 250])
        sched_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(sched_table)

    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#94A3B8'), spaceBefore=4, spaceAfter=4))
    story.append(Paragraph("EduTrack AI System Verification: This report reflects persistent institutional academic records. Generated automatically.", subtitle_style))

    doc.build(story)
    buffer.seek(0)
    return buffer
