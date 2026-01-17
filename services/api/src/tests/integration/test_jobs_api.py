

def test_get_all_jobs(client):
    response = client.get("/jobs")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)


def test_get_jobs_by_schedule_id(client, schedule_id):
    response = client.get(f"/jobs?schedule_id={schedule_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)


def test_get_job_by_id_not_found(client):
    response = client.get("/jobs/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
