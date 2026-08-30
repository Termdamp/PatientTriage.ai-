import pytest
from fastapi.testclient import TestClient

def test_health_check(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data

def test_get_queue_empty(client: TestClient):
    response = client.get("/queue")
    assert response.status_code == 200
    data = response.json()
    assert "patients" in data
    assert "totalCount" in data

def test_get_alerts_empty(client: TestClient):
    response = client.get("/alerts")
    assert response.status_code == 200
    data = response.json()
    assert "alerts" in data

def test_get_capacity(client: TestClient):
    response = client.get("/capacity")
    assert response.status_code == 200
    data = response.json()
    assert "totalBeds" in data
    assert "utilization" in data

def test_post_triage(client: TestClient):
    payload = {
        "age": 62,
        "gender": "male",
        "chiefComplaint": "Breathlessness",
        "symptoms": ["shortness_of_breath", "weakness"],
        "historyAvailable": True,
        "medicalHistory": ["hypertension"],
        "vitals": {
            "heartRate": 128,
            "systolicBp": 85,
            "diastolicBp": 52,
            "spo2": 89,
            "temperature": 38.2,
            "respiratoryRate": 30
        }
    }
    response = client.post("/triage", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "patientId" in data
    assert "priority" in data
    assert data["priority"] == "CRITICAL"
    assert "riskScore" in data
    assert "safetyFlags" in data
    assert len(data["safetyFlags"]) > 0

def test_get_patients(client: TestClient):
    response = client.get("/patients")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_patient_not_found(client: TestClient):
    response = client.get("/patients/NONEXISTENT")
    assert response.status_code == 404

def test_get_audit(client: TestClient):
    response = client.get("/audit")
    assert response.status_code == 200
    data = response.json()
    assert "events" in data

def test_triage_low_risk_patient(client: TestClient):
    payload = {
        "age": 30,
        "gender": "male",
        "chiefComplaint": "Minor laceration",
        "symptoms": ["laceration"],
        "historyAvailable": True,
        "medicalHistory": [],
        "vitals": {
            "heartRate": 72,
            "systolicBp": 120,
            "diastolicBp": 78,
            "spo2": 98,
            "temperature": 36.8,
            "respiratoryRate": 14
        }
    }
    response = client.post("/triage", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["priority"] == "LOW"
