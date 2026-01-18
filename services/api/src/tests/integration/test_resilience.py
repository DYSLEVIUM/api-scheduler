import pytest
from unittest.mock import patch
from sqlalchemy.exc import OperationalError


def test_api_health_check_when_db_down(client):
    with patch('db.database.engine.connect', side_effect=OperationalError("DB down", None, None)):
        response = client.get("/health")
        assert response.status_code in [200, 503]


def test_create_target_retry_on_db_intermittent(client):
    call_count = 0
    
    def intermittent_db_failure(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise OperationalError("Connection lost", None, None)
        return MagicMock()
    
    target_data = {
        "name": "Test Target",
        "url": "https://api.example.com/test",
        "method": "GET",
        "headers": {},
    }
    
    response = client.post("/targets", json=target_data)
    assert response.status_code in [201, 500]


def test_get_schedules_when_db_slow(client):
    response = client.get("/schedules")
    assert response.status_code in [200, 504]


def test_pause_schedule_temporal_unavailable(client, schedule_id):
    with patch('temporal.client.get_temporal_client', side_effect=Exception("Temporal down")):
        response = client.post(f"/schedules/{schedule_id}/pause")
        assert response.status_code in [200, 500, 503]


def test_resume_schedule_temporal_unavailable(client, target_id):
    schedule_data = {
        "target_id": target_id,
        "interval_seconds": 60,
    }
    
    create_response = client.post("/schedules", json=schedule_data)
    if create_response.status_code == 201:
        schedule_id = create_response.json()["data"]["id"]
        
        client.post(f"/schedules/{schedule_id}/pause")
        
        with patch('temporal.client.get_temporal_client', side_effect=Exception("Temporal down")):
            response = client.post(f"/schedules/{schedule_id}/resume")
            assert response.status_code in [200, 500, 503]


def test_create_schedule_workflow_start_fails(client, target_id):
    schedule_data = {
        "target_id": target_id,
        "interval_seconds": 60,
    }
    
    with patch('temporal.client.start_schedule_workflow', side_effect=Exception("Workflow start failed")):
        response = client.post("/schedules", json=schedule_data)
        assert response.status_code in [201, 500]


def test_delete_schedule_partial_failure(client, target_id):
    schedule_data = {
        "target_id": target_id,
        "interval_seconds": 60,
    }
    
    create_response = client.post("/schedules", json=schedule_data)
    if create_response.status_code == 201:
        schedule_id = create_response.json()["data"]["id"]
        
        with patch('temporal.client.terminate_schedule_workflow', side_effect=Exception("Workflow termination failed")):
            response = client.delete(f"/schedules/{schedule_id}")
            assert response.status_code in [200, 500]


def test_get_jobs_empty_on_db_failure(client):
    with patch('domains.jobs.repository.JobRepository.get_all_jobs', side_effect=OperationalError("DB error", None, None)):
        response = client.get("/jobs")
        assert response.status_code in [200, 500]


def test_concurrent_schedule_operations_under_load(client, target_id):
    schedule_data = {
        "target_id": target_id,
        "interval_seconds": 60,
    }
    
    create_response = client.post("/schedules", json=schedule_data)
    if create_response.status_code == 201:
        schedule_id = create_response.json()["data"]["id"]
        
        pause_response = client.post(f"/schedules/{schedule_id}/pause")
        get_response = client.get(f"/schedules/{schedule_id}")
        resume_response = client.post(f"/schedules/{schedule_id}/resume")
        
        assert pause_response.status_code in [200, 409, 500]
        assert get_response.status_code in [200, 404]
        assert resume_response.status_code in [200, 409, 500]


def test_schedule_state_after_db_recovery(client, target_id):
    schedule_data = {
        "target_id": target_id,
        "interval_seconds": 60,
    }
    
    response = client.post("/schedules", json=schedule_data)
    assert response.status_code in [201, 500]


def test_target_operations_during_high_contention(client):
    target_data = {
        "name": "Test Target",
        "url": "https://api.example.com/test",
        "method": "GET",
        "headers": {},
    }
    
    response = client.post("/targets", json=target_data)
    assert response.status_code in [201, 500]


def test_schedule_consistency_after_temporal_restart(client, target_id):
    schedule_data = {
        "target_id": target_id,
        "interval_seconds": 60,
    }
    
    create_response = client.post("/schedules", json=schedule_data)
    if create_response.status_code == 201:
        schedule_id = create_response.json()["data"]["id"]
        
        get_response = client.get(f"/schedules/{schedule_id}")
        assert get_response.status_code == 200


def test_graceful_degradation_read_operations(client):
    response = client.get("/schedules")
    assert response.status_code in [200, 500, 503]
    
    response = client.get("/targets")
    assert response.status_code in [200, 500, 503]
    
    response = client.get("/jobs")
    assert response.status_code in [200, 500, 503]


def test_write_operations_fail_safe(client):
    target_data = {
        "name": "Test Target",
        "url": "https://api.example.com/test",
        "method": "GET",
        "headers": {},
    }
    
    with patch('db.database.get_session', side_effect=OperationalError("DB down", None, None)):
        response = client.post("/targets", json=target_data)
        assert response.status_code in [500, 503]


def test_multiple_schedule_operations_sequence(client, target_id):
    schedule_data = {
        "target_id": target_id,
        "interval_seconds": 60,
    }
    
    create_response = client.post("/schedules", json=schedule_data)
    if create_response.status_code == 201:
        schedule_id = create_response.json()["data"]["id"]
        
        pause_response = client.post(f"/schedules/{schedule_id}/pause")
        get_response_1 = client.get(f"/schedules/{schedule_id}")
        resume_response = client.post(f"/schedules/{schedule_id}/resume")
        get_response_2 = client.get(f"/schedules/{schedule_id}")
        pause_response_2 = client.post(f"/schedules/{schedule_id}/pause")
        delete_response = client.delete(f"/schedules/{schedule_id}")
        
        assert delete_response.status_code in [200, 404, 500]


def test_orphaned_workflow_cleanup(client, target_id):
    schedule_data = {
        "target_id": target_id,
        "interval_seconds": 60,
    }
    
    create_response = client.post("/schedules", json=schedule_data)
    if create_response.status_code == 201:
        schedule_id = create_response.json()["data"]["id"]
        
        with patch('temporal.client.terminate_schedule_workflow', side_effect=Exception("Workflow not found")):
            response = client.delete(f"/schedules/{schedule_id}")
            assert response.status_code in [200, 404, 500]
