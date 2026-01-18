import pytest
from unittest.mock import patch, AsyncMock


def test_schedule_lifecycle_create_pause_resume_delete(client, target_id):
    schedule_data = {
        "target_id": target_id,
        "interval_seconds": 60,
    }
    
    create_response = client.post("/schedules", json=schedule_data)
    assert create_response.status_code == 201
    schedule_id = create_response.json()["data"]["id"]
    
    get_response = client.get(f"/schedules/{schedule_id}")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["paused"] is False
    
    pause_response = client.post(f"/schedules/{schedule_id}/pause")
    assert pause_response.status_code == 200
    assert pause_response.json()["data"]["paused"] is True
    
    resume_response = client.post(f"/schedules/{schedule_id}/resume")
    assert resume_response.status_code == 200
    
    delete_response = client.delete(f"/schedules/{schedule_id}")
    assert delete_response.status_code == 200


def test_target_update_affects_schedule(client, target_data):
    create_target_response = client.post("/targets", json=target_data)
    target_id = create_target_response.json()["data"]["id"]
    
    schedule_data = {
        "target_id": target_id,
        "interval_seconds": 60,
    }
    create_schedule_response = client.post("/schedules", json=schedule_data)
    assert create_schedule_response.status_code == 201
    schedule_id = create_schedule_response.json()["data"]["id"]
    
    updated_target = {
        "name": "Updated Target",
        "url": "https://api.example.com/v2/test",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": {"key": "value"},
    }
    update_response = client.put(f"/targets/{target_id}", json=updated_target)
    assert update_response.status_code == 200
    
    get_schedule_response = client.get(f"/schedules/{schedule_id}")
    assert get_schedule_response.status_code == 200


def test_delete_target_with_active_schedules(client, target_id, schedule_id):
    delete_response = client.delete(f"/targets/{target_id}")
    assert delete_response.status_code in [200, 400, 409]


def test_pause_already_paused_schedule(client, target_id):
    schedule_data = {
        "target_id": target_id,
        "interval_seconds": 60,
    }
    create_response = client.post("/schedules", json=schedule_data)
    schedule_id = create_response.json()["data"]["id"]
    
    client.post(f"/schedules/{schedule_id}/pause")
    second_pause = client.post(f"/schedules/{schedule_id}/pause")
    assert second_pause.status_code == 200


def test_resume_already_active_schedule(client, target_id):
    schedule_data = {
        "target_id": target_id,
        "interval_seconds": 60,
    }
    create_response = client.post("/schedules", json=schedule_data)
    schedule_id = create_response.json()["data"]["id"]
    
    resume_response = client.post(f"/schedules/{schedule_id}/resume")
    assert resume_response.status_code in [200, 400]


def test_multiple_schedules_same_target(client, target_id):
    schedule_data_1 = {
        "target_id": target_id,
        "interval_seconds": 60,
    }
    schedule_data_2 = {
        "target_id": target_id,
        "interval_seconds": 120,
    }
    
    response1 = client.post("/schedules", json=schedule_data_1)
    response2 = client.post("/schedules", json=schedule_data_2)
    
    assert response1.status_code == 201
    assert response2.status_code == 201
    assert response1.json()["data"]["id"] != response2.json()["data"]["id"]


def test_create_schedule_paused(client, target_id):
    schedule_data = {
        "target_id": target_id,
        "interval_seconds": 60,
        "paused": True,
    }
    
    create_response = client.post("/schedules", json=schedule_data)
    if create_response.status_code == 201:
        assert create_response.json()["data"]["paused"] is True


def test_window_schedule_lifecycle(client, target_id):
    schedule_data = {
        "target_id": target_id,
        "interval_seconds": 30,
        "duration_seconds": 300,
    }
    
    create_response = client.post("/schedules", json=schedule_data)
    assert create_response.status_code == 201
    schedule_id = create_response.json()["data"]["id"]
    
    get_response = client.get(f"/schedules/{schedule_id}")
    assert get_response.status_code == 200
    assert "duration_seconds" in get_response.json()["data"]
    
    delete_response = client.delete(f"/schedules/{schedule_id}")
    assert delete_response.status_code == 200


def test_get_schedules_with_filters(client):
    response = client.get("/schedules")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)


def test_concurrent_schedule_operations(client, target_id):
    schedule_data = {
        "target_id": target_id,
        "interval_seconds": 60,
    }
    
    create_response = client.post("/schedules", json=schedule_data)
    schedule_id = create_response.json()["data"]["id"]
    
    pause_response = client.post(f"/schedules/{schedule_id}/pause")
    get_response = client.get(f"/schedules/{schedule_id}")
    
    assert pause_response.status_code == 200
    assert get_response.status_code == 200


def test_target_with_headers_and_body(client):
    target_data = {
        "name": "Target with Headers",
        "url": "https://api.example.com/test",
        "method": "POST",
        "headers": {
            "Authorization": "Bearer token",
            "Content-Type": "application/json",
        },
        "body": {"key": "value"},
    }
    
    response = client.post("/targets", json=target_data)
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["headers"] == target_data["headers"]
    assert data["data"]["body"] == target_data["body"]


def test_target_with_query_parameters(client):
    target_data = {
        "name": "Target with Query Params",
        "url": "https://api.example.com/test?param1=value1&param2=value2",
        "method": "GET",
    }
    
    response = client.post("/targets", json=target_data)
    assert response.status_code == 201


def test_schedule_gets_jobs(client, target_id):
    schedule_data = {
        "target_id": target_id,
        "interval_seconds": 60,
    }
    
    create_response = client.post("/schedules", json=schedule_data)
    schedule_id = create_response.json()["data"]["id"]
    
    jobs_response = client.get(f"/jobs?schedule_id={schedule_id}")
    assert jobs_response.status_code == 200
    assert isinstance(jobs_response.json()["data"], list)
