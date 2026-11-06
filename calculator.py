import math


def calculate_attendance_metrics(attended: int, total: int, target_percent: float = 75.0, planned_total: int = 60):
    """
    Calculate comprehensive attendance metrics with exact mathematical guarantees.
    
    Parameters:
    - attended: Classes attended (A >= 0)
    - total: Classes conducted so far (T >= 0)
    - target_percent: Required attendance percentage (R, e.g. 75.0)
    - planned_total: Total planned classes for the entire semester
    
    Returns:
    Dict with metrics, consecutive classes required, projected paths, and explanations.
    """
    if total < 0 or attended < 0:
        raise ValueError("Class counts cannot be negative.")
    if attended > total:
        raise ValueError("Attended classes cannot exceed total classes conducted.")

    if total == 0:
        return {
            "total_conducted": 0,
            "attended": 0,
            "missed": 0,
            "current_percentage": 0.0,
            "target_percentage": float(target_percent),
            "status": "No Classes Conducted",
            "shortage": float(target_percent),
            "consecutive_required": 0,
            "achievable": True,
            "explanation": "No classes have been conducted yet.",
            "buffer_classes": 0,
            "remaining_classes": max(0, planned_total),
            "max_possible_attendance": 100.0 if planned_total > 0 else 0.0
        }

    current_pct = round((attended / total) * 100.0, 2)
    missed = total - attended
    target_r = target_percent / 100.0
    remaining_classes = max(0, planned_total - total)

    # 1. Consecutive classes required: (A + X) / (T + X) >= R
    consecutive_required = 0
    if current_pct < target_percent:
        # Solve: A + X >= R * T + R * X => X(1 - R) >= R * T - A => X >= (R * T - A) / (1 - R)
        if target_r >= 1.0:
            consecutive_required = 999999  # Cannot reach 100% if missed even one class
        else:
            num = (target_r * total) - attended
            den = 1.0 - target_r
            if den > 0:
                raw_x = num / den
                consecutive_required = max(0, math.ceil(raw_x))
                # Validate and adjust for numerical precision
                while (attended + consecutive_required) / (total + consecutive_required) < (target_r - 1e-9):
                    consecutive_required += 1

    # 2. Maximum possible attendance with remaining classes
    total_at_end = total + remaining_classes
    attended_at_end = attended + remaining_classes
    max_possible_pct = round((attended_at_end / total_at_end) * 100.0, 2) if total_at_end > 0 else current_pct
    achievable = max_possible_pct >= target_percent

    # 3. Buffer classes (how many classes can be safely missed if currently above target)
    # A / (T + Y) >= R => Y <= (A - R*T) / R
    buffer_classes = 0
    if current_pct >= target_percent and target_r > 0:
        buffer_val = (attended - (target_r * total)) / target_r
        buffer_classes = max(0, int(math.floor(buffer_val)))

    # 4. Human-readable explanation matching exact prompt requirements
    shortage = max(0.0, round(target_percent - current_pct, 2))
    if current_pct >= target_percent:
        status = "On Track"
        if buffer_classes > 0:
            explanation = f"Your current attendance is {current_pct}%, which satisfies the required {target_percent}%. You have a safety margin of {buffer_classes} class{'es' if buffer_classes > 1 else ''}."
        else:
            explanation = f"Your current attendance is {current_pct}%, meeting the required {target_percent}% threshold. Continue attending all classes to maintain this status."
    else:
        status = "Shortage Alert"
        if not achievable and remaining_classes > 0:
            explanation = (f"Your current attendance is {current_pct}% (shortage of {shortage}%). "
                           f"Even if you attend all {remaining_classes} remaining classes, your maximum possible attendance will be "
                           f"{max_possible_pct}%, which is below the required {target_percent}%. Immediate institutional intervention is required.")
        else:
            explanation = (f"Your current attendance is {current_pct}%. You need to attend the next "
                           f"{consecutive_required} consecutive classes without missing any to reach {target_percent}%.")

    return {
        "total_conducted": total,
        "attended": attended,
        "missed": missed,
        "current_percentage": current_pct,
        "target_percentage": float(target_percent),
        "shortage": shortage,
        "status": status,
        "consecutive_required": consecutive_required,
        "achievable": achievable,
        "buffer_classes": buffer_classes,
        "remaining_classes": remaining_classes,
        "max_possible_attendance": max_possible_pct,
        "explanation": explanation
    }


