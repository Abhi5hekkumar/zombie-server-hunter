from __future__ import annotations
import pandas as pd

def classify(row: pd.Series, cpu_threshold: float, p95_threshold: float, memory_threshold: float,
             network_threshold: float, disk_threshold: float, window_hours: int, min_observation_hours: int) -> tuple[str, str, int]:
    role = str(row.get("role", "unknown")).lower()
    protected_words = ("database", "db-", "replica", "security", "monitor", "backup", "standby", "control", "router", "firewall", "kafka", "queue")
    if any(word in role or word in str(row["instance"]).lower() for word in protected_words):
        return "Protected role — review", "Role/name suggests critical or standby infrastructure; never infer safe shutdown from utilization alone.", 0
    if row["cpu_avg_pct"] <= cpu_threshold and row["cpu_p95_pct"] <= p95_threshold and row["memory_avg_pct"] <= memory_threshold and row["network_avg_kbps"] <= network_threshold and row["disk_avg_kbps"] <= disk_threshold:
        # The selected observation window is used as a proxy for persistence; the UI labels this explicitly.
        confidence = 3 if window_hours >= min_observation_hours else 2
        return ("High-priority candidate" if confidence == 3 else "Candidate — more history needed",
                "Sustained low CPU, memory utilization, network and disk activity in the selected window. Validate owner, dependencies, schedules and redundancy.", confidence)
    return "Likely active / insufficient evidence", "At least one signal is above the configured low-activity threshold.", 1


def savings(row: pd.Series, watts: float, pue: float, hours_month: float, price: float, carbon: float) -> dict[str, float]:
    # Scenario estimate only: assumes full shutdown and that the stated average IT load is avoided.
    kwh = watts * pue * hours_month / 1000
    return {"monthly_kwh": kwh, "monthly_cost": kwh * price, "monthly_co2_kg": kwh * carbon}

