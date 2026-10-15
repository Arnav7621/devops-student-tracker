import os
import pytest
from app import create_app, task_store


@pytest.fixture
def app_instance():
    """Create and configure a clean Flask application instance for each test."""
    # Ensure in-memory task store is isolated and empty before test
    task_store.clear()

    test_app = create_app({"TESTING": True})

    yield test_app

    # Clean up after test
    task_store.clear()


@pytest.fixture
def client(app_instance):
    """A test client for the app."""
    return app_instance.test_client()


# 1. Homepage returns HTTP 200
def test_homepage_returns_200(client):
    """Test that the dashboard homepage renders successfully with HTTP 200."""
    response = client.get("/")
    assert response.status_code == 200
    # Verify title in HTML
    assert b"DevOps Student Task Tracker" in response.data


# 2. Health endpoint returns HTTP 200 and healthy status
def test_health_endpoint_returns_healthy(client):
    """Test that GET /health returns HTTP 200 and valid JSON health payload."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data is not None
    assert data.get("status") == "healthy"
    assert "version" in data
    assert "timestamp" in data


# 3. Version endpoint returns the configured version
def test_version_endpoint_default(client):
    """Test that GET /version returns default version when APP_VERSION is not explicitly set."""
    response = client.get("/version")
    assert response.status_code == 200
    data = response.get_json()
    assert data is not None
    assert "version" in data


def test_version_endpoint_custom_env(client, monkeypatch):
    """Test that GET /version reflects custom APP_VERSION environment variable."""
    expected_version = "v2.5.42"
    monkeypatch.setenv("APP_VERSION", expected_version)

    response = client.get("/version")
    assert response.status_code == 200
    data = response.get_json()
    assert data.get("version") == expected_version

    # Also verify health endpoint reflects it
    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert health_res.get_json().get("version") == expected_version


# 4. Adding a task works
def test_add_task_success(client):
    """Test creating a new task returns HTTP 201 and updates store and stats."""
    payload = {
        "title": "Set up Minikube Cluster",
        "description": "Start Minikube and enable ingress addon",
        "category": "Kubernetes",
        "priority": "High"
    }
    response = client.post("/api/tasks", json=payload)
    assert response.status_code == 201

    data = response.get_json()
    assert "task" in data
    task = data["task"]
    assert task["title"] == "Set up Minikube Cluster"
    assert task["description"] == "Start Minikube and enable ingress addon"
    assert task["category"] == "Kubernetes"
    assert task["priority"] == "High"
    assert task["completed"] is False
    assert task["id"] == 1

    # Verify stats
    assert data["stats"]["total"] == 1
    assert data["stats"]["pending"] == 1
    assert data["stats"]["completed"] == 0

    # Verify task appears in get_tasks
    list_res = client.get("/api/tasks")
    assert list_res.status_code == 200
    list_data = list_res.get_json()
    assert len(list_data["tasks"]) == 1
    assert list_data["tasks"][0]["id"] == 1


def test_add_task_validation_error(client):
    """Test that adding a task with empty title returns HTTP 400."""
    response = client.post("/api/tasks", json={"title": "   "})
    assert response.status_code == 400
    assert "error" in response.get_json()


# 5. Completing a task works
def test_complete_task_success(client):
    """Test marking a task as completed updates its status and stats."""
    # First create a task
    create_res = client.post("/api/tasks", json={"title": "Configure Jenkins Pipeline"})
    assert create_res.status_code == 201
    task_id = create_res.get_json()["task"]["id"]

    # Mark as completed using PUT /api/tasks/<id>/complete
    complete_res = client.put(f"/api/tasks/{task_id}/complete", json={"completed": True})
    assert complete_res.status_code == 200

    data = complete_res.get_json()
    assert data["task"]["completed"] is True
    assert data["stats"]["completed"] == 1
    assert data["stats"]["pending"] == 0
    assert data["stats"]["total"] == 1

    # Verify toggle endpoint works as well
    toggle_res = client.post(f"/api/tasks/{task_id}/toggle")
    assert toggle_res.status_code == 200
    assert toggle_res.get_json()["task"]["completed"] is False


def test_complete_nonexistent_task(client):
    """Test completing a non-existent task returns HTTP 404."""
    response = client.put("/api/tasks/999/complete", json={"completed": True})
    assert response.status_code == 404
    assert "error" in response.get_json()


# 6. Deleting a task works
def test_delete_task_success(client):
    """Test deleting an existing task removes it from the store and updates stats."""
    # Create two tasks
    res1 = client.post("/api/tasks", json={"title": "Task 1"})
    res2 = client.post("/api/tasks", json={"title": "Task 2"})
    id1 = res1.get_json()["task"]["id"]
    id2 = res2.get_json()["task"]["id"]

    # Delete task 1
    del_res = client.delete(f"/api/tasks/{id1}")
    assert del_res.status_code == 200
    data = del_res.get_json()
    assert data["stats"]["total"] == 1

    # Verify list only contains task 2
    list_res = client.get("/api/tasks")
    remaining_tasks = list_res.get_json()["tasks"]
    assert len(remaining_tasks) == 1
    assert remaining_tasks[0]["id"] == id2


def test_delete_nonexistent_task(client):
    """Test deleting non-existent task returns HTTP 404."""
    response = client.delete("/api/tasks/999")
    assert response.status_code == 404
    assert "error" in response.get_json()


# 7. State isolation verification
def test_isolation_first_step(client):
    """Step 1 to test isolation: add tasks."""
    client.post("/api/tasks", json={"title": "Isolation Task A"})
    list_res = client.get("/api/tasks")
    assert len(list_res.get_json()["tasks"]) == 1


def test_isolation_second_step(client):
    """Step 2 to test isolation: verify store was reset and has 0 tasks."""
    list_res = client.get("/api/tasks")
    assert len(list_res.get_json()["tasks"]) == 0