def calculate_projected_attendance(attended: int, total: int, upcoming_classes_attend: int, upcoming_classes_total: int):
    """Calculate attendance projection given future class attendance."""
    new_total = total + upcoming_classes_total
    new_attended = attended + upcoming_classes_attend
    if new_total == 0:
        return 0.0
    return round((new_attended / new_total) * 100.0, 2)


def calculate_required_marks(current_obtained: float, current_max: float, total_max: float,
                             pass_mark: float, target_percentage: float):
    """
    Calculate required marks for future assessments based on actual assessment structure.
    
    Formula:
    Required Future Marks = Required Overall Marks - Existing Weighted Marks
    
    Parameters:
    - current_obtained: Total marks earned so far
    - current_max: Maximum possible marks for assessments evaluated so far
    - total_max: Total maximum marks for the subject (e.g. 100)
    - pass_mark: Pass threshold (e.g. 40)
    - target_percentage: Target overall percentage (e.g. 40, 60, 70, 80, custom)
    
    Returns:
    Dict with exact marks needed, achievability status, remaining max, and explanation.
    """
    if total_max <= 0:
        raise ValueError("Total maximum marks must be greater than zero.")
    if current_max < 0 or current_obtained < 0:
        raise ValueError("Marks cannot be negative.")
    if current_obtained > current_max and current_max > 0:
        raise ValueError("Obtained marks cannot exceed maximum evaluated marks.")

    remaining_max = max(0.0, round(total_max - current_max, 2))
    current_pct = round((current_obtained / current_max * 100.0), 2) if current_max > 0 else 0.0

    # Overall target marks needed for the entire subject
    target_marks_needed = round((target_percentage / 100.0) * total_max, 2)

    # Required on remaining assessments
    required_future_marks = max(0.0, round(target_marks_needed - current_obtained, 2))

    # Required for passing specifically
    pass_marks_needed = pass_mark
    required_to_pass = max(0.0, round(pass_marks_needed - current_obtained, 2))

    # Achievability check
    max_possible_total = round(current_obtained + remaining_max, 2)
    max_possible_pct = round((max_possible_total / total_max) * 100.0, 2)

    achievable = target_marks_needed <= max_possible_total
    pass_achievable = pass_marks_needed <= max_possible_total

    # Percentage needed on the remaining component
    if remaining_max > 0:
        required_pct_on_remaining = round((required_future_marks / remaining_max) * 100.0, 2)
    else:
        required_pct_on_remaining = 0.0

    # Explanation
    if remaining_max <= 0:
        if current_obtained >= target_marks_needed:
            explanation = f"Assessment complete. Target achieved with {current_obtained}/{total_max} ({current_pct}%)."
        else:
            explanation = f"Assessment complete. Scored {current_obtained}/{total_max} ({current_pct}%). Target of {target_percentage}% was not met."
    elif not achievable:
        explanation = (f"Target of {target_percentage}% ({target_marks_needed} marks) is mathematically impossible. "
                       f"Even with 100% on all remaining assessments ({remaining_max} marks), "
                       f"the maximum possible score is {max_possible_total}/{total_max} ({max_possible_pct}%).")
    elif required_future_marks == 0:
        explanation = f"You have already secured enough marks ({current_obtained}) to satisfy the {target_percentage}% target ({target_marks_needed} marks)."
    else:
        explanation = (f"To achieve {target_percentage}% ({target_marks_needed} marks overall), you need at least "
                       f"{required_future_marks} marks out of {remaining_max} ({required_pct_on_remaining}%) in remaining assessments.")

    return {
        "current_obtained": round(current_obtained, 2),
        "current_max": round(current_max, 2),
        "current_percentage": current_pct,
        "total_max": round(total_max, 2),
        "remaining_max": remaining_max,
        "target_percentage": float(target_percentage),
        "target_marks_needed": target_marks_needed,
        "required_future_marks": required_future_marks,
        "required_pct_on_remaining": required_pct_on_remaining,
        "pass_mark": pass_mark,
        "required_to_pass": required_to_pass,
        "pass_achievable": pass_achievable,
        "max_possible_total": max_possible_total,
        "max_possible_percentage": max_possible_pct,
        "achievable": achievable,
        "explanation": explanation
    }
