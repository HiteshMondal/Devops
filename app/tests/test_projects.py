def test_list_projects_empty(client):
    resp = client.get("/api/v1/projects")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_and_list_project(client):
    create_resp = client.post(
        "/api/v1/projects",
        json={"title": "Portfolio Site", "description": "A FastAPI app", "link": "https://example.com"},
    )
    assert create_resp.status_code == 200
    assert "id" in create_resp.json()

    list_resp = client.get("/api/v1/projects")
    assert list_resp.status_code == 200
    projects = list_resp.json()
    assert len(projects) == 1
    assert projects[0]["title"] == "Portfolio Site"
    assert projects[0]["link"] == "https://example.com"


def test_create_project_requires_title(client):
    resp = client.post("/api/v1/projects", json={"description": "missing title"})
    assert resp.status_code == 422