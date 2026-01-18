from datetime import UTC, datetime


def test_get_all_runs(client):
    response = client.get("/runs")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)


def test_get_runs_by_schedule_id(client, schedule_id):
    response = client.get(f"/runs?schedule_id={schedule_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)


def test_get_runs_with_status_filter(client, schedule_id):
    response = client.get(f"/runs?schedule_id={schedule_id}&status=success")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)


def test_get_runs_with_time_filter(client, schedule_id):
    start_time = datetime.now(UTC).isoformat()
    end_time = datetime.now(UTC).isoformat()
    
    response = client.get(
        f"/runs?schedule_id={schedule_id}&start_time={start_time}&end_time={end_time}"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)


def test_get_run_by_id_not_found(client):
    response = client.get("/runs/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_get_runs_with_invalid_status_filter(client):
    response = client.get("/runs?status=invalid_status")
    assert response.status_code in [400, 422]


def test_get_runs_with_invalid_time_format(client):
    response = client.get("/runs?start_time=invalid_time")
    assert response.status_code in [400, 422]


def test_get_runs_pagination(client):
    response = client.get("/runs?limit=10&offset=0")
    assert response.status_code in [200, 404, 422]
    if response.status_code == 200:
        data = response.json()
        assert data["success"] is True
