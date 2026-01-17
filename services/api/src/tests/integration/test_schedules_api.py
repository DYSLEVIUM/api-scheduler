

def test_create_interval_schedule(client, schedule_data):
    response = client.post("/schedules", json=schedule_data)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["interval_seconds"] == 60
    assert data["data"]["paused"] is False


def test_create_window_schedule(client, target_id):
    response = client.post(
        "/schedules",
        json={
            "target_id": target_id,
            "interval_seconds": 30,
            "duration_seconds": 300,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["interval_seconds"] == 30
    assert "duration_seconds" in data["data"]


def test_get_all_schedules(client, schedule_data):
    client.post("/schedules", json=schedule_data)

    response = client.get("/schedules")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)


def test_get_schedule_by_id(client, schedule_data):
    create_response = client.post("/schedules", json=schedule_data)
    schedule_id = create_response.json()["data"]["id"]

    response = client.get(f"/schedules/{schedule_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == schedule_id


def test_pause_schedule(client, schedule_data):
    create_response = client.post("/schedules", json=schedule_data)
    schedule_id = create_response.json()["data"]["id"]

    response = client.post(f"/schedules/{schedule_id}/pause")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["paused"] is True


def test_resume_schedule(client, schedule_data):
    create_response = client.post("/schedules", json=schedule_data)
    schedule_id = create_response.json()["data"]["id"]

    client.post(f"/schedules/{schedule_id}/pause")
    response = client.post(f"/schedules/{schedule_id}/resume")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["paused"] is False


def test_delete_schedule(client, schedule_data):
    create_response = client.post("/schedules", json=schedule_data)
    schedule_id = create_response.json()["data"]["id"]

    response = client.delete(f"/schedules/{schedule_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
