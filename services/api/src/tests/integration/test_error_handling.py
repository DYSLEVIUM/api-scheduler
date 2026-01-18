import pytest


def test_create_target_with_invalid_url(client):
    response = client.post(
        "/targets",
        json={
            "name": "Invalid Target",
            "url": "not-a-valid-url",
            "method": "GET",
        },
    )
    assert response.status_code in [400, 422]


def test_create_target_with_invalid_method(client):
    response = client.post(
        "/targets",
        json={
            "name": "Invalid Target",
            "url": "https://api.example.com/test",
            "method": "INVALID",
        },
    )
    assert response.status_code in [400, 422]


def test_create_schedule_with_invalid_target_id(client):
    response = client.post(
        "/schedules",
        json={
            "target_id": "00000000-0000-0000-0000-000000000000",
            "interval_seconds": 60,
        },
    )
    assert response.status_code in [404, 422, 500]


def test_create_schedule_with_negative_interval(client, target_id):
    response = client.post(
        "/schedules",
        json={
            "target_id": target_id,
            "interval_seconds": -60,
        },
    )
    assert response.status_code in [400, 422]


def test_create_schedule_with_zero_interval(client, target_id):
    response = client.post(
        "/schedules",
        json={
            "target_id": target_id,
            "interval_seconds": 0,
        },
    )
    assert response.status_code in [400, 422]


def test_update_target_with_invalid_id(client):
    response = client.put(
        "/targets/invalid-uuid",
        json={
            "name": "Updated Target",
            "url": "https://api.example.com/test",
            "method": "GET",
        },
    )
    assert response.status_code in [400, 404, 422]


def test_delete_nonexistent_target(client):
    response = client.delete("/targets/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_delete_nonexistent_schedule(client):
    response = client.delete("/schedules/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_pause_nonexistent_schedule(client):
    response = client.post("/schedules/00000000-0000-0000-0000-000000000000/pause")
    assert response.status_code == 404


def test_resume_nonexistent_schedule(client):
    response = client.post("/schedules/00000000-0000-0000-0000-000000000000/resume")
    assert response.status_code == 404


def test_create_target_with_missing_name(client):
    response = client.post(
        "/targets",
        json={
            "url": "https://api.example.com/test",
            "method": "GET",
        },
    )
    assert response.status_code in [400, 422]


def test_create_target_with_missing_url(client):
    response = client.post(
        "/targets",
        json={
            "name": "Test Target",
            "method": "GET",
        },
    )
    assert response.status_code in [400, 422]


def test_create_schedule_with_missing_target_id(client):
    response = client.post(
        "/schedules",
        json={
            "interval_seconds": 60,
        },
    )
    assert response.status_code in [400, 422]


def test_create_schedule_with_missing_interval(client, target_id):
    response = client.post(
        "/schedules",
        json={
            "target_id": target_id,
        },
    )
    assert response.status_code in [400, 422]


def test_create_window_schedule_with_invalid_duration(client, target_id):
    response = client.post(
        "/schedules",
        json={
            "target_id": target_id,
            "interval_seconds": 30,
            "duration_seconds": -100,
        },
    )
    assert response.status_code in [400, 422]


def test_create_window_schedule_duration_less_than_interval(client, target_id):
    response = client.post(
        "/schedules",
        json={
            "target_id": target_id,
            "interval_seconds": 100,
            "duration_seconds": 50,
        },
    )
    assert response.status_code in [400, 422]


def test_update_target_with_empty_body(client, target_data):
    create_response = client.post("/targets", json=target_data)
    target_id = create_response.json()["data"]["id"]
    
    response = client.put(f"/targets/{target_id}", json={})
    assert response.status_code in [400, 422]


def test_get_target_with_malformed_uuid(client):
    response = client.get("/targets/not-a-uuid")
    assert response.status_code in [400, 404, 422]


def test_get_schedule_with_malformed_uuid(client):
    response = client.get("/schedules/not-a-uuid")
    assert response.status_code in [400, 404, 422]


def test_get_job_with_malformed_uuid(client):
    response = client.get("/jobs/not-a-uuid")
    assert response.status_code in [400, 404, 422]
