def test_create_target(client, target_data):
    payload = {**target_data, "headers": {"Authorization": "Bearer token"}}
    response = client.post("/targets", json=payload)
    assert response.status_code == 201
    result = response.json()
    assert result["success"] is True
    assert result["data"]["name"] == "Test Target"


def test_get_all_targets(client):
    response = client.get("/targets")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)


def test_get_target_by_id(client, target_data):
    create_response = client.post("/targets", json=target_data)
    target_id = create_response.json()["data"]["id"]

    response = client.get(f"/targets/{target_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == target_id


def test_get_target_by_id_not_found(client):
    response = client.get("/targets/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_update_target(client, target_data):
    create_response = client.post("/targets", json=target_data)
    target_id = create_response.json()["data"]["id"]

    response = client.put(
        f"/targets/{target_id}",
        json={
            "name": "Updated Target",
            "url": "https://api.example.com/v2/test",
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "body": {"key": "value"},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "Updated Target"


def test_delete_target(client, target_data):
    create_response = client.post("/targets", json=target_data)
    target_id = create_response.json()["data"]["id"]

    response = client.delete(f"/targets/{target_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
