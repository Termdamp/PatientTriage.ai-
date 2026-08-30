"""
Deterioration Engine - Detects significant worsening of patient vitals over time using vital trajectories.

Analyzes a timeline of vital snapshots to identify trends, slopes, and sudden drops.
DISCLAIMER: Prototype thresholds. NOT clinically validated.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.utils.enums import DeteriorationSeverity

@dataclass
class DeteriorationResult:
    deteriorating: bool
    severity: DeteriorationSeverity
    changes: List[str]
    change_details: List[Dict[str, Any]]
    score: float  # Internal deterioration severity score

def detect_deterioration(
    vitals_history: Any,
    current: Optional[Dict[str, Any]] = None
) -> DeteriorationResult:
    """
    Compare historical vitals to detect trajectories of deterioration.
    Can be called in two ways:
    1. detect_deterioration(vitals_history: List[Dict]) - trajectory mode
    2. detect_deterioration(previous: Dict, current: Dict) - backward compatibility mode
    """
    changes = []
    change_details = []
    deterioration_score = 0.0

    # Handle backward compatibility signature
    if current is not None:
        history_list = [vitals_history, current]
    else:
        history_list = vitals_history if isinstance(vitals_history, list) else []

    if len(history_list) < 2:
        return DeteriorationResult(
            deteriorating=False,
            severity=DeteriorationSeverity.STABLE,
            changes=[],
            change_details=[],
            score=0.0
        )

    # Latest and previous snapshots
    current = history_list[-1]
    previous = history_list[-2]

    # --- 1. Sudden Drop / Rise (Consecutive Snapshots) ---
    # SpO2 consecutive change
    curr_spo2 = current.get("spo2")
    prev_spo2 = previous.get("spo2")
    if curr_spo2 is not None and prev_spo2 is not None:
        delta = prev_spo2 - curr_spo2
        if delta >= 6:
            deterioration_score += 25
            changes.append(f"SpO2 critically dropped from {prev_spo2}% to {curr_spo2}% (Δ-{delta:.1f}%)")
            change_details.append({"vital": "spo2", "type": "consecutive_drop", "from": prev_spo2, "to": curr_spo2, "delta": -delta, "severity": "CRITICAL"})
        elif delta >= 3:
            deterioration_score += 12
            changes.append(f"SpO2 dropped from {prev_spo2}% to {curr_spo2}% (Δ-{delta:.1f}%)")
            change_details.append({"vital": "spo2", "type": "consecutive_drop", "from": prev_spo2, "to": curr_spo2, "delta": -delta, "severity": "HIGH"})

    # Systolic BP consecutive change
    curr_sbp = current.get("systolic_bp")
    prev_sbp = previous.get("systolic_bp")
    if curr_sbp is not None and prev_sbp is not None:
        delta = prev_sbp - curr_sbp
        if delta >= 20:
            deterioration_score += 20
            changes.append(f"Systolic BP critically dropped from {prev_sbp} to {curr_sbp}mmHg (Δ-{delta:.0f}mmHg)")
            change_details.append({"vital": "systolic_bp", "type": "consecutive_drop", "from": prev_sbp, "to": curr_sbp, "delta": -delta, "severity": "CRITICAL"})
        elif delta >= 10:
            deterioration_score += 10
            changes.append(f"Systolic BP dropped from {prev_sbp} to {curr_sbp}mmHg (Δ-{delta:.0f}mmHg)")
            change_details.append({"vital": "systolic_bp", "type": "consecutive_drop", "from": prev_sbp, "to": curr_sbp, "delta": -delta, "severity": "HIGH"})

    # Heart Rate consecutive change
    curr_hr = current.get("heart_rate")
    prev_hr = previous.get("heart_rate")
    if curr_hr is not None and prev_hr is not None:
        delta = abs(curr_hr - prev_hr)
        if delta >= 25:
            deterioration_score += 15
            dir_str = "increased" if curr_hr > prev_hr else "decreased"
            changes.append(f"Heart rate {dir_str} significantly from {prev_hr} to {curr_hr}bpm (Δ{delta:.0f})")
            change_details.append({"vital": "heart_rate", "type": "consecutive_change", "from": prev_hr, "to": curr_hr, "delta": curr_hr-prev_hr, "severity": "HIGH"})
        elif delta >= 15:
            deterioration_score += 8
            dir_str = "increased" if curr_hr > prev_hr else "decreased"
            changes.append(f"Heart rate {dir_str} from {prev_hr} to {curr_hr}bpm")
            change_details.append({"vital": "heart_rate", "type": "consecutive_change", "from": prev_hr, "to": curr_hr, "delta": curr_hr-prev_hr, "severity": "MODERATE"})

    # Respiratory Rate consecutive change
    curr_rr = current.get("respiratory_rate")
    prev_rr = previous.get("respiratory_rate")
    if curr_rr is not None and prev_rr is not None:
        delta = curr_rr - prev_rr
        if delta >= 8:
            deterioration_score += 12
            changes.append(f"Respiratory rate increased from {prev_rr} to {curr_rr}/min")
            change_details.append({"vital": "respiratory_rate", "type": "consecutive_rise", "from": prev_rr, "to": curr_rr, "delta": delta, "severity": "HIGH"})
        elif delta >= 4:
            deterioration_score += 6
            changes.append(f"Respiratory rate increased from {prev_rr} to {curr_rr}/min")
            change_details.append({"vital": "respiratory_rate", "type": "consecutive_rise", "from": prev_rr, "to": curr_rr, "delta": delta, "severity": "MODERATE"})

    # Temperature consecutive change
    curr_temp = current.get("temperature")
    prev_temp = previous.get("temperature")
    if curr_temp is not None and prev_temp is not None:
        delta = abs(curr_temp - prev_temp)
        if delta >= 1.5:
            deterioration_score += 5
            changes.append(f"Temperature changed from {prev_temp}°C to {curr_temp}°C")
            change_details.append({"vital": "temperature", "type": "consecutive_change", "from": prev_temp, "to": curr_temp, "delta": curr_temp-prev_temp, "severity": "MODERATE"})


    # --- 2. Trajectory-Based Trend Analysis (Multiple Vitals over Time) ---
    if len(history_list) >= 3:
        spo2s = [v.get("spo2") for v in history_list if v.get("spo2") is not None]
        hrs = [v.get("heart_rate") for v in history_list if v.get("heart_rate") is not None]
        sbps = [v.get("systolic_bp") for v in history_list if v.get("systolic_bp") is not None]
        timestamps = [v.get("timestamp") for v in history_list]

        # Calculate time span in hours
        time_span_hours = 1.0
        if timestamps[0] and timestamps[-1]:
            try:
                t_earliest = timestamps[0] if isinstance(timestamps[0], datetime) else datetime.fromisoformat(str(timestamps[0]).replace('Z', '+00:00'))
                t_latest = timestamps[-1] if isinstance(timestamps[-1], datetime) else datetime.fromisoformat(str(timestamps[-1]).replace('Z', '+00:00'))
                span_sec = (t_latest - t_earliest).total_seconds()
                if span_sec > 60:
                    time_span_hours = span_sec / 3600.0
            except Exception:
                pass

        # SpO2 downward trajectory (e.g. 98 -> 96 -> 94)
        if len(spo2s) >= 3:
            # Check if strictly decreasing
            is_decreasing = all(spo2s[i] > spo2s[i+1] for i in range(len(spo2s)-1))
            total_drop = spo2s[0] - spo2s[-1]
            if is_decreasing and total_drop >= 4:
                deterioration_score += 15
                changes.append(f"SpO2 showing persistent downward trajectory: decreased {total_drop}% over {len(spo2s)} readings")
                change_details.append({"vital": "spo2", "type": "trajectory_down", "values": spo2s, "delta": -total_drop, "severity": "HIGH"})
            elif total_drop / time_span_hours >= 3.0 and total_drop >= 3:
                # Rate of drop is fast
                deterioration_score += 10
                changes.append(f"SpO2 dropping rapidly at a rate of {total_drop / time_span_hours:.1f}% per hour")
                change_details.append({"vital": "spo2", "type": "rate_drop", "rate": -total_drop/time_span_hours, "severity": "HIGH"})

        # Heart Rate upward trajectory
        if len(hrs) >= 3:
            is_increasing = all(hrs[i] < hrs[i+1] for i in range(len(hrs)-1))
            total_rise = hrs[-1] - hrs[0]
            if is_increasing and total_rise >= 20:
                deterioration_score += 12
                changes.append(f"Heart rate showing persistent upward trajectory: increased +{total_rise}bpm over {len(hrs)} readings")
                change_details.append({"vital": "heart_rate", "type": "trajectory_up", "values": hrs, "delta": total_rise, "severity": "HIGH"})
            elif total_rise / time_span_hours >= 15.0 and total_rise >= 15:
                deterioration_score += 8
                changes.append(f"Heart rate rising rapidly at a rate of {total_rise / time_span_hours:.1f} bpm per hour")
                change_details.append({"vital": "heart_rate", "type": "rate_rise", "rate": total_rise/time_span_hours, "severity": "MODERATE"})

        # Systolic BP downward trajectory
        if len(sbps) >= 3:
            is_decreasing = all(sbps[i] > sbps[i+1] for i in range(len(sbps)-1))
            total_drop = sbps[0] - sbps[-1]
            if is_decreasing and total_drop >= 15:
                deterioration_score += 12
                changes.append(f"Systolic BP showing persistent downward trajectory: dropped -{total_drop}mmHg")
                change_details.append({"vital": "systolic_bp", "type": "trajectory_down", "values": sbps, "delta": -total_drop, "severity": "HIGH"})

    # Determine deterioration severity
    deteriorating = deterioration_score > 0
    if deterioration_score >= 35:
        severity = DeteriorationSeverity.CRITICAL
    elif deterioration_score >= 20:
        severity = DeteriorationSeverity.HIGH
    elif deterioration_score > 0:
        severity = DeteriorationSeverity.MODERATE
    else:
        severity = DeteriorationSeverity.STABLE

    return DeteriorationResult(
        deteriorating=deteriorating,
        severity=severity,
        changes=changes,
        change_details=change_details,
        score=deterioration_score
    )
