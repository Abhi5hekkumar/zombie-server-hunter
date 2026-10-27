import pandas as pd
from core import classify, savings


def test_low_activity_is_candidate():
    row = pd.Series({
        "instance": "staging-01:9100", "role": "unknown", "cpu_avg_pct": 1.0,
        "cpu_p95_pct": 3.0, "memory_avg_pct": 20.0, "network_avg_kbps": 1.0,
        "disk_avg_kbps": 1.0, "uptime_days": 20,
    })
    status, _, confidence = classify(row, 5, 15, 70, 10, 10, 168, 24)
    assert status == "High-priority candidate"
    assert confidence == 3


def test_protected_role_is_never_candidate():
    row = pd.Series({
        "instance": "db-replica-01:9100", "role": "database-replica", "cpu_avg_pct": 0.1,
        "cpu_p95_pct": 1.0, "memory_avg_pct": 10.0, "network_avg_kbps": 0.1,
        "disk_avg_kbps": 0.1, "uptime_days": 100,
    })
    status, _, _ = classify(row, 5, 15, 70, 10, 10, 168, 24)
    assert status == "Protected role — review"


def test_savings_formula():
    result = savings(pd.Series(), watts=100, pue=1.5, hours_month=730, price=8, carbon=0.7)
    assert round(result["monthly_kwh"], 2) == 109.5
    assert round(result["monthly_cost"], 2) == 876.0
    assert round(result["monthly_co2_kg"], 2) == 76.65
